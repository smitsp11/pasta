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


# ----------------------------------------------------------------- Research ---
# DRAFT, proposed on dev-c/research-schema-draft to match docs/ui-flow.md's Consumer
# research / Test brief screens. Not yet agreed with the team -- schema changes are
# all-hands per docs/plan.md. Every field below is additive with safe defaults so it
# does not change the behavior of any code that doesn't pass personas/evidence in.

class Complaint(BaseModel):
    """One piece of evidence gathered in Consumer research (a quote + where it came from)."""
    id: str
    quote: str
    url: str
    source: str = ""


class Segment(BaseModel):
    """A customer segment surfaced by Consumer research, with the quotes that back it."""
    name: str
    evidence: list[Complaint] = Field(default_factory=list)


class EvidencePack(BaseModel):
    """Output of Consumer research (ui-flow.md Screen 2, left half)."""
    segments: list[Segment] = Field(default_factory=list)
    complaints: list[Complaint] = Field(default_factory=list)


class Persona(BaseModel):
    """One of the 8 cards on the Test brief (ui-flow.md Screen 3).

    Matching a stalled RunResult back to the persona that produced it is exact on
    (journey_id, config) -- not semantic -- since Config is frozen/hashable and the
    Runner would launch one session per persona using exactly this config.
    """
    id: str
    segment: str
    journey_id: str
    config: Config
    goal: str
    evidence: Complaint | None = None       # the quote that justifies this persona existing
    matched_pair_id: str | None = None      # id of the other persona in this persona's
                                             # matched pair, if it's one of the deliberate 2 of 8


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
FindingTag = Literal["corroborated", "agent_readiness"]


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
    # DRAFT (dev-c/research-schema-draft), defaults keep every existing Finding valid:
    tag: FindingTag = "agent_readiness"     # "corroborated" iff the persona that hit this
                                             # was itself built from a real customer complaint
    segment: str | None = None              # persona's customer segment, for "who it affects"
    evidence_quote: str | None = None       # shown beside the replay when tag=="corroborated"
    evidence_url: str | None = None


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
