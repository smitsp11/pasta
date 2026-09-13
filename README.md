# Iris

**Send your customers in first.**

Point Iris at a company's URL with zero context. It researches who that company's real customers are, maps
what the live site lets them do, builds eight evidence-backed AI personas, and sends them through the site at
once on real cloud browsers: on mobile, as returning visitors, from other countries, with different kinds of
agent. You get a readiness score and a ranked list of flags, each with the customer quote that predicted it,
the replay frozen on the frame where the agent gave up, and a concrete fix.

Built for the Battle of the Schools hackathon, **Steel.dev Web Agents track**. Live: https://iris-tau-two.vercel.app

## Why

Companies pay for case studies and user research to learn how customers behave on their site. Agent-readiness
checkers (Cloudflare, Apify) only inspect static signals like `robots.txt` and never run anything. Single-agent
auditors send one generic agent to the homepage with fixed tasks. Iris learns who the customers are, then
**measures** the site with a controlled population of real agents.

## How it works

1. **Input.** One field: the URL.
2. **Learning.** Two agents run in parallel. Consumer research opens review sites, Reddit, help centres and a
   competitor in Steel sessions and collects real quotes. Site analysis is a read-only crawler that maps the
   site into a few executable journeys.
3. **Test brief.** One Claude call turns evidence and site map into 8 personas (segment, device, country,
   identity, goal, supporting quote). Two personas differ in exactly one variable so at least one finding is
   provably attributable.
4. **Swarm.** Eight Steel sessions at once, each with its own mobile fingerprint, residential geo proxy and
   persistent profile. A DOM agent (Browser Use) or a vision agent (Claude computer use) runs the goal and
   narrates every step. Agents never submit payment.
5. **Report.** Every stall is classified into a fixed failure taxonomy, attributed to a single variable, matched
   to the quote that predicted it, and given a proposed fix. Ranked by customers affected.

A flag is only reported if an agent actually reproduced it. Tooling failures are bucketed as harness errors
and excluded from the score.

## Key features

- **Controlled experiment.** Every run config differs from the baseline in exactly one variable, enforced when
  the matrix is built. Stalls become "fails only on mobile" or "fails for every engine, so it is the site".
- **Steel primitives as product features.** Mobile mode, residential geo proxies, persistent profiles, live
  viewer embeds in the swarm grid, and session replay seeked to the stall frame in the report.
- **Two engines, one interface.** Browser Use and Claude computer use emit the same event stream, so the
  Runner is engine-agnostic and a stall that hits every engine is flagged as engine consensus.
- **Deterministic-first scoring.** Cookie walls, CAPTCHAs, geo-blocks, login walls and timeouts are detected
  from the page; one Claude call handles the rest. The scorer runs on fixtures with no keys.
- **Front end that plays without a backend.** A pure reducer folds a typed event stream into state. Today a
  player replays a per-target script (IKEA Canada, Zara, or a fictional store); a websocket can replace it
  without touching a screen. This is also the stage fallback.

## Repo layout

```
backend/crucible/schemas.py   shared contracts: SiteModel, Config, RunEvent, RunResult, Finding, ScoreCard
backend/crucible/steel.py     Steel session lifecycle, credits log, --list / --release-all
backend/crucible/engines/     browser_use, claude_cu, fake, payment guard
backend/crucible/runner/      journeys × configs matrix, wave scheduler, profile warm-up, retries, CLI
backend/crucible/scorer/      classify, attribute, score, fixes
backend/fixtures/, tests/     example JSON for every schema; pytest with no keys or credits
web/                          Vite + React + Tailwind: Input, Learning, Brief, Swarm, Report
docs/                         ui-flow, design-brief, api (stream contract), plan, concept
```

## Setup

Requires Node 20+, Python 3.12, and [`uv`](https://docs.astral.sh/uv/).

**Backend**

```bash
cd backend
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"
cp .env.example .env                  # STEEL_API_KEY, ANTHROPIC_API_KEY
.venv/bin/python -m pytest -q         # no keys needed
```

Always run through `.venv/bin/python`. The schemas use 3.12 syntax and fail to import on older interpreters.

**Front end**

```bash
cd web
npm install
npm run dev          # http://localhost:5173
npm test             # vitest
npm run e2e          # playwright: plays the show, screenshots each stage
```

Type an IKEA or Zara URL on the input screen to load that demo target; anything else plays the fictional
store. `?target=ikea`, `?speed=6`, and `?stage=run` are available for rehearsal.

**Keys**

| Key | Needed for |
|---|---|
| `STEEL_API_KEY` | Any live session |
| `ANTHROPIC_API_KEY` | Both agent engines, the scorer classifier, Explore, brief generation |
| `OPENAI_API_KEY` | Only for the stretch OpenAI computer-use engine |

Tests, fixtures and the front end need no keys. Residential proxies need a paid Steel balance.

## Run the backend

From `backend/`:

```bash
# no credits: fake engine, full matrix
.venv/bin/python -m crucible.runner --url https://x --journey "Add a product to the cart" --fake --configs mvp

# live: one Steel session, DOM agent
.venv/bin/python -m crucible.runner --url https://x --journey "..." --configs baseline --step-cap 12

# live: vision agent
.venv/bin/python -m crucible.runner --url https://x --journey "..." --configs baseline --engine claude_cu

# session housekeeping
.venv/bin/python -m crucible.steel --list
.venv/bin/python -m crucible.steel --release-all
```

Ctrl-C releases every session before exiting. Real sessions append to `runs/credits.log`.

## Docs

`docs/ui-flow.md` (what each screen does and why) · `docs/design-brief.md` (look and motion) ·
`docs/api.md` (stream contract) · `docs/plan.md` (team plan) · `docs/concept.md` (pitch and prior art)
