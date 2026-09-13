from crucible.runner.matrix import BASELINE, MVP_CONFIGS, RunSpec
from crucible.schemas import Config, Journey
from crucible.scorer.baseline import is_baseline

J = Journey(id="j", name="j", goal="g", entry_url="https://x")


def test_labeled_baseline_is_baseline():
    assert is_baseline(BASELINE)


def test_variant_configs_are_not_baseline():
    variants = [c for c in MVP_CONFIGS if c.label != "baseline"]
    assert variants and all(not is_baseline(c) for c in variants)


def test_structurally_equal_but_differently_labeled_config_is_still_baseline():
    # Generalization over scripts/make_fixtures.py's `config.label == "baseline"` shortcut: a
    # config with a different label but identical device/identity/country/engine must still count.
    relabeled = Config(device="desktop", identity="fresh", country="US", engine="browser_use", label="custom")
    assert is_baseline(relabeled)


def test_label_baseline_wins_even_if_structurally_different():
    weird = Config(device="mobile", identity="returning", country="DE", engine="claude_cu", label="baseline")
    assert is_baseline(weird)


def test_parity_with_run_spec_is_baseline():
    for cfg in list(MVP_CONFIGS) + [Config(device="mobile", label="mobile")]:
        spec = RunSpec(run_id="x", journey=J, cfg=cfg)
        assert is_baseline(cfg) == spec.is_baseline  # Scorer and Runner must never disagree
