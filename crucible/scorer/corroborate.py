"""DRAFT (dev-c/research-schema-draft): tags a stalled RunResult's Finding as "corroborated"
or "agent_readiness", per docs/ui-flow.md Screen 5.

Matching is exact on (journey_id, config) -> Persona, not semantic: a persona's own evidence
quote is what justified generating it in Consumer research in the first place, so if a
persona's session stalls, the failure it hit is, by construction, backed by that persona's
quote. No fuzzy/LLM matching needed -- mirrors the "matching is exact ... not semantic"
decision from the earlier (v2) design doc.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..schemas import Persona, RunResult


@dataclass(frozen=True)
class Corroboration:
    tag: str  # "corroborated" | "agent_readiness"
    segment: str | None
    evidence_quote: str | None
    evidence_url: str | None


NOT_CORROBORATED = Corroboration(tag="agent_readiness", segment=None, evidence_quote=None, evidence_url=None)


def persona_for(result: RunResult, personas: list[Persona]) -> Persona | None:
    return next((p for p in personas if p.journey_id == result.journey_id and p.config == result.config), None)


def corroborate(result: RunResult, personas: list[Persona] | None) -> Corroboration:
    if not personas:
        return NOT_CORROBORATED
    persona = persona_for(result, personas)
    if persona is None:
        return NOT_CORROBORATED
    if persona.evidence is not None:
        return Corroboration(
            tag="corroborated", segment=persona.segment,
            evidence_quote=persona.evidence.quote, evidence_url=persona.evidence.url,
        )
    return Corroboration(tag="agent_readiness", segment=persona.segment, evidence_quote=None, evidence_url=None)
