from crucible.schemas import Config, RunResult
from crucible.scorer.attribute import attribute

BASELINE = Config(device="desktop", identity="fresh", country="US", engine="browser_use", label="baseline")
MOBILE = Config(device="mobile", identity="fresh", country="US", engine="browser_use", label="mobile")
RETURNING = Config(device="desktop", identity="returning", country="US", engine="browser_use", label="returning")
CLAUDE_BASE = Config(device="desktop", identity="fresh", country="US", engine="claude_cu", label="engine:claude_cu")
OPENAI_BASE = Config(device="desktop", identity="fresh", country="US", engine="openai_cu", label="engine:openai_cu")


def result(journey_id: str, cfg: Config, outcome: str, run_id: str | None = None) -> RunResult:
    return RunResult(run_id=run_id or f"{journey_id}__{cfg.label}", journey_id=journey_id, config=cfg,
                     session_id="s", outcome=outcome, events=[])


def test_variant_stall_attributed_to_its_own_axis():
    rs = [result("j", BASELINE, "completed"), result("j", MOBILE, "stalled")]
    out = attribute(rs, {rs[1].run_id: "cookie_wall"})
    assert out[rs[1].run_id] == ("device", False)


def test_returning_variant_stall_attributed_to_identity():
    rs = [result("j", BASELINE, "completed"), result("j", RETURNING, "stalled")]
    out = attribute(rs, {rs[1].run_id: "login_wall"})
    assert out[rs[1].run_id] == ("identity", False)


def test_baseline_itself_stalling_is_attributed_to_site():
    rs = [result("j", BASELINE, "stalled")]
    out = attribute(rs, {rs[0].run_id: "timeout"})
    assert out[rs[0].run_id] == ("site", False)


def test_variant_stall_when_baseline_also_stalls_is_site_not_the_axis():
    rs = [result("j", BASELINE, "stalled"), result("j", MOBILE, "stalled")]
    out = attribute(rs, {rs[0].run_id: "timeout", rs[1].run_id: "timeout"})
    assert out[rs[1].run_id][0] == "site"
    assert out[rs[0].run_id][0] == "site"


def test_missing_baseline_defaults_to_site():
    rs = [result("j", MOBILE, "stalled")]
    out = attribute(rs, {rs[0].run_id: "cookie_wall"})
    assert out[rs[0].run_id] == ("site", False)


def test_completed_results_produce_no_attribution_entry():
    rs = [result("j", BASELINE, "completed"), result("j", MOBILE, "completed")]
    out = attribute(rs, {})
    assert out == {}


def test_engine_consensus_true_when_all_engines_agree_on_category():
    rs = [
        result("j", BASELINE, "stalled"),
        result("j", CLAUDE_BASE, "stalled"),
        result("j", OPENAI_BASE, "stalled"),
    ]
    cats = {r.run_id: "cookie_wall" for r in rs}
    out = attribute(rs, cats)
    assert all(out[r.run_id][1] is True for r in rs)


def test_engine_consensus_false_when_categories_disagree():
    rs = [result("j", BASELINE, "stalled"), result("j", CLAUDE_BASE, "stalled")]
    cats = {rs[0].run_id: "cookie_wall", rs[1].run_id: "timeout"}
    out = attribute(rs, cats)
    assert out[rs[0].run_id][1] is False and out[rs[1].run_id][1] is False


def test_engine_consensus_false_when_one_engine_completes():
    rs = [result("j", BASELINE, "stalled"), result("j", CLAUDE_BASE, "completed")]
    cats = {rs[0].run_id: "cookie_wall"}
    out = attribute(rs, cats)
    assert out[rs[0].run_id][1] is False


def test_site_attribution_and_engine_consensus_can_co_occur():
    # Baseline itself stalls (-> "site") AND every engine agrees (-> consensus=True): the
    # design doc's "strongest evidence" case.
    rs = [result("j", BASELINE, "stalled"), result("j", CLAUDE_BASE, "stalled")]
    cats = {r.run_id: "timeout" for r in rs}
    out = attribute(rs, cats)
    assert out[rs[0].run_id] == ("site", True)
    assert out[rs[1].run_id] == ("site", True)
