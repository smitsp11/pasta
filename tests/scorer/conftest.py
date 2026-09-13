import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Type, TypeVar

import pytest
from pydantic import BaseModel

from crucible.runner.matrix import MVP_CONFIGS
from crucible.schemas import Config, EvidencePack, Finding, Persona, RunResult, ScoreCard, SiteModel

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"
M = TypeVar("M", bound=BaseModel)


def load_fixture(name: str, model: Type[M]) -> M:
    return model.model_validate(json.loads((FIXTURES_DIR / name).read_text()))


@pytest.fixture
def site_model() -> SiteModel:
    return load_fixture("site_model.json", SiteModel)


@pytest.fixture
def mvp_configs() -> list[Config]:
    return list(MVP_CONFIGS)


@pytest.fixture
def completed_result() -> RunResult:
    return load_fixture("run_result_completed.json", RunResult)


@pytest.fixture
def stalled_result() -> RunResult:
    return load_fixture("run_result_stalled.json", RunResult)


@pytest.fixture
def golden_finding() -> Finding:
    return load_fixture("finding.json", Finding)


@pytest.fixture
def golden_scorecard() -> ScoreCard:
    return load_fixture("scorecard.json", ScoreCard)


@pytest.fixture
def evidence_pack() -> EvidencePack:
    return load_fixture("evidence_pack.json", EvidencePack)


@pytest.fixture
def personas() -> list[Persona]:
    raw = json.loads((FIXTURES_DIR / "personas.json").read_text())
    return [Persona.model_validate(p) for p in raw]


@dataclass
class FakeClassifier:
    """Scripted Classifier for tests: no network, no Anthropic key required."""

    category: str = "other"
    description: str = "fake classification"
    raise_error: bool = False
    calls: list[str] = field(default_factory=list)

    async def classify(self, result: RunResult, screenshot: bytes | None):
        self.calls.append(result.run_id)
        if self.raise_error:
            raise RuntimeError("fake classifier failure")
        return self.category, self.description
