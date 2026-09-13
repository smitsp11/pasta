from crucible.schemas import Config, RunEvent, RunResult
from crucible.scorer.classify import URL_STALL_STEPS, classify, classify_deterministic
from tests.scorer.conftest import FakeClassifier

CFG = Config()


def ev(step_index: int, action: str, observation: str = "", outcome: str = "step_ok") -> RunEvent:
    return RunEvent(run_id="r", session_id="s", journey_id="j", config=CFG, step_index=step_index,
                    action=action, observation=observation, outcome=outcome)


def result(events: list[RunEvent], *, stall_hint: str | None = None, final_screenshot_ref: str | None = None) -> RunResult:
    return RunResult(run_id="r", journey_id="j", config=CFG, session_id="s", outcome="stalled",
                     events=events, stall_hint=stall_hint, final_screenshot_ref=final_screenshot_ref)


def test_stall_hint_step_cap_wins_immediately():
    r = result([ev(1, "click", "https://x")], stall_hint="step_cap")
    cat, desc = classify_deterministic(r)
    assert cat == "timeout" and "step cap" in desc


def test_captcha_text_detected():
    r = result([ev(1, "click", "a recaptcha iframe appeared")])
    cat, _ = classify_deterministic(r)
    assert cat == "captcha"


def test_geo_block_text_detected():
    r = result([ev(1, "go_to_url", "This content is not available in your country")])
    cat, _ = classify_deterministic(r)
    assert cat == "geo_block"


def test_specific_signal_beats_generic_url_unchanged(stalled_result: RunResult):
    # fixtures/run_result_stalled.json never changes URL across its steps, so a naive
    # URL-unchanged-first classifier would call this "timeout" -- it must be "cookie_wall".
    cat, _ = classify_deterministic(stalled_result)
    assert cat == "cookie_wall"


def test_url_unchanged_fallback_is_timeout_when_no_specific_signal():
    same_url = "https://demo-store.example/stuck"
    events = [ev(i, "wait", same_url) for i in range(1, URL_STALL_STEPS + 1)]
    r = result(events)
    cat, _ = classify_deterministic(r)
    assert cat == "timeout"


def test_url_unchanged_needs_full_window_not_fewer_steps():
    events = [ev(i, "wait", "https://x/stuck") for i in range(1, URL_STALL_STEPS)]  # one short
    r = result(events)
    assert classify_deterministic(r) is None


def test_no_deterministic_signal_returns_none():
    events = [ev(1, "click", "https://a"), ev(2, "click", "https://b")]
    r = result(events)
    assert classify_deterministic(r) is None


async def test_classify_falls_through_to_llm_when_no_deterministic_signal():
    r = result([ev(1, "click", "https://a"), ev(2, "click", "https://b")])
    fake = FakeClassifier(category="hidden_nav", description="hidden nav found")
    cat, desc = await classify(r, llm=fake)
    assert cat == "hidden_nav" and desc == "hidden nav found" and fake.calls == ["r"]


async def test_classify_never_raises_when_llm_fails():
    r = result([ev(1, "click", "https://a"), ev(2, "click", "https://b")])
    fake = FakeClassifier(raise_error=True)
    cat, desc = await classify(r, llm=fake)
    assert cat == "other" and "failed" in desc.lower()


async def test_classify_deterministic_path_never_calls_llm():
    r = result([ev(1, "click", "recaptcha challenge shown")])
    fake = FakeClassifier()
    cat, _ = await classify(r, llm=fake)
    assert cat == "captcha" and fake.calls == []
