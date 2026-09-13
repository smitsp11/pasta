from crucible.schemas import Complaint, Config, Persona, RunResult
from crucible.scorer.corroborate import corroborate, persona_for

BASELINE_CFG = Config(label="baseline")
MOBILE_CFG = Config(device="mobile", label="mobile")


def result(journey_id: str, cfg: Config, outcome: str = "stalled") -> RunResult:
    return RunResult(run_id=f"{journey_id}__{cfg.label}", journey_id=journey_id, config=cfg,
                     session_id="s", outcome=outcome, events=[])


def test_no_personas_is_never_corroborated():
    r = result("reach_checkout", MOBILE_CFG)
    c = corroborate(r, None)
    assert c.tag == "agent_readiness" and c.segment is None and c.evidence_quote is None


def test_persona_with_evidence_is_corroborated(personas: list[Persona]):
    r = result("reach_checkout", MOBILE_CFG)
    c = corroborate(r, personas)
    assert c.tag == "corroborated"
    assert c.segment == "returning bargain hunter"
    assert "resets" in c.evidence_quote
    assert c.evidence_url.startswith("https://")


def test_persona_without_evidence_is_agent_readiness_but_keeps_segment(personas: list[Persona]):
    r = result("reach_checkout", BASELINE_CFG)
    c = corroborate(r, personas)
    assert c.tag == "agent_readiness" and c.segment == "returning bargain hunter" and c.evidence_quote is None


def test_result_with_no_matching_persona_is_not_corroborated(personas: list[Persona]):
    r = result("some_other_journey", Config(country="CA", label="country:CA"))
    c = corroborate(r, personas)
    assert c.tag == "agent_readiness" and c.segment is None


def test_persona_for_matches_on_journey_and_config_exactly(personas: list[Persona]):
    r = result("find_product", Config(country="DE", label="country:DE"))
    p = persona_for(r, personas)
    assert p is not None and p.id == "p_de_freeform"


def test_persona_for_returns_none_when_config_differs(personas: list[Persona]):
    r = result("find_product", Config(country="GB", label="country:GB"))
    assert persona_for(r, personas) is None
