from crucible.runner.matrix import BASELINE
from crucible.schemas import Config, Journey, RunResult, SiteModel
from crucible.scorer.score import journey_score, score_card, weight_for

MOBILE = Config(device="mobile", label="mobile")
RETURNING = Config(identity="returning", label="returning")
COUNTRY_CA = Config(country="CA", label="country:CA")


def result(journey_id: str, cfg: Config, outcome: str, run_id: str | None = None) -> RunResult:
    return RunResult(run_id=run_id or f"{journey_id}__{cfg.label}", journey_id=journey_id, config=cfg,
                     session_id="s", outcome=outcome, events=[])


def test_weight_for_baseline_is_2_and_variant_is_1():
    assert weight_for(BASELINE) == 2
    assert weight_for(MOBILE) == 1


def test_weight_for_relabeled_structural_baseline_is_still_2():
    # Locks in the fix over make_fixtures.py's config.label == "baseline" string shortcut.
    relabeled = Config(device="desktop", identity="fresh", country="US", engine="browser_use", label="whatever")
    assert weight_for(relabeled) == 2


def test_journey_score_matches_golden_scorecard_arithmetic():
    j = Journey(id="find_product", name="n", goal="g", entry_url="https://x")
    rs = [
        result("find_product", BASELINE, "completed"),
        result("find_product", MOBILE, "stalled"),
        result("find_product", RETURNING, "completed"),
        result("find_product", COUNTRY_CA, "completed"),
    ]
    js = journey_score(j, rs)
    # weights [2,1,1,1], completed_weight = 2+1+1 = 4, score = 100*4/5 = 80.0
    assert js.score == 80.0 and js.completed == 3 and js.stalled == 1 and js.harness_errors == 0


def test_harness_errors_excluded_from_denominator_but_counted_separately():
    j = Journey(id="j", name="n", goal="g", entry_url="https://x")
    rs = [
        result("j", BASELINE, "completed"),
        result("j", MOBILE, "harness_error"),
    ]
    js = journey_score(j, rs)
    # only the baseline is "scored"; weight sum = 2, completed_weight = 2 -> 100.0, not penalized
    assert js.score == 100.0 and js.harness_errors == 1 and js.completed == 1


def test_all_harness_error_journey_scores_zero_without_crashing():
    j = Journey(id="j", name="n", goal="g", entry_url="https://x")
    rs = [result("j", BASELINE, "harness_error"), result("j", MOBILE, "harness_error")]
    js = journey_score(j, rs)
    assert js.score == 0.0 and js.harness_errors == 2 and js.completed == 0 and js.stalled == 0


def test_empty_results_for_journey_scores_zero_without_crashing():
    j = Journey(id="j", name="n", goal="g", entry_url="https://x")
    js = journey_score(j, [])
    assert js.score == 0.0 and js.completed == js.stalled == js.harness_errors == 0


def test_score_card_reproduces_golden_scorecard(site_model: SiteModel, golden_scorecard):
    results = []
    for j in site_model.journeys:
        results += [
            result(j.id, BASELINE, "completed"),
            result(j.id, MOBILE, "stalled"),
            result(j.id, RETURNING, "completed"),
            result(j.id, COUNTRY_CA, "completed"),
        ]
    card = score_card(site_model, results, static_score=85.0)
    assert card.overall == golden_scorecard.overall
    assert {p.journey_id: p.score for p in card.per_journey} == {p.journey_id: p.score for p in golden_scorecard.per_journey}


def test_score_card_static_score_none_on_failure(site_model: SiteModel):
    card = score_card(site_model, [], static_score=None)
    assert card.static_score is None


def test_score_card_empty_journeys_scores_zero():
    site = SiteModel(url="https://x", journeys=[])
    card = score_card(site, [], static_score=None)
    assert card.overall == 0.0 and card.per_journey == []
