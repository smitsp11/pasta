# Crucible — Design (v3)

Hackathon: Battle of the Schools — **Steel.dev Web Agents track** (Sept 12–13 2026). Goal: 1st place (+ the $500 Steel Computer bonus if the beta is usable). Team of 4, parallel work. Stack: **Python**.

**One-liner: Lighthouse for AI agents, measured with real agents instead of static checks.** Give Crucible a URL with zero context. It works out what the site is and discovers its key user journeys, then runs a controlled population of real agents through those journeys on real cloud browsers: on mobile, as a returning visitor, from other countries, and with different kinds of agent. It hands back a readiness score, the exact moment each agent got stuck, what that stall is attributable to, and a proposed fix.

Headline demo moment: *"Cloudflare says this site is 85/100 agent-ready. An actual agent can't get past the cookie banner on mobile. Here's the frame."*

See `docs/concept.md` for the pitch, prior art, and vocabulary.

---

## Why this version

**The world it lives in.** People are starting to delegate real work to web agents: shopping, booking, form-filling, account admin. The question a site owner now has to answer is not "what would a customer do" but "does my site survive the population of agents that actually exist." That population is real and measurable, so every finding is a fact, not a prediction.

**What exists today, and the gap:**
- **Cloudflare's Agent Readiness score** (April 2026) and **Apify's readiness audit** are static: robots.txt, llms.txt, headers, structured data, MCP cards. Neither ever runs an agent through a task.
- **Agent Checker** runs one agent, one way, through a fixed task list and returns a PDF with replay. No mobile, no geo, no returning identity, no second kind of agent, no attribution, no fix.
- **Steel** rates *agents* on sites (AgentBench leaderboard). Nobody rates *sites* for agents on Steel's infrastructure.

Crucible is the missing half of Steel's own leaderboard, built on the primitives only Steel provides.

**Rejected on the way here (Sept 12):** v1 red-team vs. Juice Shop (neutralised every Steel differentiator); pure geo-differential auditing (strong but narrow); v2's research stage that mined customer complaints into hypotheses (reintroduced a hypothetical layer and was the flakiest stage on stage). Remove Steel and the product must die; that principle chose everything below.

---

## Pipeline (4 stages)

```
URL ──▶ 1 Explore ──▶ 2 Run ──▶ 3 Score ──▶ 4 Fix
        site model    run events   findings +    proposed fixes
        + journeys    (per config) readiness     (stretch: applied on
                                   score         a Steel Computer)
```

Stage 1 is pre-cached for the stage demo (shown as a fast replay). Stages 2–3 run live. Stage 4 is the stretch closer.

### Stage 1 — Explore (zero-context site mapping)

- **Input:** a URL. Optional one-line hint from the user (e.g. "it's a shoe store"), which seeds the site model and lets us shortcut on stage.
- **Behaviour:** one agent on a Steel session maps the site **read-only**, breadth-first from the landing page.
- **Output:** a `SiteModel` (schema below): what the site is, who it is for, brand, category, and the top 3 user journeys with entry points.
- **Stopping rule (all three enforced):** stop when two consecutive pages add no new *action types*; or at 25 pages; or at 3 minutes.
- **Safety allowlist:** may click links, nav, tabs, menus, and scroll; may type only into inputs that look like search. Must never submit a form whose button or surrounding text matches purchase / delete / cancel / subscribe / unsubscribe / confirm patterns, and never type into payment or password fields.
- **Steel primitives:** Sessions API, live viewer embed (the audience watches it think).

### Stage 2 — Run (controlled agent population)

- **Input:** `SiteModel.journeys`.
- **Population matrix:** a baseline config (**desktop, fresh profile, US, DOM engine**) plus variants that change exactly one variable:
  - `device`: mobile mode.
  - `identity`: returning. A persistent Profile warmed up first: the baseline run for that journey is created with `persist_profile=True`, and the returning variant launches with its `profile_id`, so it arrives with the baseline's cookies and history.
  - `country`: two extra countries via residential geo proxies.
  - `engine`: the kind of agent. Baseline is a DOM-based agent (Browser Use). Variants are vision agents driven by computer-use models (Claude computer use; OpenAI computer use as a second vision engine). Same Steel session config, same journey goal; only the agent differs.
  The baseline always runs so every variant has a comparator.
- **Engine adapter:** one interface (`run_journey(session, journey) -> RunEvent stream`) with an implementation per engine, so the Runner is engine-agnostic. Step caps per engine so a slow vision loop cannot eat the wave budget.
- **Execution:** each journey × config is its own Steel session. Journeys **stop at the checkout / payment page and never submit payment.** Sessions run in waves of at most 10 (free-tier cap) with a 12-minute per-session budget (under the 15-minute cap).
- **Output:** a stream of `RunEvent`s per session, ending in a terminal outcome.
- **Steel primitives:** Sessions + concurrency, **mobile mode** (`device_config={"device": "mobile"}`), **persistent Profiles** (`persist_profile=True`, then `profile_id=`), **residential geo proxies** (`use_proxy={"geolocation": {"country": "CA"}}`), the cookbook integrations for Claude and OpenAI computer use on a Steel session, interactive live viewer for the grid, Agent Traces / session replay for jump-to-failure.

