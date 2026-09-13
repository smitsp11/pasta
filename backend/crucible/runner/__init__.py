"""run_matrix: the controlled population, scheduled in waves under the Steel concurrency cap.

Two phases per journey, not one flat wave: a `returning` variant needs the baseline's
persistent profile, and Steel only finalises that profile after the baseline session is
released. Returning specs await a per-baseline future; everything else starts immediately,
bounded by a semaphore.
"""
from __future__ import annotations

import asyncio
import logging

from typing import Any, AsyncIterator, Awaitable, Callable

from ..engines.base import Engine, RunContext
from ..engines.guard import hits_payment_guard
from ..schemas import TERMINAL, Config, RunEvent, RunResult, SessionStarted, SiteModel, TerminalOutcome
from ..steel import SteelUnavailable, open_session, wait_profile_ready
from .matrix import MVP_CONFIGS, SHOULD_CONFIGS, STRETCH_CONFIGS, RunSpec, build_matrix  # noqa: F401
from .outcomes import harness_result, last_step_index, should_retry

log = logging.getLogger("crucible.runner")

DEFAULT_MAX_CONCURRENCY = 8          # leave 2 of the free-tier 10 for retries
DEFAULT_RUN_BUDGET_S = 10 * 60       # under the 12-minute session timeout
DEFAULT_PROFILE_WAIT_S = 90.0
_SENTINEL = object()

SessionFactory = Callable[..., Any]                 # open_session-like asynccontextmanager
ProfileWaiter = Callable[[str], Awaitable[bool]]     # wait_profile_ready-like


