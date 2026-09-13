"""Engine contract (locked at M0). An engine turns (session, journey) into a RunEvent stream.

Rules:
  * one RunEvent per agent step with outcome="step_ok"; one terminal event (completed|stalled)
  * never raise for a site problem; raise only for engine/infra failure (-> harness_error)
  * the Runner enforces step caps, time budgets, and the payment guard; engines just report
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Protocol, runtime_checkable

from ..schemas import Config, Journey, Outcome, RunEvent, utcnow
from ..steel import SteelSession

PAYMENT_GUARD_PROMPT = (
    "SAFETY RULES: You are testing whether this website works for automated agents. "
    "Stop and report the task as complete as soon as you reach the checkout or payment page. "
    "Never enter card numbers, never enter passwords, never click Pay, Place order, Buy now, "
    "Confirm purchase, Subscribe, or Delete. Never create an account. If the site blocks you "
    "(cookie wall you cannot dismiss, CAPTCHA, login wall, geo block), stop and report that "
    "you are stuck and why, instead of retrying the same action more than twice."
)


@dataclass(frozen=True)
class RunContext:
    """Identifiers the Runner assigns; engines stamp them on every event."""
    run_id: str
    session_id: str
    journey_id: str
    config: Config

    def event(self, step_index: int, action: str, observation: str = "",
              screenshot_ref: str | None = None, outcome: Outcome = "step_ok") -> RunEvent:
        return RunEvent(run_id=self.run_id, session_id=self.session_id, journey_id=self.journey_id,
                        config=self.config, step_index=step_index, timestamp=utcnow(),
                        action=action[:500], observation=observation[:2000],
                        screenshot_ref=screenshot_ref, outcome=outcome)


@runtime_checkable
class Engine(Protocol):
    name: str
    default_step_cap: int

    def run_journey(self, session: SteelSession, journey: Journey, cfg: Config,
                    step_cap: int, ctx: RunContext) -> AsyncIterator[RunEvent]: ...
