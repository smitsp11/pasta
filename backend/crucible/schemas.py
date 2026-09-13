"""Shared contracts between Explore (B), Runner/engines (A), Scorer (C), and UI (D).

Changes here are all-hands. Every module builds against these models and the
fixtures under fixtures/.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------- Explore ---

class Journey(BaseModel):
    id: str
    name: str
    goal: str            # specific, executable instruction for an agent
    entry_url: str


class SiteModel(BaseModel):
    url: str
    brand: str = ""
    category: str = ""
    description: str = ""
    audience_guess: list[str] = Field(default_factory=list)
    journeys: list[Journey] = Field(default_factory=list)


# ------------------------------------------------------------- Population ---

Device = Literal["desktop", "mobile"]
Identity = Literal["fresh", "returning"]
EngineName = Literal["browser_use", "claude_cu", "openai_cu"]


class Config(BaseModel):
    """One point in the population matrix. Hashable so it can key dicts."""
    model_config = ConfigDict(frozen=True)

    device: Device = "desktop"
    identity: Identity = "fresh"
    country: str = "US"
    engine: EngineName = "browser_use"
    label: str = "baseline"

    def diff_from(self, base: "Config") -> list[str]:
        """Names of the fields that differ from `base` (attribution uses this)."""
        return [f for f in ("device", "identity", "country", "engine")
                if getattr(self, f) != getattr(base, f)]


# ------------------------------------------------------------------ Runner ---

Outcome = Literal["none", "step_ok", "completed", "stalled", "harness_error"]
TerminalOutcome = Literal["completed", "stalled", "harness_error"]
TERMINAL: frozenset[str] = frozenset({"completed", "stalled", "harness_error"})


class RunEvent(BaseModel):
    type: Literal["run_event"] = "run_event"
    run_id: str
    session_id: str
    journey_id: str
    config: Config
    step_index: int
    timestamp: datetime = Field(default_factory=utcnow)
    action: str
    observation: str = ""
    screenshot_ref: str | None = None
    outcome: Outcome = "step_ok"


class SessionStarted(BaseModel):
    type: Literal["session_started"] = "session_started"
    run_id: str
    session_id: str
    journey_id: str
    config: Config
    viewer_url: str
    replay_url: str
    hls_url: str
    timestamp: datetime = Field(default_factory=utcnow)


class RunResult(BaseModel):
    type: Literal["run_result"] = "run_result"
    run_id: str
    journey_id: str
    config: Config
    session_id: str | None
    outcome: TerminalOutcome
    attempt: int = 1
    events: list[RunEvent] = Field(default_factory=list)
    replay_url: str | None = None
    hls_url: str | None = None
    final_screenshot_ref: str | None = None
    failure_step_index: int | None = None     # jump-to-failure
    replay_offset_s: float | None = None      # seconds into the HLS replay
    harness_reason: str | None = None         # only for harness_error
    stall_hint: str | None = None             # e.g. "step_cap", "run_budget"


class StageMarker(BaseModel):
    type: Literal["stage"] = "stage"
    name: Literal["explore", "run", "score", "fix", "done"]
    timestamp: datetime = Field(default_factory=utcnow)


PipelineEvent = RunEvent | SessionStarted | RunResult | StageMarker


# ------------------------------------------------------------------ Scorer ---

FailureCategory = Literal[
    "cookie_wall", "captcha", "hidden_nav", "icon_only_control", "ambiguous_cta",
    "geo_block", "infinite_scroll", "login_wall", "layout_shift", "timeout", "other",
]
AttributedTo = Literal["device", "identity", "country", "engine", "site"]


class Finding(BaseModel):
    id: str
    journey_id: str
    config: Config
    category: FailureCategory
    description: str
    attributed_to: AttributedTo
    engine_consensus: bool = False
    session_id: str | None = None
    step_index: int | None = None
    replay_url: str | None = None
    replay_offset_s: float | None = None
    proposed_fix: str = ""


class JourneyScore(BaseModel):
    journey_id: str
    score: float
    completed: int
    stalled: int
    harness_errors: int


class ScoreCard(BaseModel):
    overall: float
    static_score: float | None = None
    per_journey: list[JourneyScore] = Field(default_factory=list)
