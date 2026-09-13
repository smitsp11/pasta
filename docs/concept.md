# Crucible — concept, prior art & requirements

> Working title: **Crucible** (a severe test that reveals what something is made of).

Hackathon: Battle of the Schools — **Steel.dev Web Agents track**. Goal: 1st place (+ possibly the $500 Steel Computer bonus). Stack: **Python**.

---

## 1. The pitch (simplified)

**One-liner:**
> Lighthouse for AI agents, grounded in real customer complaints. Point Crucible at any website with zero context: it works out what the site is and who it serves, gathers real complaints about it from the web, turns them into hypotheses, runs a controlled population of AI agents through the site in real cloud browsers, and hands you a readiness score with the exact moment each agent got stuck, the customer quote it corroborates, and a proposed fix.

**The 30-second version:**
Every company has customers complaining somewhere on the web — Trustpilot, Reddit, app-store reviews — and no cheap way to reproduce what they're describing. Meanwhile AI agents are starting to shop, book, and browse on their behalf, and nobody knows whether their site survives that. Crucible does both at once. It reads the site, reads the complaints, and then unleashes agents on real Steel browsers — on mobile, as a returning visitor, from Canada or Germany — one variable at a time, so every failure is attributable. When an agent hits the exact wall a customer described, you get the quote and the replay side by side.

**Product spine (decided): agent-readiness, grounded in evidence-backed research.**
- **Research gathers real complaints; agents test them.** Research never predicts behaviour — agents are not consumers. It produces *hypotheses* (journey + config + the complaint that motivated it), and the run stage tests them.
- **The population is a controlled experiment.** Baseline (desktop, fresh, US) plus variants that change exactly one thing: mobile mode, a returning persistent Profile, another country. Those variables *are* Steel's differentiators, so the product cannot exist on plain Playwright.
- **Two kinds of finding, both honest:** *corroborated* (a real complaint the agents reproduced) and *agent-readiness* (the site is hostile to agents specifically; the agents are the population being measured).

**Why it's not just "AI QA":**
1. **Findings are grounded in real humans.** "Three customers said checkout breaks on mobile in Canada; here's our agent hitting it." That is not a synthetic-user guess.
2. **Attributable, not noisy.** One-variable-at-a-time configs mean "fails only on mobile" is a fact, not an impression.
3. **It is Steel's own thesis as a product.** The web is hostile to agents; reliability is diagnosis, not blind retries; agents run at fleet scale.

**The demo moment:** a corroborated finding — customer quote on the left, the Steel replay frozen at the stall on the right. Stretch closer: a Steel Computer applies the proposed fix to our self-hosted store, re-runs, and the score climbs live.

---

## 2. Similar products / prior art (and how we differ)

| Name | What it is | How Crucible differs |
|---|---|---|
| **UXAgent** (Amazon, CHI 2025) | LLM agents as simulated usability-test participants. [paper](https://arxiv.org/abs/2504.09407) | UXAgent *imagines* users and runs a plain Chrome connector. We ground hypotheses in real complaints and run a controlled matrix on real geo / device / identity via Steel. |
| **Synthetic Users** (syntheticusers.io) | Commercial "synthetic user research" — mostly LLM-imagined interviews. | We never sell imagined behaviour; findings are reproduced complaints or measured agent failures. |
| **Browser Use `qa-use`** | Open-source "QA-test your site with an agent." | The commoditised baseline. We add research grounding, a controlled population, attribution, a readiness score, and jump-to-failure replay. |
| **Browser Brawl** (YC Web Agents Hackathon winner) | Attacker vs. defender agents on a live site. [site](https://www.browser-brawl.com/) | Same "agents vs. product" energy, but we diagnose a real product instead of staging a duel, and we don't depend on a defended target. |
| **Lighthouse / axe** | Deterministic page audits for performance and accessibility. | We audit *task completion by agents*, not static page properties — and we show the failing moment. |
| **WebArena / WebVoyager** | Benchmarks for web agents on sandboxed sites. [WebArena](https://github.com/web-arena-x/webarena) | Benchmarks rate agents; we use agents to rate a product. |
| **Coframe** (on Browserbase) | Agents that A/B test and edit live pages. | Closest in spirit to our fix loop; we start from complaints and agent failures rather than conversion tuning. |

**Positioning in one line:** *Lighthouse for agents, with the customer's complaint and the replay side by side, on Steel's real mobile / identity / geo infrastructure.*

---

## 3. Requirements to read up on

### A. Vocabulary to explain the idea

- **Agent-readiness** — how well a site holds up when an AI agent, not a human, tries to complete a task on it.
- **Site model** — the structured output of zero-context exploration: what the site is, who it's for, its key journeys.
- **Journey** — a task a user (or agent) completes end to end: find product → add to cart → reach checkout.
- **Hypothesis** — a journey + a config + the real complaint that motivated testing it.
- **Corroborated finding** — a real complaint the agents reproduced, with quote and replay.
- **Controlled population / one-variable-at-a-time** — every config differs from baseline in exactly one dimension, so failures are attributable.
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
- **Live session embed** (the grid) — https://docs.steel.dev/overview/sessions-api/embed-sessions/live-sessions
- **Agent Traces** (jump-to-failure) — https://docs.steel.dev/overview/agent-traces/overview
- Python + Playwright quickstart — https://docs.steel.dev/integrations/playwright · Cookbook — https://docs.steel.dev/cookbook
- (Stretch) Steel Computer beta — https://computers-preview.apidocumentation.com · activate: https://app.steel.dev/computer-access

**Browser automation & agents:**
- **Playwright for Python** + `connect_over_cdp` — https://playwright.dev/python/
- **Browser Use** on Steel for journey execution (the observe → decide → act loop).
- **Structured output** (Pydantic) for the site model, research brief, events, findings.
- Claude API reference — read via the `claude-api` skill before wiring the model.

**Supporting engineering:**
- Python `asyncio` for parallel Steel sessions in waves under the 10-session cap.
- Secrets in `.env`, gitignored.
- FastAPI + React + Tailwind for the journey map, live grid, score card, finding detail.

---

## Decisions & open items
- **Team:** 4 devs, parallel work (module split in the design doc). ✅
- **Spine:** agent-readiness + evidence-backed research (red-team and synthetic-consumer versions rejected). ✅
- **Full design:** `docs/superpowers/specs/2026-09-12-crucible-design.md`
- At the event: confirm Steel Computer beta scope at the 1:00 PM workshop (fix loop is stretch-only); secure elevated concurrency / proxy credits from the Steel booth; pick the real demo target from 2–3 pre-scouted candidates.
