import pytest

from crucible.runner.matrix import MVP_CONFIGS, SHOULD_CONFIGS, build_matrix
from crucible.schemas import Config


def test_mvp_matrix_shape(site):
    specs = build_matrix(site, MVP_CONFIGS)
    assert len(specs) == 2 * 4
    assert [s.cfg.label for s in specs[:2]] == ["baseline", "baseline"]
    assert all(s.persist_profile for s in specs[:2])          # returning variant exists
    ret = [s for s in specs if s.cfg.identity == "returning"]
    assert {s.needs_profile_from for s in ret} == {"find_product__baseline", "reach_checkout__baseline"}


def test_no_returning_means_no_persist(site):
    cfgs = [c for c in MVP_CONFIGS if c.identity != "returning"]
    specs = build_matrix(site, cfgs)
    assert not any(s.persist_profile for s in specs)


def test_should_configs_are_one_variable_each(site):
    build_matrix(site, SHOULD_CONFIGS)


def test_two_variable_config_rejected(site):
    bad = MVP_CONFIGS + [Config(device="mobile", country="DE", label="mobile+DE")]
    with pytest.raises(ValueError):
        build_matrix(site, bad)


def test_step_caps_applied(site):
    specs = build_matrix(site, MVP_CONFIGS, step_caps={"browser_use": 7})
    assert all(s.step_cap == 7 for s in specs)
