import asyncio

import pytest

from crucible.engines.fake import FakeEngine
from crucible.runner import run_matrix
from crucible.runner.matrix import MVP_CONFIGS
from crucible.schemas import Config, RunResult, SessionStarted
from tests.conftest import FakeSessionFactory, profile_ready


async def collect(site, configs, engines, **kw):
    items = []
    async for it in run_matrix(site, configs, engines, profile_waiter=profile_ready, **kw):
        items.append(it)
    return items


def results(items):
    return {r.run_id: r for r in items if isinstance(r, RunResult)}


async def test_full_mvp_matrix_completes(site, factory):
    items = await collect(site, MVP_CONFIGS, {"browser_use": FakeEngine()}, session_factory=factory)
    res = results(items)
    assert len(res) == 8 and all(r.outcome == "completed" for r in res.values())
    assert sum(isinstance(i, SessionStarted) for i in items) == 8
    # every session released exactly once
    assert sorted(factory.client.released) == sorted(s.session_id for s in factory.opened)
    assert len(set(factory.client.released)) == 8
    # results carry replay linkage
    r = res["find_product__mobile"]
    assert r.session_id and r.replay_url and r.hls_url and r.final_screenshot_ref
    assert r.failure_step_index is None and r.replay_offset_s is not None


async def test_returning_waits_for_baseline_profile(site, factory):
    eng = FakeEngine(step_delay_s=0.01)
    items = await collect(site, MVP_CONFIGS, {"browser_use": eng}, session_factory=factory)
    # order of engine calls: baseline for a journey strictly before its returning variant
    calls = eng.calls
    for j in ("find_product", "reach_checkout"):
        assert calls.index((j, "baseline")) < calls.index((j, "returning"))
    # the returning session was created with the baseline's profile id
    created = factory.client.created
    persisted = [kw for kw in created if kw.get("persist_profile")]
    returning = [kw for kw in created if kw.get("profile_id")]
    assert len(persisted) == 2 and len(returning) == 2
    assert {kw["profile_id"] for kw in returning} <= {"prof-1", "prof-2", "prof-3", "prof-4"}
    # SessionStarted precedes the first RunEvent of that session
    seen = set()
    for it in items:
        if isinstance(it, SessionStarted):
            seen.add(it.session_id)
        elif it.type == "run_event":
            assert it.session_id in seen


async def test_concurrency_bounded(site, factory):
    eng = FakeEngine(step_delay_s=0.02)
    await collect(site, MVP_CONFIGS, {"browser_use": eng}, session_factory=factory, max_concurrency=3)
    assert factory.max_open <= 3


async def test_stalled_retried_once_then_reported(site, factory):
    eng = FakeEngine(terminal="stalled")
    cfgs = [MVP_CONFIGS[0]]
    res = results(await collect(site, cfgs, {"browser_use": eng}, session_factory=factory))
    assert all(r.outcome == "stalled" and r.attempt == 2 for r in res.values())
    assert len(factory.client.released) == 4          # 2 journeys × 2 attempts
    assert all(r.failure_step_index == 3 for r in res.values())


async def test_completed_never_retried(site, factory):
    res = results(await collect(site, [MVP_CONFIGS[0]], {"browser_use": FakeEngine()}, session_factory=factory))
    assert all(r.attempt == 1 for r in res.values())


async def test_engine_exception_is_harness_error_and_retried(site, factory):
    eng = FakeEngine(raise_at_step=2)
    res = results(await collect(site, [MVP_CONFIGS[0]], {"browser_use": eng}, session_factory=factory))
    r = res["find_product__baseline"]
    assert r.outcome == "harness_error" and r.attempt == 2 and "RuntimeError" in r.harness_reason
    assert len(r.events) == 1                         # events before the crash are kept
    assert sorted(factory.client.released) == sorted(s.session_id for s in factory.opened)


async def test_steel_create_failure_is_harness_error(site, factory):
    factory.fail_labels = {"country:CA"}
    res = results(await collect(site, MVP_CONFIGS, {"browser_use": FakeEngine()}, session_factory=factory))
    ca = [r for r in res.values() if r.config.label == "country:CA"]
    assert all(r.outcome == "harness_error" and "steel_unavailable" in r.harness_reason for r in ca)
    others = [r for r in res.values() if r.config.label != "country:CA"]
    assert all(r.outcome == "completed" for r in others)


async def test_step_cap_cuts_never_ending_engine(site, factory):
    eng = FakeEngine(terminal=None)
    res = results(await collect(site, [MVP_CONFIGS[0]], {"browser_use": eng}, session_factory=factory,
                                step_caps={"browser_use": 5}, max_retries=0))
    r = res["find_product__baseline"]
    assert r.outcome == "stalled" and r.stall_hint == "step_cap" and len(r.events) == 5


async def test_run_budget_cuts_slow_engine(site, factory):
    eng = FakeEngine(terminal=None, step_delay_s=0.02)
    res = results(await collect(site, [MVP_CONFIGS[0]], {"browser_use": eng}, session_factory=factory,
                                run_budget_s=0.1, max_retries=0))
    assert all(r.outcome == "stalled" and r.stall_hint == "run_budget" for r in res.values())
    assert len(factory.client.released) == 2


async def test_payment_guard_ends_run_as_completed(site, factory):
    eng = FakeEngine(terminal=None, steps=[("click 'Checkout'", "https://x.test/cart"),
                                           ("navigate", "https://x.test/checkout/payment")])
    res = results(await collect(site, [MVP_CONFIGS[0]], {"browser_use": eng}, session_factory=factory))
    assert all(r.outcome == "completed" and r.stall_hint == "payment_guard" for r in res.values())


async def test_cancel_releases_every_session(site, factory):
    eng = FakeEngine(terminal=None, step_delay_s=0.02)
    gen = run_matrix(site, MVP_CONFIGS, {"browser_use": eng}, session_factory=factory, profile_waiter=profile_ready)
    started = 0
    async for it in gen:
        if isinstance(it, SessionStarted):
            started += 1
        if started >= 2 and it.type == "run_event":
            break
    await gen.aclose()
    await asyncio.sleep(0.05)
    assert factory.open_now == 0
    assert sorted(factory.client.released) == sorted(s.session_id for s in factory.opened)
    assert len(factory.client.released) == len(set(factory.client.released))


async def test_profile_not_ready_marks_returning_harness_error(site, factory):
    async def never_ready(_pid):
        return False
    res = {}
    async for it in run_matrix(site, MVP_CONFIGS, {"browser_use": FakeEngine()}, session_factory=factory,
                               profile_waiter=never_ready):
        if isinstance(it, RunResult):
            res[it.run_id] = it
    ret = [r for r in res.values() if r.config.identity == "returning"]
    assert all(r.outcome == "harness_error" and r.harness_reason == "profile_not_ready" for r in ret)
    assert all(r.outcome == "completed" for r in res.values() if r.config.identity != "returning")


async def test_missing_engine_rejected(site, factory):
    with pytest.raises(ValueError):
        async for _ in run_matrix(site, MVP_CONFIGS, {}, session_factory=factory):
            pass
