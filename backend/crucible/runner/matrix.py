"""Population matrix: journeys × configs -> RunSpecs, baseline first."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..schemas import Config, Journey, SiteModel

BASELINE = Config(device="desktop", identity="fresh", country="US", engine="browser_use", label="baseline")

MVP_CONFIGS: list[Config] = [
    BASELINE,
    Config(device="mobile", identity="fresh", country="US", engine="browser_use", label="mobile"),
    Config(device="desktop", identity="returning", country="US", engine="browser_use", label="returning"),
    Config(device="desktop", identity="fresh", country="CA", engine="browser_use", label="country:CA"),
]
SHOULD_CONFIGS: list[Config] = MVP_CONFIGS + [
    Config(device="desktop", identity="fresh", country="DE", engine="browser_use", label="country:DE"),
    Config(device="desktop", identity="fresh", country="US", engine="claude_cu", label="engine:claude_cu"),
]
STRETCH_CONFIGS: list[Config] = SHOULD_CONFIGS + [
    Config(device="desktop", identity="fresh", country="US", engine="openai_cu", label="engine:openai_cu"),
]


@dataclass
class RunSpec:
    run_id: str
    journey: Journey
    cfg: Config
    persist_profile: bool = False
    needs_profile_from: str | None = None    # run_id of the baseline whose profile we reuse
    step_cap: int | None = None              # None -> engine default
    tags: dict[str, str] = field(default_factory=dict)

    @property
    def is_baseline(self) -> bool:
        return self.cfg.diff_from(BASELINE) == [] or self.cfg.label == "baseline"


def find_baseline(configs: list[Config]) -> Config:
    for c in configs:
        if c.label == "baseline":
            return c
    return BASELINE


def build_matrix(site: SiteModel, configs: list[Config], *, baseline: Config | None = None,
                 step_caps: dict[str, int] | None = None) -> list[RunSpec]:
    """One RunSpec per journey × config. The baseline for each journey always runs and comes first.

    Every non-baseline config must differ from the baseline in exactly one variable so that
    attribution is well-defined; `ValueError` otherwise.
    """
    base = baseline or find_baseline(configs)
    step_caps = step_caps or {}
    variants: list[Config] = []
    for c in configs:
        if c == base:
            continue
        diff = c.diff_from(base)
        if len(diff) != 1:
            raise ValueError(f"config {c.label!r} differs from baseline in {diff}; must be exactly one variable")
        variants.append(c)
    has_returning = any(c.identity == "returning" for c in variants)

    specs: list[RunSpec] = []
    for j in site.journeys:
        base_id = f"{j.id}__{base.label}"
        specs.append(RunSpec(run_id=base_id, journey=j, cfg=base, persist_profile=has_returning,
                             step_cap=step_caps.get(base.engine)))
    for j in site.journeys:
        base_id = f"{j.id}__{base.label}"
        for c in variants:
            specs.append(RunSpec(
                run_id=f"{j.id}__{c.label}", journey=j, cfg=c,
                needs_profile_from=base_id if c.identity == "returning" else None,
                step_cap=step_caps.get(c.engine),
            ))
    return specs
