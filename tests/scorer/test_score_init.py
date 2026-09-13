import json

from crucible.schemas import Config, Journey, RunEvent, RunResult, SiteModel
from crucible.scorer import score
from tests.scorer.conftest import FIXTURES_DIR, FakeClassifier

CFG = Config()
J = Journey(id="j", name="j", goal="g", entry_url="https://x")
SITE = SiteModel(url="https://demo-store.example", journeys=[J])


def load_demo_run() -> tuple[SiteModel, list[RunResult]]:
    raw = json.loads((FIXTURES_DIR / "demo_run.json").read_text())
    site = SiteModel.model_validate(raw["site_model"])
    results = [RunResult.model_validate(e) for e in raw["events"] if e.get("type") == "run_result"]
    return site, results


def ev(step_index: int, action: str, observation: str = "", outcome: str = "step_ok") -> RunEvent:
    return RunEvent(run_id="r", session_id="s", journey_id="j", config=CFG, step_index=step_index,
                    action=action, observation=observation, outcome=outcome)


def result(journey_id: str, cfg: Config, outcome: str, events: list[RunEvent] | None = None,
          run_id: str | None = None, stall_hint: str | None = None) -> RunResult:
    return RunResult(run_id=run_id or f"{journey_id}__{cfg.label}", journey_id=journey_id, config=cfg,
                     session_id="s", outcome=outcome, events=events or [], stall_hint=stall_hint)


async def test_only_stalled_results_become_findings():
    rs = [result("j", CFG, "completed"), result("j", CFG, "harness_error", run_id="j__err")]
    card, findings = await score(SITE, rs)
    assert findings == [] and card.per_journey[0].completed == 1 and card.per_journey[0].harness_errors == 1


async def test_finding_reproduces_golden_category_and_attribution_for_mobile_stall(
    site_model: SiteModel, completed_result: RunResult, stalled_result: RunResult, golden_finding
):
    card, findings = await score(site_model, [completed_result, stalled_result])
    assert len(findings) == 1
    f = findings[0]
    # category/attribution are the parts classify_deterministic + attribute() can derive; the
    # hand-authored description/proposed_fix prose in finding.json isn't reproducible byte-for-byte.
    assert f.category == golden_finding.category == "cookie_wall"
    assert f.attributed_to == golden_finding.attributed_to == "device"
    assert f.session_id == stalled_result.session_id
    assert f.step_index == stalled_result.failure_step_index
    assert "#consent-modal" in f.proposed_fix


async def test_classifier_failure_is_isolated_to_other_category_not_a_crash():
    # No stall_hint and no deterministic text signal -> forces the LLM path.
    events = [ev(1, "click", "https://a"), ev(2, "click", "https://b")]
    rs = [result("j", CFG, "completed", run_id="j__baseline"), result("j", CFG, "stalled", events=events, run_id="j__mobile")]
    card, findings = await score(SITE, rs, classifier=FakeClassifier(raise_error=True))
    assert len(findings) == 1 and findings[0].category == "other"
    assert card.per_journey[0].stalled == 1  # score_card itself is unaffected by the classifier failure


async def test_score_signature_accepts_site_and_results_only():
    # Locks the public contract: score(site, results) -> (ScoreCard, list[Finding])
    card, findings = await score(SITE, [])
    assert card.overall == 0.0 and findings == []


async def test_static_score_is_none_without_a_confirmed_endpoint():
    card, _ = await score(SITE, [])
    assert card.static_score is None


async def test_full_demo_run_pipeline_reproduces_golden_scorecard_shape():
    site, results = load_demo_run()
    card, findings = await score(site, results)
    # 3 journeys x 4 configs, mobile stalls on each -> 3 findings, all cookie_wall/device
    assert len(findings) == 3
    assert all(f.category == "cookie_wall" and f.attributed_to == "device" for f in findings)
    assert card.overall == 80.0
    assert all(p.score == 80.0 and p.completed == 3 and p.stalled == 1 and p.harness_errors == 0 for p in card.per_journey)


async def test_no_env_vars_or_network_required_for_default_pipeline(monkeypatch):
    # Every stall in these fixtures resolves via deterministic classification, so the default
    # LLMClassifier is never actually invoked -- no ANTHROPIC_API_KEY needed.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    site, results = load_demo_run()
    card, findings = await score(site, results)
    assert len(findings) == 3 and card.overall == 80.0
