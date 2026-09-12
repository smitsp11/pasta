# Crucible — concept, prior art & requirements

> Working title: **Crucible** (a severe test that reveals what something is made of). Alternatives: *Populace, Proving Ground, Colosseum, Cohort*.

Hackathon: Battle of the Schools — **Steel.dev Web Agents track**. Goal: 1st place (+ possibly the $500 Steel Computer bonus). Stack: **Python**.

---

## 1. The pitch (simplified)

**One-liner:**
> Point Crucible at any website and it unleashes a population of AI users on it — some acting like real customers, some acting like adversaries — then hands you a report of exactly where your product breaks, with a video replay of each failure.

**The 30-second version:**
Real products are tested by a handful of engineers on their own laptops, in one language, from one country, on one clean browser. Real *users* are thousands of different people, on different devices, in different countries, some confused, some malicious. Crucible closes that gap: it spins up a swarm of AI "users" in real cloud browsers (via Steel), each a distinct **persona** — a returning mobile shopper in Germany, a first-timer in Brazil, a fraudster probing your checkout — and turns them loose on your live product at the same time. You watch them work in a live grid, and when they get stuck, abandon, or break something, Crucible catches it and shows you the exact moment it happened.

**Product spine (decided): red-team + realistic-crowd baseline.**
Crucible is primarily a **red-teaming / vulnerability product**: adversarial agents probe the product for abuse and breakage (promo/coupon farming, signup & bot abuse, broken auth/access control, rate-limit gaps) and produce a findings report with jump-to-failure replays. The **cooperative personas play a supporting role** — they form the realistic "normal traffic" the attackers hide inside, and they showcase Steel's geo + persistent-identity diversity. The headline question this frames: **does your product catch the fraudster without breaking for the grandma?** You can't answer that without both populations in the same run.

**Why it's not just "AI QA":**
Two things make it new and make Steel irreplaceable:
1. **Real diversity, not imagined.** Personas run as **persistent identities** (they remember past visits) across **real geographies** (real residential IPs in different countries) and **devices**. You cannot fake "a returning user in Germany on mobile" from a laptop — that needs Steel's Profiles + geo proxies.
2. **Adversaries, not just customers.** Alongside cooperative personas, adversarial agents probe for abuse and breakage (signup spam, promo-code abuse, broken auth, rate limits). This "agents vs. product" framing is the archetype that won the YC Web Agents hackathon (*Browser Brawl*).

**The demo moment:** run it live on the *judges' own* product and watch a population of AI users find its cracks in real time.

---

## 2. Similar products / prior art (and how we differ)

