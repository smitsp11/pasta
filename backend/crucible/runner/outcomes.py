"""Terminal outcome policy: what counts as what, and what gets retried."""
from __future__ import annotations

from ..schemas import RunEvent, RunResult, TerminalOutcome
from .matrix import RunSpec

RETRYABLE: frozenset[str] = frozenset({"stalled", "harness_error"})


def should_retry(outcome: TerminalOutcome, attempt: int, max_retries: int) -> bool:
    return outcome in RETRYABLE and attempt <= max_retries


def harness_result(spec: RunSpec, attempt: int, reason: str, *, session_id: str | None = None,
                   events: list[RunEvent] | None = None, replay_url: str | None = None,
                   hls_url: str | None = None) -> RunResult:
    events = events or []
    return RunResult(
        run_id=spec.run_id, journey_id=spec.journey.id, config=spec.cfg, session_id=session_id,
        outcome="harness_error", attempt=attempt, events=events, harness_reason=reason,
        replay_url=replay_url, hls_url=hls_url,
        final_screenshot_ref=next((e.screenshot_ref for e in reversed(events) if e.screenshot_ref), None),
    )


def last_step_index(events: list[RunEvent]) -> int | None:
    for e in reversed(events):
        if e.outcome == "step_ok":
            return e.step_index
    return None
