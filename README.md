# Crucible

Lighthouse for AI agents, measured with real agents on Steel. Docs: `docs/concept.md` (pitch),
`docs/superpowers/specs/2026-09-12-crucible-design.md` (design), `docs/plan.md` (team plan),
`docs/dev-a-plan.md` (Steel core plan).

## Setup

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m playwright install chromium     # only for local, credit-free work
cp .env.example .env                                 # STEEL_API_KEY, ANTHROPIC_API_KEY
```

## Layout

```
crucible/schemas.py      shared contracts (all devs)      fixtures/        example JSON for every schema + demo_run.json
crucible/steel.py        Steel session lifecycle (A)      tests/           pytest, no credits needed
crucible/engines/        browser_use, claude_cu (A)       scripts/         spikes + fixture generator
crucible/runner/         matrix, scheduler, CLI (A)
crucible/testing.py      fakes for tests / dry runs
```

## Run

```bash
.venv/bin/python -m pytest -q                                   # 41 tests, ~1s
.venv/bin/python scripts/make_fixtures.py                       # regenerate fixtures/
.venv/bin/python -m crucible.runner --url https://x --journey "Add a product to the cart" --fake --configs mvp
.venv/bin/python -m crucible.runner --url https://x --journey "..." --configs baseline --step-cap 12   # M1, live
.venv/bin/python -m crucible.runner --site-json targets/cache/shop.json --configs mvp --out runs/events.jsonl
.venv/bin/python -m crucible.steel --list            # live sessions
.venv/bin/python -m crucible.steel --release-all     # panic button
```

## Contracts (M0)

- `Engine.run_journey(session, journey, cfg, step_cap, ctx) -> AsyncIterator[RunEvent]` — `crucible/engines/base.py`
- `run_matrix(site, configs, engines) -> AsyncIterator[RunEvent | SessionStarted | RunResult]` — `crucible/runner/__init__.py`
- `score(site, results) -> (ScoreCard, list[Finding])` — Dev C, `crucible/scorer/__init__.py`
- `explore(url, hint=None) -> SiteModel` — Dev B, `crucible/explore/__init__.py`
- Pipeline events carry a `type` field: `session_started`, `run_event`, `run_result`, `stage`.