| Name | What it is | How Crucible differs |
|---|---|---|
| **Browser Brawl** (YC Web Agents Hackathon winner) | Two agents on a live site: an attacker completes a task, a defender injects JS to block it; emits traces as fine-tuning data. [site](https://www.browser-brawl.com/) · [repo](https://github.com/RichardHruby/browser-brawl) | Same adversarial/self-play DNA, but aimed at **testing a real product** (not an abstract duel) and paired with **cooperative geo/persona users** + a usable report. |
| **UXAgent** (Amazon, CHI 2025) | LLM agents as simulated usability-test participants; persona generator + browser connector; thousands of simulated users. [paper](https://arxiv.org/abs/2504.09407) | UXAgent uses a **plain Chrome connector** — no real geography, no persistent identity, no scale infra, no adversaries. We add all four via Steel. |
| **Synthetic Users** (syntheticusers.io) | Commercial "synthetic user research" — mostly LLM *imagining* users / interviews; some browser onboarding runs. | We drive **real browsers at fleet scale across real geographies**, not an LLM imagining a user. |
| **Generative Agents / "Smallville"** + **AI Town** | 25 LLM agents living in a simulated town (memory, planning, emergent behavior). [paper](https://arxiv.org/pdf/2304.03442) · [repo](https://github.com/joonspk-research/generative_agents) | The "agent society" idea, but ours acts **on a real product on the live web**, producing actionable QA/UX/abuse findings. |
| **WebArena / WebVoyager** | Benchmarks for web agents on (mostly) sandboxed sites. [WebArena](https://github.com/web-arena-x/webarena) | Benchmarks *rate agents*; we use agents to *rate a product*. |
| **Browser Use `qa-use`** | Open-source "QA-test your site with an agent." | The commoditized baseline we must out-class — via geo + persistent identity + adversarial + replay report. |
| **HackWorld** | Research: evaluating computer-use agents at exploiting web-app vulnerabilities. [paper](https://arxiv.org/html/2510.12200v1) | Direct inspiration for the **adversarial** half; we productize it into a report. |

**Positioning in one line:** *UXAgent's synthetic users + Browser Brawl's adversaries, run on Steel's real-world infrastructure (geo + persistent identity + scale + replay).*

---

## 3. Requirements to read up on

Two lists. **A** = vocabulary we must be able to *say* to explain/pitch the idea. **B** = concepts/tech we must *learn* to build it.

### A. Vocabulary to explain the idea

- **Synthetic / simulated user** — an AI agent standing in for a real human user.
- **Persona** — a defined user profile (goals, traits, device, location, patience) driving one agent's behavior.
- **Agent** — an LLM-driven loop that perceives a page, decides an action, and acts (repeat).
- **Cooperative vs. adversarial agent** — one tries to *use* the product normally; the other tries to *abuse/break* it.
- **Self-play / agent arena** — agents interacting/competing in a shared environment (the winning hackathon archetype).
- **Red-teaming** — deliberately attacking a system to find weaknesses before real attackers do.
- **Conversion funnel** — the steps a user passes through (land → signup → checkout); each step loses some users.
- **Drop-off / abandonment** — where and why users quit the funnel.
- **UX / localization (i18n) conformance** — does the product behave correctly per language/currency/region/consent law.
- **Dark pattern** — a deceptive UI trick (hidden costs, forced continuity); something adversarial agents can surface.
- **Session replay** — a video/timeline reconstruction of what happened in a browser session.
- **Jump-to-failure** — linking a detected failure straight to that moment in the replay.
- **Eval / benchmark & traces** — structured records of agent behavior, usable to measure or to fine-tune models (judges love this).
- **Digital twin** — a persistent simulated stand-in for a real returning user.

### B. Tech to learn to build it

**Steel (the core — read these first):**
- Intro & overview — https://docs.steel.dev/overview/intro-to-steel
- Sessions API (create/connect/release, the atomic unit) — https://docs.steel.dev/overview/sessions-api/overview
- Session lifecycle & limits (15-min free cap, timeouts) — https://docs.steel.dev/overview/sessions-api/session-lifecycle
- Session configuration (viewport, device, proxy flags) — https://docs.steel.dev/overview/sessions-api/configuration
- **Persistent Profiles** (returning identities) — https://docs.steel.dev/overview/profiles-api/overview
- **Residential proxies + geolocation** (per-country IPs) — https://docs.steel.dev/overview/stealth/proxies
- **Live session embed** (interactive viewer for the grid) — https://docs.steel.dev/overview/sessions-api/embed-sessions/live-sessions
- **Agent Traces** (jump-to-failure replay) — https://docs.steel.dev/overview/agent-traces/overview
- Credentials API (logged-in personas without leaking secrets) — https://docs.steel.dev/overview/credentials-api/overview
- Python + Playwright quickstart — https://docs.steel.dev/integrations/playwright · Cookbook — https://docs.steel.dev/cookbook
- (Optional/bonus) Steel Computer beta — https://computers-preview.apidocumentation.com · activate: https://app.steel.dev/computer-access

**Browser automation:**
- **Playwright for Python** (driving the page) — https://playwright.dev/python/
- **CDP** (Chrome DevTools Protocol) & `connect_over_cdp` — how Playwright attaches to a remote Steel browser.
- DOM-based control (selectors, `get_by_role`) vs. **vision/computer-use** control (screenshot → click coordinates) — pick per agent.

**LLM agents:**
- The **agent loop**: observe (page/DOM/screenshot) → decide → act → repeat.
- **Tool / function calling** and **structured output** (getting reliable actions + JSON findings out of an LLM).
- **DOM-based agent frameworks** to consider: Browser Use, Stagehand (both run on Steel) — vs. rolling our own loop.
- **Computer-use** models (Claude/OpenAI/Gemini) — screenshot-driven action; Steel has `sessions.computer()` + recipes.
- **Persona prompting** — system prompts that make each agent behave like its persona (impatient, confused, malicious).
- Claude API reference (models/pricing/tool use) — read via the `claude-api` skill before wiring the model.

**Supporting engineering:**
- **Python `asyncio`** / concurrency — running many Steel sessions in parallel (respect the 10-session free cap; batch in waves).
- **Secrets** — `STEEL_API_KEY` + model keys in `.env`, `.gitignore`'d (Steel's guide is explicit about this).
- **A thin UI** to show the live grid + funnel + report — likely **FastAPI + a simple frontend** (or Streamlit for speed); embed Steel's live viewer iframes.
- **Findings data model** — per-agent event log (step, action, screenshot/trace ref, outcome) → aggregate into funnel + report.

---

## Decisions & open items
- **Team:** 4 devs, parallel work (see design doc for module split). ✅
- **Demo balance:** red-team spine + realistic-crowd baseline. ✅
- **Full design:** `docs/superpowers/specs/2026-09-12-crucible-design.md`
- Still to do at the event: confirm Steel Computer beta scope at the 1:00 PM workshop (only if we chase the $500 bonus); secure elevated concurrency / proxy credits from the Steel booth.