### Stage 3 — Score (findings, taxonomy, attribution, readiness)

- **Input:** all `RunEvent`s.
- **Outcome per run:** `completed`, `stalled`, or `harness_error`. Harness errors (model timeouts, Steel session failures, engine crashes unrelated to the page) are **excluded from the score** and shown separately, so tool flakiness never masquerades as a site problem. A stalled run is retried once before being counted.
- **Failure taxonomy (fixed list, one per stall):** `cookie_wall`, `captcha`, `hidden_nav`, `icon_only_control`, `ambiguous_cta`, `geo_block`, `infinite_scroll`, `login_wall`, `layout_shift`, `timeout`, `other`.
- **Classification:** hybrid. Deterministic signals first (URL never changed after N actions → `timeout`; overlay intercepting clicks with cookie/consent text → `cookie_wall`; CAPTCHA iframe present → `captcha`; proxy country returned a block page → `geo_block`). An LLM pass over the final screenshot + last 5 events assigns the remaining categories and writes the one-line description.
- **Attribution:** because only one variable differs from baseline, a stall present in a variant but absent in baseline is attributed to that variable: "fails only on mobile", "fails only for vision agents", "fails only from Germany". A stall present in the baseline too is attributed to `site` (it fails for everyone). A stall present across every engine is flagged `engine_consensus`, the strongest evidence that the site, not the agent, is at fault.
- **Readiness score:** per journey, completion rate across scored configs, weighted 2× for baseline and 1× for each variant; overall score is the mean across journeys, 0–100.
- **Static contrast (cheap, high impact):** fetch the target's public Cloudflare Agent Readiness score once and show it beside ours on the score card. It costs nothing and makes "static vs. real" land in one glance.
- **Output:** a `Finding` list and a `ScoreCard`, each finding linked to its Steel session replay and the step index where the stall began.

### Stage 4 — Fix

- **MVP:** each finding carries a concrete proposed fix generated from its category and the offending element (e.g. "the cart button is icon-only; add `aria-label=\"Cart\"`", "the consent overlay intercepts pointer events; make the accept button keyboard-reachable and first in DOM order").
- **Stretch (Steel Computer bonus):** against the **self-hosted demo store only**, a Steel Computer clones the store repo, applies the proposed patch, restarts the dev server, and re-runs the failing journey × config. The score card updates live. This is the "why does the agent need its own computer" answer: it needs a terminal, a filesystem, and a process to fix and re-test.

---

## Shared schemas (locked in the first 30 minutes)

Indicative shapes; the exact Pydantic models live in `crucible/schemas.py` and are the contract between all four devs.

```
SiteModel {
  url, brand, category, description,          # what it is
  audience_guess: [str],                       # who it's for (from its own pages)
  journeys: [ { id, name, goal, entry_url } ]  # top 3, e.g. find_product / add_to_cart / reach_checkout
}

Config {
  device:   "desktop" | "mobile",
  identity: "fresh" | "returning",
  country:  "US" | "CA" | "DE" | ...,
  engine:   "browser_use" | "claude_cu" | "openai_cu",
  label
}

RunEvent {
  run_id, session_id, journey_id, config, step_index, timestamp,
  action, observation, screenshot_ref,
  outcome: none | step_ok | completed | stalled | harness_error
}

Finding {
  id, journey_id, config, category, description,
  attributed_to: "device" | "identity" | "country" | "engine" | "site",
  engine_consensus: bool,
  session_id, step_index,                      # jump-to-failure
  proposed_fix
}

ScoreCard {
  overall, static_score?,                      # ours vs. Cloudflare's static score
  per_journey: [ { journey_id, score, completed, stalled, harness_errors } ]
}
```

---

## Demo targets and demo script

**Two targets, deliberately:**

- **Headline: a real public e-commerce site**, pre-scouted from 2–3 candidates the night before (mid-size Shopify-style stores are ideal; pick one with a decent Cloudflare static score and a cookie modal). Explore output is cached; Run and Score go live. Only using our own store would smell like Juice Shop.
- **Fix loop: a small self-hosted storefront** (a Next.js commerce template is enough) with three injected agent traps: an icon-only cart button, a consent modal with no accessible name, and a mobile hamburger-only nav. Only using a live site would make the closing loop a coin flip.

**Script (~4 minutes):**

1. Show the target's Cloudflare static score: "85/100, agent-ready."
2. Paste the URL into Crucible. Site model and journey map appear (cached replay, fast).
3. Live grid of Steel sessions runs the journeys across the matrix: desktop, mobile, returning, two countries, DOM and vision agents. Some stall.
4. Score card lands next to the static score. Click a finding: "fails only on mobile", replay frozen at the stall on the right.
5. Click an `engine_consensus` finding: every kind of agent hit the same wall; this is the site's problem.
6. Stretch: point the fix loop at the self-hosted store, watch the Computer patch it, re-run, score climbs.
7. Encore: offer to point it at a judge's own site.

---

## Architecture and ownership (4 devs / 4 Claude sessions)

