"""Browser Use (DOM agent) on a Steel session. Verified against browser-use 0.13.10:
   Browser(cdp_url=...) passed as `browser=`; Agent.run(max_steps, on_step_start, on_step_end);
   history.urls()/model_actions()/is_done()/is_successful()/final_result()/errors().
"""
from __future__ import annotations

import asyncio
import base64
import logging
import os
from typing import Any, AsyncIterator

from ..schemas import Config, Journey, RunEvent
from ..steel import SteelSession
from .base import PAYMENT_GUARD_PROMPT, RunContext, anthropic_headers

log = logging.getLogger("crucible.engines.browser_use")

DEFAULT_MODEL = os.environ.get("CRUCIBLE_BROWSER_USE_MODEL", "claude-opus-5")


def summarise_action(action: Any) -> str:
    """Browser Use model_actions() items are dicts like {"click_element_by_index": {"index": 3}, "interacted_element": ...}."""
    if not isinstance(action, dict):
        return str(action)[:200]
    for k, v in action.items():
        if k == "interacted_element":
            continue
        if isinstance(v, dict):
            args = ", ".join(f"{a}={str(b)[:40]!r}" for a, b in v.items() if a not in ("interacted_element",))
            return f"{k}({args})"
        return f"{k}={str(v)[:60]}"
    return "(no action)"


class BrowserUseEngine:
    name = "browser_use"
    default_step_cap = 25

    def __init__(self, model: str = DEFAULT_MODEL, *, step_timeout_s: int = 45, llm_timeout_s: int = 60,
                 max_actions_per_step: int = 3, max_failures: int = 2, use_vision: Any = "auto"):
        self.model = model
        self.step_timeout_s = step_timeout_s
        self.llm_timeout_s = llm_timeout_s
        self.max_actions_per_step = max_actions_per_step
        self.max_failures = max_failures
        self.use_vision = use_vision

    def _llm(self):
        from browser_use import ChatAnthropic
        return ChatAnthropic(model=self.model, default_headers=anthropic_headers() or None)

    async def run_journey(self, session: SteelSession, journey: Journey, cfg: Config, step_cap: int,
                          ctx: RunContext) -> AsyncIterator[RunEvent]:
        from browser_use import Agent, Browser

        q: asyncio.Queue[RunEvent | None] = asyncio.Queue()
        step = 0

        async def snapshot(agent) -> tuple[str, str | None]:
            """(url, screenshot_ref) from the agent's own browser state, falling back to our page."""
            url, ref = "", None
            try:
                state = await agent.browser_session.get_browser_state_summary()
                url = getattr(state, "url", "") or ""
                shot = getattr(state, "screenshot", None)
                if shot:
                    ref = session.save_screenshot_bytes(step, base64.b64decode(shot))
            except Exception as e:  # noqa: BLE001
                log.debug("state summary failed: %s", e)
            if not url:
                try:
                    url = (agent.history.urls() or [""])[-1] or session.url
                except Exception:  # noqa: BLE001
                    url = session.url
            if ref is None:
                ref = await session.screenshot_ref(step)
            return url, ref

        async def on_step_end(agent) -> None:
            nonlocal step
            step += 1
            try:
                actions = agent.history.model_actions()
                last = summarise_action(actions[-1]) if actions else "(thinking)"
            except Exception:  # noqa: BLE001
                last = "(unknown action)"
            thought = ""
            try:
                thoughts = agent.history.model_thoughts()
                if thoughts:
                    t = thoughts[-1]
                    thought = getattr(t, "next_goal", None) or getattr(t, "evaluation_previous_goal", None) or ""
            except Exception:  # noqa: BLE001
                pass
            url, ref = await snapshot(agent)
            obs = url if not thought else f"{url}\n{thought}"
            await q.put(ctx.event(step, last, obs, screenshot_ref=ref))

        task = f"Go to {journey.entry_url} and complete this task: {journey.goal}"
        agent = Agent(
            task=task,
            llm=self._llm(),
            browser=Browser(cdp_url=session.cdp_url),
            extend_system_message=PAYMENT_GUARD_PROMPT,
            max_actions_per_step=self.max_actions_per_step,
            max_failures=self.max_failures,
            use_vision=self.use_vision,
            step_timeout=self.step_timeout_s,
            llm_timeout=self.llm_timeout_s,
            calculate_cost=False,
            enable_signal_handler=False,
        )

        async def run_agent():
            try:
                return await agent.run(max_steps=step_cap, on_step_end=on_step_end)
            finally:
                q.put_nowait(None)

        runner = asyncio.create_task(run_agent())
        try:
            while (ev := await q.get()) is not None:
                yield ev
            history = await runner                       # re-raises engine exceptions -> harness_error
        except (asyncio.CancelledError, GeneratorExit):
            runner.cancel()
            await asyncio.gather(runner, return_exceptions=True)
            raise

        done = successful = False
        final = ""
        try:
            done = bool(history.is_done())
            successful = bool(history.is_successful())
            final = str(history.final_result() or "")
        except Exception as e:  # noqa: BLE001
            log.debug("history inspection failed: %s", e)
        outcome = "completed" if (done and successful) else "stalled"
        errors = []
        try:
            errors = [e for e in history.errors() if e]
        except Exception:  # noqa: BLE001
            pass
        obs = final or (f"errors: {errors[-1]}" if errors else session.url)
        yield ctx.event(step + 1, "done", obs, screenshot_ref=await session.screenshot_ref(step + 1),
                        outcome=outcome)  # type: ignore[arg-type]
