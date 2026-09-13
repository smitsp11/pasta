"""Generate fixtures/ from the fake pipeline: one example per schema, a completed and a stalled
RunResult, and a full canned run (demo_run.json) for the UI and the API stub.

  .venv/bin/python scripts/make_fixtures.py
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from crucible.engines.fake import FakeEngine
from crucible.runner import run_matrix
from crucible.runner.matrix import MVP_CONFIGS
from crucible.schemas import (Config, Finding, Journey, JourneyScore, RunResult, ScoreCard, SessionStarted,
                              SiteModel, StageMarker)
from crucible.testing import FakeSessionFactory, profile_ready

OUT = Path("fixtures")

SITE = SiteModel(
    url="https://demo-store.example", brand="Northwind Outfitters", category="ecommerce / apparel",
    description="Mid-size Shopify-style clothing store with a cookie consent modal and a mobile hamburger nav.",
    audience_guess=["outdoor apparel shoppers", "returning customers with accounts"],
    journeys=[
        Journey(id="find_product", name="Find a product",
                goal="From the home page, open the 'All products' collection and open the first product's page.",
                entry_url="https://demo-store.example/"),
        Journey(id="add_to_cart", name="Add to cart",
                goal="Open any product page, add it to the cart, and open the cart page.",
                entry_url="https://demo-store.example/collections/all"),
        Journey(id="reach_checkout", name="Reach checkout",
                goal="With one item in the cart, proceed to checkout and stop at the payment step. Do not pay.",
                entry_url="https://demo-store.example/cart"),
    ],
)

COMPLETED_STEPS = [
    ("go_to_url(url='https://demo-store.example/')", "https://demo-store.example/"),
    ("click_element_by_index(index=2, text='Accept cookies')", "https://demo-store.example/"),
    ("click_element_by_index(index=7, text='All products')", "https://demo-store.example/collections/all"),
    ("click_element_by_index(index=12, text='Trail Jacket')", "https://demo-store.example/products/trail-jacket"),
    ("click_element_by_index(index=21, text='Add to cart')", "https://demo-store.example/cart"),
]
COOKIE_WALL_STEPS = [
    ("go_to_url(url='https://demo-store.example/')", "https://demo-store.example/"),
    ("click_element_by_index(index=7, text='All products')", "https://demo-store.example/\nclick intercepted by overlay #consent-modal"),
    ("scroll(down=500)", "https://demo-store.example/\noverlay still present"),
    ("click_element_by_index(index=7, text='All products')", "https://demo-store.example/\nclick intercepted by overlay #consent-modal"),
]


class ScriptedEngine(FakeEngine):
    """Completed on desktop, cookie-walled on mobile (the headline demo finding)."""

    async def run_journey(self, session, journey, cfg, step_cap, ctx):
        if cfg.device == "mobile":
            self.steps, self.terminal = COOKIE_WALL_STEPS, "stalled"
        else:
            self.steps, self.terminal = COMPLETED_STEPS, "completed"
        async for ev in super().run_journey(session, journey, cfg, step_cap, ctx):
            yield ev


async def main() -> None:
    OUT.mkdir(exist_ok=True)
    events: list = [StageMarker(name="explore"), StageMarker(name="run")]
    results: list[RunResult] = []
    async for it in run_matrix(SITE, MVP_CONFIGS, {"browser_use": ScriptedEngine()},
                               session_factory=FakeSessionFactory(), profile_waiter=profile_ready,
                               max_retries=0):
        events.append(it)
        if isinstance(it, RunResult):
            results.append(it)
    events.append(StageMarker(name="score"))

    mobile_stall = next(r for r in results if r.config.label == "mobile" and r.outcome == "stalled")
    findings = [Finding(
        id="f1", journey_id=mobile_stall.journey_id, config=mobile_stall.config, category="cookie_wall",
        description="On mobile, the consent modal intercepts every click and its accept button is off-screen; "
                    "the agent never reaches the collection page.",
        attributed_to="device", engine_consensus=False, session_id=mobile_stall.session_id,
        step_index=mobile_stall.failure_step_index, replay_url=mobile_stall.replay_url,
        replay_offset_s=mobile_stall.replay_offset_s,
        proposed_fix="Make the consent modal's Accept button visible in the mobile viewport, first in DOM order, "
                     "and give the dialog role=\"dialog\" with aria-label=\"Cookie consent\".",
    )]
    per_journey = []
    for j in SITE.journeys:
        rs = [r for r in results if r.journey_id == j.id]
        scored = [r for r in rs if r.outcome != "harness_error"]
        weights = [2 if r.config.label == "baseline" else 1 for r in scored]
        done = [w for r, w in zip(scored, weights) if r.outcome == "completed"]
        score = round(100 * sum(done) / max(sum(weights), 1), 1)
        per_journey.append(JourneyScore(journey_id=j.id, score=score,
                                        completed=sum(r.outcome == "completed" for r in rs),
                                        stalled=sum(r.outcome == "stalled" for r in rs),
                                        harness_errors=sum(r.outcome == "harness_error" for r in rs)))
    card = ScoreCard(overall=round(sum(p.score for p in per_journey) / len(per_journey), 1), static_score=85.0,
                     per_journey=per_journey)
    events.append(StageMarker(name="done"))

    completed = next(r for r in results if r.outcome == "completed" and r.config.label == "baseline")
    started = next(e for e in events if isinstance(e, SessionStarted))
    dump = lambda m: json.dumps(m.model_dump(mode="json"), indent=2)  # noqa: E731
    (OUT / "site_model.json").write_text(dump(SITE))
    (OUT / "config.json").write_text(json.dumps([c.model_dump() for c in MVP_CONFIGS], indent=2))
    (OUT / "session_started.json").write_text(dump(started))
    (OUT / "run_event.json").write_text(dump(completed.events[1]))
    (OUT / "run_result_completed.json").write_text(dump(completed))
    (OUT / "run_result_stalled.json").write_text(dump(mobile_stall))
    (OUT / "finding.json").write_text(dump(findings[0]))
    (OUT / "scorecard.json").write_text(dump(card))
    (OUT / "demo_run.json").write_text(json.dumps({
        "site_model": SITE.model_dump(mode="json"),
        "events": [e.model_dump(mode="json") for e in events],
        "findings": [f.model_dump(mode="json") for f in findings],
        "scorecard": card.model_dump(mode="json"),
    }, indent=2))
    print(f"wrote {len(list(OUT.iterdir()))} files to {OUT}/; {len(results)} results, "
          f"{sum(r.outcome == 'stalled' for r in results)} stalled")


if __name__ == "__main__":
    asyncio.run(main())
