"""Per-journey weighted completion rate. Harness errors excluded from the score and reported
separately (JourneyScore.harness_errors), per the design doc.

score = 100 * sum(weight_i for i in scored if completed) / max(sum(weight_i for i in scored), 1)
  scored = [r for r in journey_results if r.outcome != "harness_error"]
  weight_i = 2 if is_baseline(r.config) else 1
overall = mean(per_journey scores), rounded to 1 decimal
"""
from __future__ import annotations

from ..schemas import Config, Journey, JourneyScore, RunResult, ScoreCard, SiteModel
from .baseline import is_baseline


def weight_for(cfg: Config) -> int:
    return 2 if is_baseline(cfg) else 1


def journey_score(journey: Journey, results: list[RunResult]) -> JourneyScore:
    rs = [r for r in results if r.journey_id == journey.id]
    scored = [r for r in rs if r.outcome != "harness_error"]
    weights = [weight_for(r.config) for r in scored]
    completed_weight = sum(w for r, w in zip(scored, weights) if r.outcome == "completed")
    score = round(100 * completed_weight / max(sum(weights), 1), 1)
    # score == 0.0 covers two situations the schema can't otherwise distinguish: (a) everything
    # scored failed, or (b) there was nothing to score (rs empty, or every result was a
    # harness_error). Callers tell them apart via the raw counts below.
    return JourneyScore(
        journey_id=journey.id,
        score=score,
        completed=sum(1 for r in rs if r.outcome == "completed"),
        stalled=sum(1 for r in rs if r.outcome == "stalled"),
        harness_errors=sum(1 for r in rs if r.outcome == "harness_error"),
    )


def score_card(site: SiteModel, results: list[RunResult], *, static_score: float | None) -> ScoreCard:
    per_journey = [journey_score(j, results) for j in site.journeys]
    overall = round(sum(p.score for p in per_journey) / len(per_journey), 1) if per_journey else 0.0
    return ScoreCard(overall=overall, static_score=static_score, per_journey=per_journey)
