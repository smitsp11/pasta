# Iris

**Send your customers in first.**

Point Iris at a company's URL with zero context. It researches who that company's real customers are, maps
what the live site lets them do, builds eight evidence-backed AI personas, and sends them through the site at
once on real cloud browsers: on mobile, as returning visitors, from other countries, with different kinds of
agent. You get a readiness score and a ranked list of flags, each with the customer quote that predicted it,
the replay frozen on the frame where the agent gave up, and a concrete fix.

Built for the Battle of the Schools hackathon, **Steel.dev Web Agents track**. Live: https://iris-tau-two.vercel.app

## Why

**Agents are already the customer.** AI-referred traffic to US retail sites grew [393% year over year in Q1 2026](https://finance.yahoo.com/sectors/technology/articles/ai-traffic-us-retailers-jumps-160141756.html)
and is up [more than 14× since October 2024](https://www.digitalcommerce360.com/2026/06/17/adobe-ai-referred-traffic-to-retail-sites-doubles-in-a-year/).
Those visitors now convert 54% better than non-AI traffic, a reversal from a year earlier when they converted
at half the rate (Adobe Analytics). McKinsey forecasts [$3 to 5 trillion in agentic commerce by 2030](https://www.digitalcommerce360.com/2025/10/20/mckinsey-forecast-5-trillion-agentic-commerce-sales-2030/).
Yet Adobe finds 30 to 40% of content on retailers' highest-value pages is still invisible to AI, and no tool
tells a site owner whether an agent can actually reach checkout.

**The alternative is slow and expensive.** A moderated usability study with 5 to 10 users [starts at $40,000 at
Nielsen Norman Group](https://www.nngroup.com/consulting/user-testing/), and $80,000 to $150,000 with multiple
audiences or designs. Recruiting alone runs [about $171 per participant](https://www.nngroup.com/articles/recruiting-test-participants-for-usability-studies/),
and a typical study takes [2 to 6 weeks end to end](https://cleverx.com/guides/how-long-does-user-research-take-timelines-by-method-and-industry/).
Static agent-readiness checkers (Cloudflare, Apify) are free but never run anything. Single-agent auditors send
one generic agent to the homepage with fixed tasks.

**What Iris saves.** One run replaces the study: research, 8 personas across devices, countries and identities,
and a ranked fix list, in minutes instead of weeks, for the price of eight cloud browser sessions and a few
dozen model calls. Cheap enough to run on every deploy rather than once a quarter. And it measures the thing
that matters: cart abandonment already [averages 70% and is worse on mobile](https://baymard.com/lists/cart-abandonment-rate);
an agent that stalls on a cookie wall or an unlabelled cart button is the same failure, now at machine scale.

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
