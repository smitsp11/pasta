# Crucible — Design

Hackathon: Battle of the Schools — **Steel.dev Web Agents track** (Sept 12–13 2026). Goal: 1st place (+ possibly the $500 Steel Computer bonus). Team of 4, parallel work. Stack: **Python**.

**Product spine (decided):** red-teaming / vulnerability product with a realistic-crowd baseline. Adversarial agents probe a live product for abuse and breakage; cooperative geo/persona agents form the "normal traffic" they hide inside. Headline: **"does your product catch the fraudster without breaking for the grandma?"**

See `docs/concept.md` for the pitch, prior art, and vocabulary.

---

## Architecture (5 modules, each independently ownable)

```
        ┌─────────────┐
UI ──▶  │ Orchestrator │ ──creates──▶ Steel Sessions (cloud browsers)
        │ (Run Manager)│              │ Profiles · geo proxies · concurrency
        └──────┬───────┘              ▼
               │              ┌────────────────┐
               │              │  Agent Core     │  observe→decide→act loop
               │              │  (persona/attack│  (LLM + Playwright/CDP)
               │              │   variants)     │
               │              └───────┬─────────┘
               │                      │ emits Events (shared schema)
               ▼                      ▼
        ┌─────────────┐      ┌────────────────┐
        │  Dashboard  │◀─────│ Findings Engine │  outcomes, funnel,
        │ live grid + │      │ + data store    │  vuln scoring, replay links
        │ report      │      └────────────────┘
        └─────────────┘
```

1. **Orchestrator / Run Manager** — takes a target URL + run config (personas, attacks, geos); spins up Steel sessions with the right Profile + geo proxy + device per agent; manages lifecycle (create → connect → release); enforces the free-tier caps (**10 concurrent, 15-min max**) by batching in waves; never leaks a paid session. `asyncio`.
2. **Agent Core** — the shared observe→decide→act loop driving a Steel browser. Two flavors on one engine: **cooperative persona** and **adversarial attacker**. Built on **Browser Use** (runs natively on Steel; handles the loop) with persona/attack prompts layered on top — fastest reliable path in 24h vs. hand-rolling. Emits structured events.
3. **Persona & Attack Library** — data-driven definitions. Cooperative personas (goal, traits, geo, device, patience). Adversarial **playbooks**: coupon/promo farming, signup & bot abuse, broken auth / access control, rate-limit probing. Easy to extend.
4. **Findings Engine + store** — ingests events; detects outcomes (completed / dropped-off / **exploit succeeded**); scores severity; aggregates into a funnel + vulnerability report; links each finding to its **Steel Agent Trace / session replay** for jump-to-failure.
5. **Dashboard / UI** — live grid (embedded Steel interactive viewers), funnel, findings/vuln report with replay links, and the money-shot view: *"attacker slipped through here / grandma dropped off there."* **FastAPI backend + lightweight React + Tailwind front.**

## Data flow

Enter URL + pick run config → Orchestrator launches sessions (Profiles for returning personas, geo proxy per persona) → each Agent runs on its session, streaming events → Findings Engine aggregates **live** → Dashboard updates grid + funnel in real time → on finish, a report with jump-to-failure replays.

## The shared contract: Event schema

The interface between all modules. Locked first, together, in the first 30 minutes. Every agent emits a stream of events; Findings and Dashboard consume them. Indicative shape:

```
Event {
  run_id, agent_id, persona_id, kind: "cooperative" | "adversarial",
  geo, device, step_index, timestamp,
  action,                 # what the agent did (navigate/click/type/...)
  observation,            # brief page state / result
  outcome,                # none | step_ok | dropped_off | exploit_success | blocked | error
  finding,                # optional: {severity, category, description}
  trace_ref,              # Steel session id / trace pointer for replay
  screenshot_ref          # optional
}
```

## Demo target (reliability decision)

Primary target = **OWASP Juice Shop** — a real, well-known, *intentionally vulnerable* web shop, self-hosted. Guarantees the attackers find real things live (coupons, auth flaws, access-control bugs), it's credible, and it's 100% reliable on stage. Running adversarial agents against a target we own = clean, no ToS/ethics issue. **Encore:** offer to point it at the judges' own site live.

## Error handling

On the hostile web, agent failure is *the signal*, not a crash — a persona that can't complete = a drop-off finding; an attacker that gets blocked = a good result to show. Per-session failures are isolated; timeouts enforced; session release is idempotent so we never bill-leak.

## Testing (pragmatic for 24h)

TDD where cheap and high-value: the **Findings Engine** logic (outcome/funnel/severity) against fixture events. A **mock target** to develop the agent loop without burning Steel credits. Juice Shop as the integration target. Not chasing full coverage.

## Parallelization (4 devs / 4 Claude sessions)

**First 30 min, together: lock the Event schema.** Then split:
- **Dev A → Orchestrator + Steel integration** (sessions, Profiles, proxies, concurrency, event bus)
- **Dev B → Agent Core + Persona/Attack library** (the loop, cooperative + adversarial)
- **Dev C → Findings Engine + data model** (outcomes, funnel, vuln scoring, replay linking)
- **Dev D → Dashboard/UI + demo target** (grid embeds, viz, report, deploy Juice Shop)

A/B/C build against the shared schema with fixtures until integration; D builds UI against mock data immediately.

## Scope tiers

- **MVP (must-win):** Orchestrator + Agent Core on Steel + 2 adversarial playbooks + a few cooperative personas + live grid + findings report w/ replay links, vs. Juice Shop.
- **Differentiators (should):** geo + persistent Profiles (a returning persona across 2–3 countries); the funnel + "fraudster vs grandma" money-shot; polished dashboard.
- **Stretch:** more attack playbooks; a Steel Computer angle for the $500 bonus; run-on-judges'-site encore.

## Steel primitives used (all load-bearing)

Sessions API + fleet concurrency · persistent **Profiles** · residential **proxies + geolocation** · **Agent Traces** + session replay · embeddable **interactive live viewer** · Credentials API.

## Practical setup

Spend the **$10** to unlock residential proxies (geo is the differentiator). Ask the Steel booth (1 PM workshop) for elevated concurrency + proxy credits. Keys in `.env` (gitignored).

## Open decisions confirmed as recommendations

- **Demo target:** OWASP Juice Shop (self-hosted).
- **Agent engine:** Browser Use on Steel (vs. hand-rolled loop).
- **UI:** FastAPI + React + Tailwind.
