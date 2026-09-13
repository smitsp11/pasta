# Crucible — concept, prior art & requirements

> Working title: **Crucible** (a severe test that reveals what something is made of).

Hackathon: Battle of the Schools — **Steel.dev Web Agents track**. Goal: 1st place (+ possibly the $500 Steel Computer bonus). Stack: **Python**.

---

## 1. The pitch (simplified)

**One-liner:**
> Lighthouse for AI agents, measured with real agents instead of static checks. Point Crucible at any website with zero context: it discovers the site's key user journeys, then runs a controlled population of real agents through them on real cloud browsers — on mobile, as a returning visitor, from other countries, and with different kinds of agent — and hands you a readiness score, the exact moment each agent got stuck, what that stall is attributable to, and a proposed fix.

**The 30-second version:**
People are starting to hand real work to web agents: shopping, booking, forms, account admin. Site owners now face a question they have no way to answer: does my site survive when the visitor is an agent? Today's "agent readiness" tools (Cloudflare, Apify) only check static signals like robots.txt and llms.txt; they never run an agent through a task. Crucible does. It maps the site with zero context, then unleashes a population of real agents on real Steel browsers, changing one variable at a time — mobile, returning identity, country, DOM agent vs. vision agent — so every failure is attributable. You get a score next to Cloudflare's static score, and the frame where each agent hit the wall.

**Product spine (decided): agent-readiness, measured with real agents.**
- **No hypothetical layer.** We don't predict what customers would do. Agents are the population being measured, so every finding is a fact: "an agent tried to reach checkout and stalled at step 4 on the cookie overlay."
- **A controlled experiment, not a swarm.** Baseline (desktop, fresh, US, DOM agent) plus variants that change exactly one thing: mobile mode, a returning persistent Profile, another country, a vision agent. Those variables *are* Steel's differentiators, so the product cannot exist on plain Playwright.
- **Attribution is the product.** "Fails only on mobile." "Fails only for vision agents." "Fails for every kind of agent, so it's the site." That last one, engine consensus, is the strongest evidence a site owner can get.

**Why it's not just "AI QA":**
1. **It measures what the static tools can't.** Cloudflare can tell you whether you published llms.txt. We tell you whether an agent can actually check out.
2. **Population, not one agent.** Agent Checker runs a single agent one way. We run a matrix on Steel's mobile / identity / geo infrastructure plus multiple agent engines, and attribute every stall.
3. **It is Steel's own thesis as a product.** The web is hostile to agents; reliability is diagnosis, not blind retries. Steel's leaderboard rates agents on sites; Crucible is the other half, rating sites for agents.

**The demo moment:** Cloudflare's static score on the left ("85/100 agent-ready"), Crucible's measured score on the right, and a replay frozen on a mobile agent stuck behind a cookie banner. Stretch closer: a Steel Computer applies the proposed fix to our self-hosted store, re-runs, and the score climbs live.

---

## 2. Similar products / prior art (and how we differ)

