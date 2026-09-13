from crucible.schemas import Config, RunEvent, RunResult
from crucible.scorer.fixes import GENERIC_ELEMENT, TEMPLATES, offending_element, proposed_fix

CFG = Config()


def ev(step_index: int, action: str, observation: str = "", outcome: str = "step_ok") -> RunEvent:
    return RunEvent(run_id="r", session_id="s", journey_id="j", config=CFG, step_index=step_index,
                    action=action, observation=observation, outcome=outcome)


def result(events: list[RunEvent], failure_step_index: int | None) -> RunResult:
    return RunResult(run_id="r", journey_id="j", config=CFG, session_id="s", outcome="stalled",
                     events=events, failure_step_index=failure_step_index)


def test_extracts_id_selector_near_failure_step():
    events = [
        ev(1, "click", "https://x"),
        ev(2, "click", "click intercepted by overlay #consent-modal"),
        ev(3, "done", "stalled", outcome="stalled"),
    ]
    r = result(events, failure_step_index=2)
    assert offending_element(r) == "#consent-modal"


def test_extracts_quoted_text_when_no_id_selector():
    events = [ev(1, "click_element_by_index(index=7, text='All products')", "https://x")]
    r = result(events, failure_step_index=1)
    assert offending_element(r) == 'the "All products" element'


def test_falls_back_to_empty_when_nothing_extractable():
    events = [ev(1, "wait", "nothing useful here")]
    r = result(events, failure_step_index=1)
    assert offending_element(r) == ""


def test_no_events_returns_empty_element():
    r = result([], failure_step_index=None)
    assert offending_element(r) == ""


def test_proposed_fix_names_the_offending_element():
    events = [ev(1, "click", "click intercepted by overlay #consent-modal")]
    r = result(events, failure_step_index=1)
    fix = proposed_fix("cookie_wall", r)
    assert "#consent-modal" in fix and "{element}" not in fix


def test_proposed_fix_falls_back_to_generic_noun_phrase_when_no_element_extractable():
    r = result([ev(1, "wait", "nothing useful")], failure_step_index=1)
    fix = proposed_fix("captcha", r)
    assert GENERIC_ELEMENT["captcha"] in fix and "{element}" not in fix


def test_every_failure_category_has_a_template_and_produces_nonempty_text():
    r = result([ev(1, "wait", "no signal")], failure_step_index=1)
    for category in TEMPLATES:
        fix = proposed_fix(category, r)
        assert fix and "{element}" not in fix