```
        UI (D) ──▶ Orchestrator ──▶ Steel sessions (mobile · Profiles · geo · viewer · traces)
                       │
        ┌──────────────┼────────────────────────┐
        ▼              ▼                        ▼
   Explore (A)    Engine adapters (A)       Runner (B)        ── all emit schema objects ──▶  Scorer (C) ──▶ UI (D)
   site model     browser_use / claude_cu   matrix, waves,                                    findings, score,
                  / openai_cu               events, lifecycle                                 static contrast,
                                                                                              fixes, fix loop
```

- **Dev A — Explore + engine adapters.** Bounded exploration with the safety allowlist and site model output; the engine adapter interface and its three implementations (Browser Use first, then Claude computer use, then OpenAI). Owns cached site models for demo targets.
- **Dev B — Runner + Steel integration.** Population matrix, session lifecycle (create → connect → release, idempotent release, wave batching under the 10-session cap), mobile / Profile / geo config, Profile warm-up ordering, event emission.
- **Dev C — Scorer.** Failure taxonomy, deterministic classifiers + LLM fallback, attribution and engine consensus, readiness score, Cloudflare static-score fetch, proposed fixes, replay linking. Owns the fix-loop stretch.
- **Dev D — UI + targets.** FastAPI backend, lightweight React + Tailwind front: journey map, live grid of embedded Steel viewers, score card with static contrast, finding detail with replay. Scouts the real target, stands up the self-hosted store with traps, records the cached Explore runs.

A, B, and C build against fixtures of the shared schemas until integration; D builds against mock data from hour one.

**Timeline (24h):** 0:00–0:30 schemas together · 0:30–6:00 each module vertical with fixtures · 6:00–14:00 integrate on the real target · 14:00–20:00 second engine, polish, cache demo stages, self-hosted store + fix loop · 20:00–24:00 rehearse five times, Devpost, fallback checks.

---

## Scope tiers

- **MVP (must-win):** Explore → Run → Score with proposed fixes, on one real site, 2 journeys, configs = baseline + mobile + returning + one extra country, Browser Use engine only, live grid, score card with the Cloudflare static contrast, one attributed finding with replay.
- **Should:** Claude computer use as the second engine (unlocks `engine` attribution and `engine_consensus`), 3 journeys, 3 countries, polished finding detail view, cached Explore for two targets.
- **Stretch:** OpenAI computer use as a third engine; fix loop on Steel Computer against the self-hosted store; run on a judge's site as the encore.

## Steel primitives used (all load-bearing)

Sessions API + wave concurrency · **mobile mode** · **persistent Profiles** · **residential geo proxies** · computer-use integrations on Steel sessions (Claude, OpenAI) · interactive live viewer embeds · **Agent Traces / session replay** for jump-to-failure · **Steel Computer** (stretch) for the fix loop.

## Error handling

On a hostile site, agent failure is the signal, not a crash. A stalled run is a finding; a blocked run is a finding. Harness errors are isolated, retried once, and shown outside the score. Per-session timeouts and per-engine step caps are enforced below Steel's limits, and session release is idempotent so a paid session is never leaked. If the Cloudflare static score cannot be fetched, the contrast panel is simply hidden.

## Testing (pragmatic for 24h)

Unit-test the **Scorer** first: classifiers, attribution, engine consensus, and the score formula against fixture event streams. A **mock target** (a local static site with known traps) lets Runner, Explore, and the engine adapters develop without burning Steel credits. The self-hosted store is the integration target for the fix loop; the real site is the integration target for everything else. No coverage chasing.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Explore is slow / flaky on stage | Cached site model for demo targets; user hint box to shortcut |
| An engine fails for reasons unrelated to the site | `harness_error` bucket excluded from score; retry once |
| Vision engines are slow or expensive | Per-engine step caps; vision engines run only on the 2 demo journeys; Browser Use is the MVP engine |
| Real target blocks or CAPTCHAs everything | Pre-scout three candidates; Steel stealth on; cached run as last resort |
| Steel Computer beta unavailable or unstable | Fix loop is stretch-only; confirm access at the 1 PM workshop before touching it |
| Proxy credit / concurrency limits | Spend the $10 to unlock residential proxies; ask the Steel booth for elevated concurrency |
| Judges name Agent Checker or Cloudflare | Prior-art slide: static vs. single-agent vs. controlled population; we differ on every axis that needs Steel |

## Practical setup

`STEEL_API_KEY` + model keys in `.env`, gitignored. Spend the $10 to unlock residential proxies. Ask the Steel booth (1 PM workshop) for elevated concurrency and proxy credits, and confirm Steel Computer beta scope.

## Decisions

- **Spine:** agent-readiness measured with real agents; no research or synthetic-consumer layer.
- **Population axes:** device, identity, country, engine; one variable at a time against a baseline.
- **Demo target:** real e-commerce site (headline) + self-hosted storefront with injected traps (fix loop).
- **Framing device:** Cloudflare static score beside our measured score.
- **Classification:** deterministic signals first, LLM for the remainder.
- **Agent engines:** Browser Use (MVP), Claude computer use (should), OpenAI computer use (stretch), all on Steel.
- **UI:** FastAPI + React + Tailwind.
