# Crucible

Lighthouse for AI agents, measured with real agents on Steel. Docs: `docs/concept.md` (pitch),
`docs/superpowers/specs/2026-09-12-crucible-design.md` (design), `docs/plan.md` (team plan),
`docs/dev-a-plan.md` (Steel core plan).

## Repo layout

```
backend/   Python: schemas, Steel core, engines, Runner, Scorer, fixtures, tests   (Devs A, B, C)
web/       Vite + React + Tailwind front end                                        (Dev D)
docs/      concept, design, plan, API contract, UI flow
design/    design exports
```

All Python commands below run **from `backend/`**.

## Setup

```bash
cd backend
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m playwright install chromium     # only for local, credit-free work
cp .env.example .env                                 # STEEL_API_KEY, ANTHROPIC_API_KEY
```

Python 3.12 is required. `crucible/schemas.py` uses `list[str]` / `X | None` annotations, so an older
interpreter (e.g. a conda 3.8 on your PATH) fails at import with a pydantic `TypeError`. Always run
through `.venv/bin/python`, never bare `python`.

### Keys: who needs what

| Key | Used by | Needed for |
|---|---|---|
| `STEEL_API_KEY` | `crucible/steel.py` | Any live session: Runner without `--fake`, spikes, Explore on a real site |
| `ANTHROPIC_API_KEY` | Browser Use engine (`ChatAnthropic`), Claude CU engine, Scorer LLM classifier, Explore summariser | Any live run, plus the LLM pass in `score()` and `explore()` |
| `OPENAI_API_KEY` | `engines/openai_cu.py` (stretch only) | Only if the third engine is built |

Tests, fixtures, the API stub, and the React views need **no keys**. Dev C and Dev D can work all day
on `fixtures/` without a Steel or Anthropic account.

## Backend layout (`backend/`)

```
crucible/schemas.py      shared contracts (all devs)      fixtures/        example JSON for every schema + demo_run.json
crucible/steel.py        Steel session lifecycle (A)      tests/           pytest, no credits needed
crucible/engines/        browser_use, claude_cu (A)       scripts/         spikes + fixture generator
crucible/runner/         matrix, scheduler, CLI (A)
crucible/scorer/         classify, attribute, score (C)
crucible/testing.py      fakes for tests / dry runs
```

## Run (from `backend/`)

```bash
.venv/bin/python -m pytest -q                                   # 102 tests, ~1s
.venv/bin/python scripts/make_fixtures.py                       # regenerate fixtures/
.venv/bin/python -m crucible.runner --url https://x --journey "Add a product to the cart" --fake --configs mvp
.venv/bin/python -m crucible.runner --url https://x --journey "..." --configs baseline --step-cap 12   # M1, live
.venv/bin/python -m crucible.runner --url https://x --journey "..." --configs baseline --engine claude_cu    # vision engine
.venv/bin/python -m crucible.runner --site-json targets/cache/shop.json --configs mvp --out runs/events.jsonl
.venv/bin/python -m crucible.steel --list            # live sessions
.venv/bin/python -m crucible.steel --release-all     # panic button
```

## Getting started (Dev B / C / D)

The M0 contracts are on `main`: `crucible/schemas.py` and every example in `fixtures/`. Nothing before
hour 7 in `docs/plan.md` is a hard block on Dev A, so start from the fixtures, not from live runs.

1. `git pull origin main`, then the Setup block above.
2. `.venv/bin/python -m pytest -q` must pass before you touch anything.
3. Build against the fixtures:
   - **Dev B** — `api/` stub serves `fixtures/demo_run.json`; the websocket replays its `events`
     list with small delays. `explore/` returns a `SiteModel` shaped like `fixtures/site_model.json`.
   - **Dev C** — `scorer/` takes `fixtures/run_result_*.json` in and produces `Finding`s shaped like
     `fixtures/finding.json` and a `ScoreCard` shaped like `fixtures/scorecard.json`. Put tests in
     `tests/scorer/`.
   - **Dev D** — read `fixtures/demo_run.json` (`site_model`, `events`, `findings`, `scorecard`)
     until B's API stub is up, then point at the stub.
4. Every fixture validates against its schema class; `fixtures/config.json` is a **list** of configs.
   If you change `schemas.py`, regenerate with `scripts/make_fixtures.py` and tell the whole team;
   schema changes need everyone in the room.
5. Live runs, Steel credits, and the call to fall back to cached mode belong to Dev A. Do not run the
   Runner without `--fake` unless A has handed you a session budget.

## Contracts (M0)

- `Engine.run_journey(session, journey, cfg, step_cap, ctx) -> AsyncIterator[RunEvent]` — `crucible/engines/base.py`
- `run_matrix(site, configs, engines) -> AsyncIterator[RunEvent | SessionStarted | RunResult]` — `crucible/runner/__init__.py`
- `score(site, results) -> (ScoreCard, list[Finding])` — Dev C, `crucible/scorer/__init__.py`
- `explore(url, hint=None) -> SiteModel` — Dev B, `crucible/explore/__init__.py`
- Pipeline events carry a `type` field: `session_started`, `run_event`, `run_result`, `stage`.
