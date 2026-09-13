# Crucible — Design (v2)

Hackathon: Battle of the Schools — **Steel.dev Web Agents track** (Sept 12–13 2026). Goal: 1st place (+ the $500 Steel Computer bonus if the beta is usable). Team of 4, parallel work. Stack: **Python**.

**One-liner: Lighthouse for AI agents, grounded in real customer complaints.** Give Crucible a URL with zero context. It figures out what the site is and who it serves, gathers real complaints about it from the web, turns those into testable hypotheses, runs a controlled population of agents through the site on real cloud browsers, and hands back a readiness score with the exact moment each agent got stuck, the customer quote it corroborates, and a proposed fix.

Headline demo moment: *"Three customers said checkout breaks on mobile in Canada. Here is our agent hitting it, frame by frame."*

See `docs/concept.md` for the pitch, prior art, and vocabulary.

---

## What changed from v1 and why

v1 was a red-team product against OWASP Juice Shop with a cooperative "crowd" as scenery. It was dropped because:

- Juice Shop neutralised every Steel differentiator (no localisation, no defences, so geo/Profiles had no observable effect).
- The crowd had no mechanism; removing it changed nothing.
- Red-team is the archetype that already won the previous web-agents hackathon, and nothing in it required Steel.

v2 keeps the "population of agents on a live site" DNA but makes two honest moves:

1. **Agents are not consumers.** So we do not sell "predicted consumer behaviour." Research gathers *real* human complaints; agents *test* them. Findings are either a reproduced human complaint or a genuine agent-readiness failure. Both are real.
2. **The population is a controlled experiment.** Configs change one variable at a time (device, identity age, country) against a baseline, so every finding is attributable. Those variables are exactly Steel's primitives: mobile mode, persistent Profiles, residential geo proxies.

This is Steel's own thesis returned as a product: the web is hostile to agents, and reliability is diagnosis, not blind retries.

---

## Pipeline (5 stages)

```
URL ──▶ 1 Explore ──▶ 2 Research ──▶ 3 Run ──▶ 4 Score ──▶ 5 Fix
        site model    research brief   run events  findings +   proposed fixes
        + journeys    + hypotheses     (per config) readiness    (stretch: applied
                                                    score        on Steel Computer)
```

Stages 1–2 are pre-cached for the stage demo (shown as a fast replay). Stages 3–4 run live. Stage 5 is the stretch closer.

### Stage 1 — Explore (zero-context site mapping)

- **Input:** a URL. Optional one-line hint from the user (e.g. "it's a shoe store"), which seeds the site model and lets us shortcut on stage.
- **Behaviour:** one agent on a Steel session maps the site **read-only**, breadth-first from the landing page.
- **Output:** a `SiteModel` (schema below): what the site is, who it is for, brand name, category, likely competitors, and the top 3 user journeys with their entry points.
- **Stopping rule (all three enforced):** stop when two consecutive pages add no new *action types*; or at 25 pages; or at 3 minutes.
- **Safety allowlist:** may click links, nav, tabs, menus, and scroll; may type only into inputs that look like search. Must never submit a form whose button or surrounding text matches purchase / delete / cancel / subscribe / unsubscribe / confirm patterns, and never type into payment or password fields.
- **Steel primitives:** Sessions API, live viewer embed (the audience watches it think).

### Stage 2 — Research (evidence-backed hypothesis generation)

The rule that keeps this honest: **research supplies what to test, never the answer.**

- **Input:** the `SiteModel`.
- **Sources (max 6), each in its own parallel Steel session:** the site's own help centre / FAQ; Trustpilot or equivalent; Google reviews; Reddit search for the brand; app-store reviews if an app exists; one competitor's equivalent journey for contrast. Running these in Steel is load-bearing: review sites and Reddit are bot-hostile and geo-varying, and the fan-out demonstrates fleet-scale sessions.
- **Output:** a `ResearchBrief` (schema below) containing audience segments with evidence links, top complaints as quotes with links, and **hypotheses**. Each hypothesis is one journey plus one config plus the complaint that motivated it.
- **Bounds:** 6 sources, 4 minutes wall clock, hard stop; a source that yields nothing is dropped, not retried.
- **Cached fallback:** a saved brief for each pre-scouted demo target.

### Stage 3 — Run (controlled agent population)

