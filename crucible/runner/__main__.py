"""Run the population matrix from the command line.

  python -m crucible.runner --url https://shop.test --journey "Add any product to the cart and open the cart" \
      --configs mvp --out runs/results.jsonl
  python -m crucible.runner --site-json targets/cache/shop.json --configs should
  python -m crucible.runner --url https://x --journey "..." --fake     # no Steel, no model
  python -m crucible.runner --url https://x --journey "..." --configs baseline --step-cap 10   # M1
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from ..schemas import Config, Journey, RunResult, SiteModel
from . import run_matrix
from .matrix import BASELINE, MVP_CONFIGS, SHOULD_CONFIGS, STRETCH_CONFIGS

CONFIG_SETS = {"baseline": [BASELINE], "mvp": MVP_CONFIGS, "should": SHOULD_CONFIGS, "stretch": STRETCH_CONFIGS}


def _site_from_args(a) -> SiteModel:
    if a.site_json:
        return SiteModel.model_validate_json(Path(a.site_json).read_text())
    if not (a.url and a.journey):
        raise SystemExit("need --site-json, or --url and at least one --journey")
    journeys = [Journey(id=f"j{i+1}", name=g[:40], goal=g, entry_url=a.url) for i, g in enumerate(a.journey)]
    return SiteModel(url=a.url, journeys=journeys)


def _configs(a) -> list[Config]:
    cfgs = list(CONFIG_SETS[a.configs])
    if a.engine:                      # run the whole set on another engine (e.g. a claude_cu smoke test)
        cfgs = [c.model_copy(update={"engine": a.engine}) for c in cfgs if c.engine == "browser_use"]
    if a.only:
        keep = set(a.only.split(","))
        cfgs = [c for c in cfgs if c.label in keep or c.label == "baseline"]
    return cfgs


async def _main(a) -> int:
    site = _site_from_args(a)
    configs = _configs(a)
    kw: dict = dict(max_concurrency=a.max_concurrency, run_budget_s=a.run_budget, max_retries=a.retries)
    if a.step_cap:
        kw["step_caps"] = {e: a.step_cap for e in ("browser_use", "claude_cu", "openai_cu")}
    if a.fake:
        from ..engines.fake import FakeEngine
        from ..testing import FakeSessionFactory, profile_ready
        engines = {e: FakeEngine(name=e) for e in ("browser_use", "claude_cu", "openai_cu")}
        kw.update(session_factory=FakeSessionFactory(), profile_waiter=profile_ready)
    else:
        from ..engines import default_engines
        engines = default_engines()

    out = open(a.out, "a") if a.out else None
    summary: list[RunResult] = []
    try:
        async for item in run_matrix(site, configs, engines, **kw):
            line = item.model_dump_json()
            if out:
                out.write(line + "\n"); out.flush()
            if item.type == "session_started":
                print(f"▶ {item.run_id:40s} session={item.session_id} viewer={item.viewer_url}")
            elif item.type == "run_event":
                flag = "" if item.outcome == "step_ok" else f"  [{item.outcome}]"
                print(f"  {item.run_id:40s} #{item.step_index:<3d} {item.action[:70]}{flag}")
            elif item.type == "run_result":
                summary.append(item)
                extra = f" ({item.harness_reason})" if item.harness_reason else (f" ({item.stall_hint})" if item.stall_hint else "")
                print(f"■ {item.run_id:40s} {item.outcome.upper()}{extra} attempt={item.attempt} "
                      f"steps={len(item.events)} replay={item.replay_url} @{item.replay_offset_s}")
    finally:
        if out:
            out.close()
    print("\nSummary:")
    for r in summary:
        print(f"  {r.journey_id:18s} {r.config.label:18s} {r.outcome}")
    return 0 if summary else 1


def cli() -> int:
    load_dotenv()
    ap = argparse.ArgumentParser(prog="python -m crucible.runner", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site-json")
    ap.add_argument("--url")
    ap.add_argument("--journey", action="append", help="journey goal (repeatable)")
    ap.add_argument("--configs", choices=CONFIG_SETS, default="baseline")
    ap.add_argument("--only", help="comma-separated config labels to keep (baseline always kept)")
    ap.add_argument("--engine", choices=["browser_use", "claude_cu", "openai_cu"], help="override the engine for every config")
    ap.add_argument("--step-cap", type=int)
    ap.add_argument("--max-concurrency", type=int, default=8)
    ap.add_argument("--run-budget", type=float, default=600.0)
    ap.add_argument("--retries", type=int, default=1)
    ap.add_argument("--out", help="append every pipeline event as JSONL")
    ap.add_argument("--fake", action="store_true", help="fake engines + fake sessions (no credits)")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return asyncio.run(_main(a))


if __name__ == "__main__":
    sys.exit(cli())
