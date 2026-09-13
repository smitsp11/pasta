"""score(): classify -> attribute -> fixes -> per-journey/overall score + static contrast,
assembled into (ScoreCard, list[Finding]).

Only "stalled" RunResults become Findings; "completed" needs none, and "harness_error" is
tooling noise, not a site-fault category (no FailureCategory exists for it) -- it's counted in
JourneyScore.harness_errors and never turned into a Finding. Findings are generated for every
stalled result regardless of whether its journey_id matches a SiteModel journey (the stall is
still a fact); only score_card()'s per-journey aggregation is scoped to site.journeys, matching
the reference formula in scripts/make_fixtures.py.

Isolation: a bad classification, a bad fix-text generation, or a broken static fetch must never
crash the whole call -- each is wrapped so one failure degrades just that piece ("other"
category / empty fix text / static_score=None) instead of aborting the batch.

DRAFT (dev-c/research-schema-draft): an optional `personas` argument threads through to
attribute() (matched-pair attribution instead of the single-baseline matrix) and corroborate()
(tags a Finding "corroborated" when the persona that hit it was built from a real customer
complaint, per docs/ui-flow.md). Omitting it reproduces the original v3 behavior exactly.
"""
from __future__ import annotations

import asyncio
import logging

from ..schemas import Finding, Persona, RunResult, ScoreCard, SiteModel
from .attribute import attribute
from .classify import Classifier, classify
from .corroborate import NOT_CORROBORATED, corroborate
from .fixes import proposed_fix
from .score import score_card
from .static import fetch_static_score

log = logging.getLogger("crucible.scorer")


async def score(
    site: SiteModel,
    results: list[RunResult],
    *,
    classifier: Classifier | None = None,
    personas: list[Persona] | None = None,
) -> tuple[ScoreCard, list[Finding]]:
    stalled = [r for r in results if r.outcome == "stalled"]

    raw = await asyncio.gather(*(classify(r, llm=classifier) for r in stalled), return_exceptions=True)
    categories: dict[str, str] = {}
    descriptions: dict[str, str] = {}
    for r, res in zip(stalled, raw):
        if isinstance(res, BaseException):
            log.warning("classify raised for %s: %s", r.run_id, res)
            res = ("other", "Automatic classification failed; needs manual review.")
        categories[r.run_id], descriptions[r.run_id] = res

    attribution = attribute(results, categories, personas=personas)  # run_id -> (attributed_to, engine_consensus)

    findings: list[Finding] = []
    for i, r in enumerate(stalled):
        attributed_to, consensus = attribution.get(r.run_id, ("site", False))
        try:
            fix_text = proposed_fix(categories[r.run_id], r)
        except Exception as e:  # noqa: BLE001 - a bad fix template must not drop the finding
            log.warning("proposed_fix failed for %s: %s", r.run_id, e)
            fix_text = ""
        try:
            corrob = corroborate(r, personas)
        except Exception as e:  # noqa: BLE001 - a corroboration bug must not drop the finding
            log.warning("corroborate failed for %s: %s", r.run_id, e)
            corrob = NOT_CORROBORATED
        findings.append(
            Finding(
                id=f"f{i + 1}",
                journey_id=r.journey_id,
                config=r.config,
                category=categories[r.run_id],
                description=descriptions[r.run_id],
                attributed_to=attributed_to,
                engine_consensus=consensus,
                session_id=r.session_id,
                step_index=r.failure_step_index,
                replay_url=r.replay_url,
                replay_offset_s=r.replay_offset_s,
                proposed_fix=fix_text,
                tag=corrob.tag,
                segment=corrob.segment,
                evidence_quote=corrob.evidence_quote,
                evidence_url=corrob.evidence_url,
            )
        )

    try:
        static_score = await fetch_static_score(site.url)
    except Exception as e:  # noqa: BLE001 - contrast panel just hides itself per the design doc
        log.info("static score unavailable for %s: %s", site.url, e)
        static_score = None

    return score_card(site, results, static_score=static_score), findings
