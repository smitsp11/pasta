"""Structural "is this the baseline config" check, shared by score.py and attribute.py.

Mirrors RunSpec.is_baseline in crucible/runner/matrix.py exactly, so Scorer and Runner never
disagree about which run in a journey is the baseline: a config counts as baseline if it is
labeled "baseline" (the convention every config list in this repo follows) OR it is
structurally identical to runner.matrix.BASELINE (desktop/fresh/US/browser_use) once `label`
is ignored -- so a config list that forgets the label still scores/attributes correctly.
"""
from __future__ import annotations

from ..runner.matrix import BASELINE
from ..schemas import Config


def is_baseline(cfg: Config) -> bool:
    return cfg.label == "baseline" or cfg.diff_from(BASELINE) == []