| Name | What it is | How Crucible differs |
|---|---|---|
| **Cloudflare Agent Readiness score** (Apr 2026, isitagentready.com) | Static score: robots.txt, llms.txt, headers, bot rules, MCP/API discovery. [blog](https://blog.cloudflare.com/agent-readiness/) | Never runs an agent. We measure task completion by real agents and show both scores side by side. Our foil, not our competitor. |
| **Apify AI Agent Readiness Audit** | 47 static crawl-based checks in 7 categories. [api](https://apify.com/exalted_mud_vjz/agent-readiness-audit/api) | Same: static only. |
| **Agent Checker** (agentchecker.ai) | A real agent drives a real browser through ~20 fixed tasks; PDF + click replay. £19. | Closest prior art. One agent, one config. No mobile, geo, returning identity, engine diversity, attribution, or fix loop — every axis we add needs Steel. |
| **Steel AgentBench leaderboard** | Ranks LLM agents across interactive environments. [site](https://leaderboard.steel.dev/) | Rates agents on sites. We rate sites for agents: the missing half. |
| **Browser Use `qa-use`** | Open-source "QA-test your site with an agent." | The commoditised baseline. We add zero-context discovery, a controlled population, attribution, a score, and jump-to-failure replay. |
| **UXAgent** (Amazon, CHI 2025) | LLM agents as imagined usability-test participants. [paper](https://arxiv.org/abs/2504.09407) | UXAgent imagines humans. We measure agents, which is the population actually arriving. |
| **Lighthouse / axe** | Deterministic page audits for performance and accessibility. | We audit *task completion*, not static page properties, and show the failing moment. |
| **Coframe** (on Browserbase) | Agents that A/B test and edit live pages. | Closest in spirit to our fix loop; we start from agent failures rather than conversion tuning. |

**Positioning in one line:** *Lighthouse for agents: real agents, a controlled population on Steel's mobile / identity / geo infrastructure, attribution, and the replay, next to the static score everyone else stops at.*

---

## 3. Requirements to read up on

### A. Vocabulary to explain the idea

- **Agent-readiness** — how well a site holds up when an AI agent, not a human, tries to complete a task on it.
- **Static vs. measured readiness** — checking robots.txt / llms.txt / headers (Cloudflare, Apify) vs. running a real agent through a real task (us).
- **Site model** — the structured output of zero-context exploration: what the site is, who it's for, its key journeys.
- **Journey** — a task completed end to end: find product → add to cart → reach checkout.
- **Controlled population / one-variable-at-a-time** — every config differs from baseline in exactly one dimension, so failures are attributable.
- **Engine** — the kind of agent: DOM-based (Browser Use) vs. vision / computer-use (Claude, OpenAI).
- **Engine consensus** — a stall every engine hits; the strongest evidence that the site, not the agent, is at fault.
- **Attribution** — which single variable a stall is pinned to: device, identity, country, engine, or the site itself.
- **Persistent Profile / returning identity** — a Steel browser identity that remembers past visits.
- **Mobile mode** — Steel's full mobile fingerprint (viewport, touch, UA), not a spoofed header.
- **Failure taxonomy** — the fixed list of stall causes (cookie wall, CAPTCHA, hidden nav, icon-only control, geo-block, …).
- **Harness error** — a failure caused by our tooling, not the site; kept out of the score.
- **Session replay / jump-to-failure** — Steel Agent Traces linking a finding straight to the frame where it happened.
- **Readiness score** — weighted journey completion across configs, 0–100.
- **Fix loop** — proposed fix → applied on a Steel Computer → re-run → score delta.

### B. Tech to learn to build it

**Steel (the core — read these first):**
- Intro & overview — https://docs.steel.dev/overview/intro-to-steel
- Sessions API — https://docs.steel.dev/overview/sessions-api/overview
- Session lifecycle & limits (15-min free cap, timeouts) — https://docs.steel.dev/overview/sessions-api/session-lifecycle
- Session configuration (**mobile mode** via `device_config`, viewport) — https://docs.steel.dev/overview/sessions-api/configuration
- **Persistent Profiles** (`persist_profile=True`, `profile_id=`) — https://docs.steel.dev/overview/profiles-api/overview
- **Residential proxies + geolocation** (`use_proxy={"geolocation": {"country": ...}}`) — https://docs.steel.dev/overview/stealth/proxies
- **Computer-use integrations on Steel** (Claude, OpenAI) — https://docs.steel.dev/cookbook (computer-use recipes)
- **Live session embed** (the grid) — https://docs.steel.dev/overview/sessions-api/embed-sessions/live-sessions
- **Agent Traces** (jump-to-failure) — https://docs.steel.dev/overview/agent-traces/overview
- Python + Playwright quickstart — https://docs.steel.dev/integrations/playwright
- (Stretch) Steel Computer beta — https://computers-preview.apidocumentation.com · activate: https://app.steel.dev/computer-access

**Browser automation & agents:**
- **Playwright for Python** + `connect_over_cdp` — https://playwright.dev/python/
- **Browser Use** on Steel for the DOM engine (the observe → decide → act loop).
- **Structured output** (Pydantic) for the site model, events, findings.
- Claude API reference — read via the `claude-api` skill before wiring the model.
- Cloudflare's public checker for the static contrast — https://isitagentready.com

**Supporting engineering:**
- Python `asyncio` for parallel Steel sessions in waves under the 10-session cap.
- Secrets in `.env`, gitignored.
- FastAPI + React + Tailwind for the journey map, live grid, score card, finding detail.

---

## Decisions & open items
- **Team:** 4 devs, parallel work (module split in the design doc). ✅
- **Spine:** agent-readiness measured with real agents (red-team, synthetic-consumer, and complaint-research versions rejected). ✅
- **Full design:** `docs/superpowers/specs/2026-09-12-crucible-design.md`
- At the event: confirm Steel Computer beta scope at the 1:00 PM workshop (fix loop is stretch-only); secure elevated concurrency / proxy credits from the Steel booth; pick the real demo target from 2–3 pre-scouted candidates and capture its Cloudflare static score.