- **Input:** `SiteModel.journeys` and `ResearchBrief.hypotheses`.
- **Population matrix:** a baseline config (**desktop, fresh profile, US**) plus variants that change exactly one variable: `mobile`, `returning` (a persistent Profile warmed up first: the baseline run for that journey is created with `persist_profile=True`, and the returning variant launches with its `profile_id`, so it arrives with the baseline's cookies and history), and two extra countries. Research hypotheses add or prioritise specific journey × config pairs; the baseline always runs so every variant has a comparator.
- **Execution:** each journey × config runs as its own Steel session driven by Browser Use with the journey goal as the task. Journeys **stop at the checkout / payment page and never submit payment.** Sessions run in waves of at most 10 (free-tier cap) with a 12-minute per-session budget (under the 15-minute cap).
- **Output:** a stream of `RunEvent`s per session (schema below), ending in a terminal outcome.
- **Steel primitives:** Sessions + concurrency, **mobile mode** (`device_config={"device": "mobile"}`), **persistent Profiles** (`persist_profile=True`, then `profile_id=`), **residential geo proxies** (`use_proxy={"geolocation": {"country": "CA"}}`), interactive live viewer for the grid, Agent Traces / session replay for jump-to-failure.

### Stage 4 — Score (findings, taxonomy, readiness)

- **Input:** all `RunEvent`s plus the `ResearchBrief`.
- **Outcome per run:** `completed`, `stalled`, or `harness_error`. Harness errors (model timeouts, Steel session failures, Browser Use crashes unrelated to the page) are **excluded from the score** and shown separately, so tool flakiness never masquerades as a site problem. A stalled run is retried once before being counted.
- **Failure taxonomy (fixed list, one per stall):** `cookie_wall`, `captcha`, `hidden_nav`, `icon_only_control`, `ambiguous_cta`, `geo_block`, `infinite_scroll`, `login_wall`, `layout_shift`, `timeout`, `other`.
- **Classification:** hybrid. Deterministic signals first (page never changed URL after N actions → `timeout`; overlay intercepting clicks with cookie/consent text → `cookie_wall`; CAPTCHA iframe present → `captcha`; proxy country returned a block page → `geo_block`). An LLM pass over the final screenshot + last 5 events assigns the remaining categories and writes the one-line description.
- **Attribution:** because only one variable differs from baseline, a stall present in a variant but absent in baseline is attributed to that variable ("fails only on mobile").
- **Finding tags:** `corroborated` if a research hypothesis predicted this journey × config × failure (attach the quote and link), otherwise `agent_readiness`.
- **Readiness score:** per journey, completion rate across scored configs, weighted 2× for baseline and 1× for each variant; overall score is the mean across journeys, 0–100.
- **Output:** a `Finding` list and a `ScoreCard`, each finding linked to its Steel session replay and the step index where the stall began.

### Stage 5 — Fix

- **MVP:** each finding carries a concrete proposed fix generated from its category and the offending element (e.g. "the cart button is icon-only; add `aria-label=\"Cart\"`", "the consent overlay intercepts pointer events; make the accept button keyboard-reachable and first in DOM order").
- **Stretch (Steel Computer bonus):** against the **self-hosted demo store only**, a Steel Computer clones the store repo, applies the proposed patch, restarts the dev server, and re-runs the failing journey × config. The score card updates live. This is the "why does the agent need its own computer" answer: it needs a terminal, a filesystem, and a process to fix and re-test.

---

## Shared schemas (locked in the first 30 minutes)

Indicative shapes; the exact Pydantic models live in `crucible/schemas.py` and are the contract between all four devs.

```
SiteModel {
  url, brand, category, description,          # what it is
  audience_guess: [str],                       # who it's for (from its own pages)
  competitors: [str],
  journeys: [ { id, name, goal, entry_url } ]  # top 3, e.g. find_product / add_to_cart / reach_checkout
}

ResearchBrief {
  segments:   [ { name, evidence: [ { quote, url } ] } ],
  complaints: [ { id, quote, url, source } ],
  hypotheses: [ { id, journey_id, config: Config, complaint_id, rationale } ]
}

Config { device: "desktop"|"mobile", identity: "fresh"|"returning", country: "US"|"CA"|"DE"|..., label }

RunEvent {
  run_id, session_id, journey_id, config, step_index, timestamp,
  action, observation, screenshot_ref,
  outcome: none | step_ok | completed | stalled | harness_error
}

Finding {
  id, journey_id, config, category, description,
  attributed_to: "device"|"identity"|"country"|"baseline",
  tag: "corroborated"|"agent_readiness", complaint_id?,
  session_id, step_index,                      # jump-to-failure
  proposed_fix
}

ScoreCard { overall, per_journey: [ { journey_id, score, completed, stalled, harness_errors } ] }
```

---

## Demo targets and demo script

**Two targets, deliberately:**

- **Headline: a real public e-commerce site**, pre-scouted from 2–3 candidates the night before (mid-size Shopify-style stores with real reviews on Trustpilot/Reddit are ideal). Explore and Research outputs are cached; Run and Score go live. Only using our own store would smell like Juice Shop.
- **Fix loop: a small self-hosted storefront** (a Next.js commerce template is enough) with three injected agent traps: an icon-only cart button, a consent modal with no accessible name, and a mobile hamburger-only nav. Only using a live site would make the closing loop a coin flip.

**Script (~4 minutes):**

1. Paste the URL. Site model and journey map appear (cached replay, fast).
2. Research brief slides in: segments, three real complaint quotes, hypotheses.
3. Live grid of Steel sessions runs the journeys across the matrix. Some stall on mobile / in Canada.
4. Score card lands. Click the corroborated finding: quote on the left, replay frozen at the stall on the right.
5. Stretch: point the fix loop at the self-hosted store, watch the Computer patch it, re-run, score climbs.
6. Encore: offer to point it at a judge's own site.

---

## Architecture and ownership (4 devs / 4 Claude sessions)

```
        UI (D) ──▶ Orchestrator ──▶ Steel sessions (mobile · Profiles · geo · viewer · traces)
                       │
        ┌──────────────┼──────────────────┐
        ▼              ▼                  ▼
   Explore (A)    Research (A)        Runner (B)          ── all emit schema objects ──▶  Scorer (C) ──▶ UI (D)
   site model     research brief      run events                                          findings, score,
                                                                                          proposed fixes, fix loop
```

- **Dev A — Explore + Research.** Both are bounded exploration agents with schema output and the same safety allowlist. Owns the stopping rules and the cached briefs for demo targets.
- **Dev B — Runner + Steel integration.** Population matrix, session lifecycle (create → connect → release, idempotent release, wave batching under the 10-session cap), mobile/Profile/geo config, Browser Use journey execution, event emission.
- **Dev C — Scorer.** Failure taxonomy, deterministic classifiers + LLM fallback, attribution, corroboration matching, readiness score, proposed fixes, replay linking. Owns the fix-loop stretch.
- **Dev D — UI + targets.** FastAPI backend, lightweight React + Tailwind front: journey map, live grid of embedded Steel viewers, score card, finding detail (quote + replay). Scouts the real target, stands up the self-hosted store with traps, and records the cached runs.

A, B, and C build against fixtures of the shared schemas until integration; D builds against mock data from hour one.

**Timeline (24h):** 0:00–0:30 schemas together · 0:30–6:00 each module vertical with fixtures · 6:00–14:00 integrate on the real target · 14:00–20:00 polish, cache demo stages, self-hosted store + fix loop · 20:00–24:00 rehearse five times, Devpost, fallback checks.

---

## Scope tiers

- **MVP (must-win):** Explore → Research → Run → Score with proposed fixes, on one real site, 2 journeys, 4 configs (baseline, mobile, returning, one extra country), live grid, score card, corroborated finding with replay.
- **Should:** 3 journeys, 3 countries, polished finding detail view, cached Explore/Research replays for two targets.
- **Stretch:** fix loop on Steel Computer against the self-hosted store; run on a judge's site as the encore.

## Steel primitives used (all load-bearing)

Sessions API + wave concurrency · **mobile mode** · **persistent Profiles** · **residential geo proxies** · interactive live viewer embeds · **Agent Traces / session replay** for jump-to-failure · **Steel Computer** (stretch) for the fix loop.

## Error handling

On a hostile site, agent failure is the signal, not a crash. A stalled run is a finding; a blocked run is a finding. Harness errors are isolated, retried once, and shown outside the score. Per-session timeouts are enforced below Steel's cap and session release is idempotent so a paid session is never leaked. Research sources that fail are dropped silently within the stage budget.

## Testing (pragmatic for 24h)

Unit-test the **Scorer** first: classifiers, attribution, corroboration matching, and the score formula against fixture event streams. A **mock target** (a local static site with known traps) lets Runner and Explore develop without burning Steel credits. The self-hosted store is the integration target for the fix loop; the real site is the integration target for everything else. No coverage chasing.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Explore or Research is slow / flaky on stage | Cached outputs for demo targets; user hint box to shortcut Explore |
| Browser Use fails for reasons unrelated to the site | `harness_error` bucket excluded from score; retry once |
| Real target blocks or CAPTCHAs everything | Pre-scout three candidates; Steel stealth on; cached run as last resort |
| Steel Computer beta unavailable or unstable | Fix loop is stretch-only; confirm access at the 1 PM workshop before touching it |
| Proxy credit / concurrency limits | Spend the $10 to unlock residential proxies; ask the Steel booth for elevated concurrency |
| Corroboration matching is fuzzy | Hypotheses carry explicit `journey_id` + `Config`; matching is exact on those, not semantic |

## Practical setup

`STEEL_API_KEY` + model keys in `.env`, gitignored. Spend the $10 to unlock residential proxies. Ask the Steel booth (1 PM workshop) for elevated concurrency and proxy credits, and confirm Steel Computer beta scope.

## Decisions

- **Spine:** agent-readiness grounded in evidence-backed research (not red-team, not synthetic consumers).
- **Demo target:** real e-commerce site (headline) + self-hosted storefront with injected traps (fix loop).
- **Population:** controlled one-variable-at-a-time matrix; research hypotheses prioritise pairs.
- **Diff/classification:** deterministic signals first, LLM for the remainder.
- **Agent engine:** Browser Use on Steel.
- **UI:** FastAPI + React + Tailwind.