async def run_matrix(
    site: SiteModel,
    configs: list[Config],
    engines: dict[str, Engine],
    *,
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
    run_budget_s: float = DEFAULT_RUN_BUDGET_S,
    max_retries: int = 1,
    profile_wait_s: float = DEFAULT_PROFILE_WAIT_S,
    session_factory: SessionFactory = open_session,
    profile_waiter: ProfileWaiter | None = None,
    step_caps: dict[str, int] | None = None,
) -> AsyncIterator[RunEvent | SessionStarted | RunResult]:
    """Yield SessionStarted / RunEvent / RunResult for every journey × config, as they happen.

    Cancelling the generator cancels every in-flight run; each run releases its own session.
    """
    specs = build_matrix(site, configs, step_caps=step_caps)
    missing = {s.cfg.engine for s in specs} - set(engines)
    if missing:
        raise ValueError(f"no engine registered for {sorted(missing)}")
    profile_waiter = profile_waiter or (lambda pid: wait_profile_ready(pid, timeout_s=profile_wait_s))

    queue: asyncio.Queue[Any] = asyncio.Queue()
    sem = asyncio.Semaphore(max_concurrency)
    loop = asyncio.get_running_loop()
    profile_futures: dict[str, asyncio.Future[str | None]] = {
        s.run_id: loop.create_future() for s in specs if s.persist_profile
    }

    async def attempt(spec: RunSpec, attempt_no: int) -> tuple[RunResult, str | None]:
        """One attempt. Returns (result, profile_id_if_persisted)."""
        engine = engines[spec.cfg.engine]
        step_cap = spec.step_cap or engine.default_step_cap
        profile_id: str | None = None
        if spec.needs_profile_from:
            fut = profile_futures.get(spec.needs_profile_from)
            if fut is None:
                return harness_result(spec, attempt_no, "profile_source_missing"), None
            try:
                profile_id = await asyncio.wait_for(asyncio.shield(fut), timeout=profile_wait_s + run_budget_s)
            except asyncio.TimeoutError:
                profile_id = None
            if not profile_id:
                return harness_result(spec, attempt_no, "profile_not_ready"), None

        events: list[RunEvent] = []
        outcome: TerminalOutcome | None = None
        stall_hint: str | None = None
        harness_reason: str | None = None
        session_info: dict[str, Any] = {}
        persisted_profile: str | None = None

        async with sem:
            try:
                async with session_factory(spec.cfg, profile_id=profile_id,
                                           persist_profile=spec.persist_profile) as session:
                    session_info = {"session_id": session.session_id, "replay_url": session.replay_url,
                                    "hls_url": session.hls_url}
                    persisted_profile = session.profile_id if spec.persist_profile else None
                    ctx = RunContext(run_id=f"{spec.run_id}#{attempt_no}" if attempt_no > 1 else spec.run_id,
                                     session_id=session.session_id, journey_id=spec.journey.id, config=spec.cfg)
                    await queue.put(SessionStarted(run_id=ctx.run_id, session_id=session.session_id,
                                                   journey_id=spec.journey.id, config=spec.cfg,
                                                   viewer_url=session.viewer_url, replay_url=session.replay_url,
                                                   hls_url=session.hls_url))
                    agen = engine.run_journey(session, spec.journey, spec.cfg, step_cap, ctx)
                    steps = 0
                    try:
                        async with asyncio.timeout(run_budget_s):
                            async for ev in agen:
                                events.append(ev)
                                await queue.put(ev)
                                if ev.outcome in TERMINAL:
                                    outcome = ev.outcome  # type: ignore[assignment]
                                    break
                                if hits_payment_guard(ev):
                                    outcome, stall_hint = "completed", "payment_guard"
                                    break
                                if ev.outcome == "step_ok":
                                    steps += 1
                                    if steps >= step_cap:
                                        outcome, stall_hint = "stalled", "step_cap"
                                        break
                    except TimeoutError:
                        outcome, stall_hint = "stalled", "run_budget"
                    finally:
                        await agen.aclose()
                    if outcome is None:                    # engine returned without a terminal event
                        outcome, stall_hint = "stalled", "no_terminal_event"
                    # Replay offset of the last event, against the session clock.
                    if events:
                        session_info["replay_offset_s"] = session.replay_offset_s(events[-1].timestamp)
            except SteelUnavailable as e:
                outcome, harness_reason = "harness_error", f"steel_unavailable: {e}"
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001 - engine/infra failure, never a site problem
                log.exception("harness error in %s attempt %s", spec.run_id, attempt_no)
                outcome, harness_reason = "harness_error", f"{type(e).__name__}: {e}"

        result = RunResult(
            run_id=spec.run_id, journey_id=spec.journey.id, config=spec.cfg,
            session_id=session_info.get("session_id"), outcome=outcome, attempt=attempt_no, events=events,
            replay_url=session_info.get("replay_url"), hls_url=session_info.get("hls_url"),
            final_screenshot_ref=next((e.screenshot_ref for e in reversed(events) if e.screenshot_ref), None),
            failure_step_index=last_step_index(events) if outcome != "completed" else None,
            replay_offset_s=session_info.get("replay_offset_s"),
            harness_reason=harness_reason, stall_hint=stall_hint,
        )
        return result, persisted_profile

    async def execute(spec: RunSpec) -> RunResult:
        attempt_no = 1
        profile_id: str | None = None
        try:
            while True:
                result, profile_id = await attempt(spec, attempt_no)
                if not should_retry(result.outcome, attempt_no, max_retries):
                    break
                log.info("retrying %s after %s (attempt %s)", spec.run_id, result.outcome, attempt_no)
                attempt_no += 1
            await queue.put(result)
            return result
        finally:
            fut = profile_futures.get(spec.run_id)
            if fut is not None and not fut.done():
                ready = False
                if profile_id:
                    try:
                        ready = await profile_waiter(profile_id)
                    except Exception as e:  # noqa: BLE001
                        log.warning("profile wait for %s failed: %s", profile_id, e)
                fut.set_result(profile_id if ready else None)

    tasks = [asyncio.create_task(execute(s), name=s.run_id) for s in specs]
    gate = asyncio.gather(*tasks, return_exceptions=True)
    gate.add_done_callback(lambda _: queue.put_nowait(_SENTINEL))
    try:
        while True:
            item = await queue.get()
            if item is _SENTINEL:
                break
            yield item
        for t, r in zip(tasks, gate.result()):
            if isinstance(r, BaseException) and not isinstance(r, asyncio.CancelledError):
                log.error("run task %s died: %r", t.get_name(), r)
    finally:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


