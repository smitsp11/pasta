"""FakeEngine for Runner tests and dry runs: replays scripted steps, no browser, no model."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import AsyncIterator

from ..schemas import Config, Journey, RunEvent
from .base import RunContext


@dataclass
class FakeEngine:
    name: str = "fake"
    default_step_cap: int = 25
    steps: list[tuple[str, str]] = field(default_factory=lambda: [
        ("navigate https://example.test/", "https://example.test/"),
        ('click "Shop"', "https://example.test/collections/all"),
        ('click "Add to cart"', "https://example.test/cart"),
    ])
    terminal: str | None = "completed"      # None = never terminates (tests step caps)
    raise_at_step: int | None = None        # raise RuntimeError at this step (-> harness_error)
    step_delay_s: float = 0.0
    calls: list[tuple[str, str]] = field(default_factory=list)   # (journey_id, label)

    async def run_journey(self, session, journey: Journey, cfg: Config, step_cap: int,
                          ctx: RunContext) -> AsyncIterator[RunEvent]:
        self.calls.append((journey.id, cfg.label))
        i = 0
        while True:
            for action, url in self.steps:
                i += 1
                if self.raise_at_step is not None and i == self.raise_at_step:
                    raise RuntimeError(f"fake engine crash at step {i}")
                if self.step_delay_s:
                    await asyncio.sleep(self.step_delay_s)
                yield ctx.event(i, action, url, screenshot_ref=f"fake/{ctx.session_id}/{i:03d}.png")
            if self.terminal is not None:
                yield ctx.event(i + 1, "done", self.steps[-1][1], outcome=self.terminal)  # type: ignore[arg-type]
                return
            if self.step_delay_s == 0:
                await asyncio.sleep(0)   # let the Runner cut us off
