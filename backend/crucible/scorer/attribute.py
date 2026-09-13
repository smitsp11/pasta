"""attributed_to + engine_consensus for every stalled RunResult in a batch.

Attribution: a stall only in a variant (not in the baseline) is pinned to the one axis that
variant differs on (device/identity/country/engine). A stall present in the baseline too, or a
config that can't be cleanly diffed against a baseline (missing baseline, or differs in more
than one axis), is attributed to "site" -- the conservative choice when a single variable can't
be isolated.

Engine consensus: for the group of RunResults sharing (journey_id, device, identity, country)
-- i.e. differing only in engine -- if every distinct engine present in that group stalled with
the SAME category, every stalled result in the group is flagged engine_consensus=True. A
harness_error or a completed result for any engine in the group breaks consensus: we don't have
independent evidence from that engine either way.
"""
from __future__ import annotations

from collections import defaultdict

from ..schemas import AttributedTo, FailureCategory, RunResult
from .baseline import is_baseline


def _attribute_one(r: RunResult, baseline: RunResult | None, baseline_stalled: bool) -> AttributedTo:
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


def attribute(results: list[RunResult], categories: dict[str, FailureCategory]) -> dict[str, tuple[AttributedTo, bool]]:
    out: dict[str, tuple[AttributedTo, bool]] = {}
    by_journey: dict[str, list[RunResult]] = defaultdict(list)
    for r in results:
        by_journey[r.journey_id].append(r)

    for group in by_journey.values():
        baseline = next((r for r in group if is_baseline(r.config)), None)
        baseline_stalled = baseline is not None and baseline.outcome == "stalled"
        for r in group:
            if r.outcome == "stalled":
                out[r.run_id] = (_attribute_one(r, baseline, baseline_stalled), False)

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
