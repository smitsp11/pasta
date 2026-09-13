"""attributed_to + engine_consensus for every stalled RunResult in a batch.

Two attribution modes, chosen by whether `personas` is passed:

1. Baseline mode (personas=None, the original v3 population): a stall only in a variant (not
   in the baseline) is pinned to the one axis that variant differs on (device/identity/country/
   engine). A stall present in the baseline too, or a config that can't be cleanly diffed
   against a baseline (missing baseline, or differs in more than one axis), is attributed to
   "site" -- the conservative choice when a single variable can't be isolated.

2. DRAFT persona mode (dev-c/research-schema-draft, personas given, per docs/ui-flow.md): there
   is no single shared baseline across all 8 personas -- only the deliberate "matched pair" (2
   of 8) is guaranteed to differ in exactly one variable. A stalled persona with no matched
   partner, or whose partner isn't a clean single-variable diff, is attributed to "site" (same
   conservative default as mode 1, just far more common here since 6 of 8 personas have no
   comparator at all).

Engine consensus is identical in both modes and does not depend on which one ran: for the
group of RunResults sharing (journey_id, device, identity, country) -- i.e. differing only in
engine -- if every distinct engine present in that group stalled with the SAME category, every
stalled result in the group is flagged engine_consensus=True. A harness_error or a completed
result for any engine in the group breaks consensus: we don't have independent evidence from
that engine either way.
"""
from __future__ import annotations

from collections import defaultdict

from ..schemas import AttributedTo, FailureCategory, Persona, RunResult
from .baseline import is_baseline


def _attribute_one_vs_baseline(r: RunResult, baseline: RunResult | None, baseline_stalled: bool) -> AttributedTo:
    if baseline is None:
        return "site"  # can't isolate a variable without a baseline reference
    if r.run_id == baseline.run_id:
        return "site"  # the baseline itself stalls: fails for everyone
    diff = r.config.diff_from(baseline.config)
    if len(diff) != 1:
        return "site"  # not a clean single-variable variant; conservative
    if baseline_stalled:
        return "site"  # same failure present in the control condition too
    return diff[0]  # "device" | "identity" | "country" | "engine"


def _attribute_stalls_by_baseline(results: list[RunResult]) -> dict[str, AttributedTo]:
    out: dict[str, AttributedTo] = {}
    by_journey: dict[str, list[RunResult]] = defaultdict(list)
    for r in results:
        by_journey[r.journey_id].append(r)
    for group in by_journey.values():
        baseline = next((r for r in group if is_baseline(r.config)), None)
        baseline_stalled = baseline is not None and baseline.outcome == "stalled"
        for r in group:
            if r.outcome == "stalled":
                out[r.run_id] = _attribute_one_vs_baseline(r, baseline, baseline_stalled)
    return out


def _attribute_stalls_by_matched_pair(results: list[RunResult], personas: list[Persona]) -> dict[str, AttributedTo]:
    out: dict[str, AttributedTo] = {}
    persona_by_key = {(p.journey_id, p.config): p for p in personas}
    persona_by_id = {p.id: p for p in personas}

    for r in results:
        if r.outcome != "stalled":
            continue
        persona = persona_by_key.get((r.journey_id, r.config))
        partner_persona = persona_by_id.get(persona.matched_pair_id) if persona and persona.matched_pair_id else None
        if partner_persona is None:
            out[r.run_id] = "site"  # not part of a matched pair: no clean comparator
            continue
        partner_result = next(
            (x for x in results if x.journey_id == r.journey_id and x.config == partner_persona.config), None
        )
        if partner_result is None:
            out[r.run_id] = "site"  # the pair's partner never ran
            continue
        diff = r.config.diff_from(partner_result.config)
        if len(diff) != 1:
            out[r.run_id] = "site"  # not a clean single-variable pair; conservative
        elif partner_result.outcome == "stalled":
            out[r.run_id] = "site"  # both halves of the pair fail: not attributable to the axis
        else:
            out[r.run_id] = diff[0]
    return out


def _apply_engine_consensus(
    attributed: dict[str, AttributedTo], results: list[RunResult], categories: dict[str, FailureCategory]
) -> dict[str, tuple[AttributedTo, bool]]:
    out: dict[str, tuple[AttributedTo, bool]] = {run_id: (a, False) for run_id, a in attributed.items()}
    by_journey: dict[str, list[RunResult]] = defaultdict(list)
    for r in results:
        by_journey[r.journey_id].append(r)

    for group in by_journey.values():
        by_axes: dict[tuple, list[RunResult]] = defaultdict(list)
        for r in group:
            by_axes[(r.config.device, r.config.identity, r.config.country)].append(r)
        for subgroup in by_axes.values():
            engines = {r.config.engine for r in subgroup}
            if len(engines) < 2:
                continue
            per_engine_category: dict[str, FailureCategory] = {}
            consensus = True
            for eng in engines:
                eng_results = [r for r in subgroup if r.config.engine == eng]
                if not all(r.outcome == "stalled" for r in eng_results):
                    consensus = False
                    break
                cats = {categories[r.run_id] for r in eng_results if r.run_id in categories}
                if len(cats) != 1:
                    consensus = False
                    break
                per_engine_category[eng] = next(iter(cats))
            if consensus and len(set(per_engine_category.values())) == 1:
                for r in subgroup:
                    if r.run_id in out:
                        attributed_to, _ = out[r.run_id]
                        out[r.run_id] = (attributed_to, True)
    return out


def attribute(
    results: list[RunResult], categories: dict[str, FailureCategory], *, personas: list[Persona] | None = None
) -> dict[str, tuple[AttributedTo, bool]]:
    attributed = (
        _attribute_stalls_by_matched_pair(results, personas) if personas else _attribute_stalls_by_baseline(results)
    )
    return _apply_engine_consensus(attributed, results, categories)
