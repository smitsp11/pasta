# Iris — Flow, pages and frames

This is the agreed product flow and what every screen must achieve. It is written for the whole team: each stage says **what it does**, **what the user sees**, and **why it exists**, with a tag telling you whether it is a Steel feature we are showcasing, a decision we made, or an LLM call.

**One line:** companies pay for case studies and user research to learn how customers behave on their site. Iris automates that: it researches the company's real customers, sends a swarm of evidence-backed AI personas through the live site on real cloud browsers, and hands back the issues and flags for the company to fix.

**The foil:** DataDab's Agent Audit sends one generic agent to your homepage with three fixed B2B tasks and emails you a PDF. Iris learns who your customers are, sends eight of them on the devices, countries and identities those customers actually use, and shows you the frame where each one gave up.

### Tags used below

| Tag | Meaning |
|---|---|
| `STEEL` | A Steel primitive. This is what the sponsor judges are scoring; keep it visible in the UI. |
| `DECISION` | Something we chose for the demo or the pitch. Could be done differently; this is the agreed way. |
| `LLM` | A model call (Claude by default). Costs tokens; keep the count low. |
| `OURS` | Code we write: crawler, scorer, UI. |

---

## The flow

```
URL (+ optional context)
        │
   ┌────┴────────────────┐            PARALLEL
   ▼                     ▼
[A] Consumer          [B] Site analysis
    research              zero-context explore
   │                     │
   └────────┬────────────┘
            ▼
[C] TEST BRIEF  · 8 personas + stress-test list
            │
            ▼
[D] THE SWARM  · 8 Steel sessions in a live grid
            │
            ▼
[E] FINDINGS   · stall → cause → who → evidence
            │
            ▼
[F] REPORT     · issues & flags for the company
```

Five screens, in the same order: **Input → Learning (split screen) → Test brief → Swarm → Report.** Nothing appears in the UI that is not a stage in this diagram. The UI *is* the narration.

---

## Screen 1 — Input

**What it does.** Takes the company URL. Nothing else.

**What the user sees.** One headline, one field, one button. Nothing else.

**Why.**
- `DECISION` Zero-context is the promise. Nothing else is asked for, because the pitch is that we replace the case study, not that we make the company fill in a brief.
- `DECISION` A hint for the stage fallback exists only as a URL parameter (`?hint=`). It is never a visible field; the screen stays minimal.

<details><summary>Why not ask for logins or a task list?</summary>

Asking for tasks would make us DataDab with more steps. Asking for logins is out of scope for 24 hours and adds a credential-handling story we don't want on stage. Everything the personas do is on the public site and stops before payment.
</details>

---

## Screen 2 — Learning (split screen, both halves live)

Two agents run **in parallel** the moment the URL is submitted. The screen is split down the middle so the audience sees both working.

### Left half — [A] Consumer research

**What it does.** A research agent gathers evidence about the company's real customers: who they are, what device and country they shop from, what they complain about, where they drop off. Sources: the site's own help centre and FAQ, review sites, Reddit, app-store reviews, and one competitor for contrast. Output is an **evidence pack**: quotes with links, plus a short list of segments.

**What the user sees.** Sources appearing one by one as cards ("Trustpilot · 3 quotes", "Reddit r/… · 2 threads"), each with a quote. A running count: *"14 pieces of evidence from 5 sources."*

**Why.**
- `DECISION` This is the stage that replaces the paid case study. It has to be visible, and it has to show *real* quotes, because that is the difference between us and tools that imagine users.
- `STEEL` Each source is opened in its own Steel session. Review sites and Reddit are bot-hostile and geo-varying, so plain HTTP scraping fails; Steel's stealth and proxies are what make this stage work at all, and the fan-out shows fleet-scale sessions.
- `LLM` One call at the end turns the raw pages into the evidence pack (segments + quotes). The crawling itself is not an LLM loop.

<details><summary>Bounds (so it can't run away on stage)</summary>

At most 6 sources, 4 minutes wall clock, hard stop. A source that yields nothing is dropped, not retried. For the demo targets the evidence pack is also cached, and the screen replays it fast if we're in fallback mode.
</details>

<details><summary>What research is allowed to claim</summary>

Research supplies **what to test**, never **the answer**. It produces hypotheses ("mobile shoppers in Canada report checkout resets") that the swarm then tests. A finding is only reported if an agent actually reproduced it. This is the rule that keeps the report honest when a judge asks "how do you know that's real?"
</details>

### Right half — [B] Site analysis

**What it does.** A zero-context explorer maps the live site to find out **what is possible on it**: the key journeys (find a product, add to cart, reach checkout, book a demo, sign up), forms, login walls, the mobile layout. Output is a **site map**: what the site is, who it's for, and 3–5 executable journeys.

**What the user sees.** A live Steel viewer of the explorer clicking through the site, and beside it the site map building up: brand, category, and journey cards appearing as they're discovered.

**Why.**
- `OURS` The explorer is a read-only breadth-first crawler with a stopping rule (stop when two pages in a row add nothing new, or at 25 pages, or at 3 minutes). It only follows links, never submits forms, never clicks buy/delete/cancel. That is what makes it safe to point at a stranger's site on stage.
- `STEEL` It runs in a Steel session so the audience can watch it in the embedded live viewer. Off stage it can run on a local browser and spend no credits.
- `LLM` One call turns the crawled page summaries into the site map with concrete journey goals ("on /collections/all, open the first product, add it to the cart, open the cart page").

<details><summary>Why the site analysis is not an agent</summary>

Crawling links is deterministic. An agent here would be slower, cost tokens per page, and might click something destructive. We save the agents for the swarm, where being an agent is the point.
</details>

---

## Screen 3 — Test brief

**What it does.** Consolidates the evidence pack and the site map into the plan for the swarm: **8 personas** and a **stress-test list**.

Each persona is:
- a **segment** from the research ("returning bargain hunter", "first-time mobile shopper in Canada")
- a **device**, a **country**, and an **identity** (new or returning)
- a **goal** on this site, taken from the site map's journeys
- the **evidence** that justifies them: the quote or stat that says this kind of customer exists and struggles here

The stress-test list is the set of things to probe, each with a why and a source: "checkout on mobile — 3 reviewers report it resets", "coupon field — Reddit thread says it rejects valid codes".

**What the user sees.** Eight persona cards in a grid. Each card shows the segment name, three chips (device · country · identity), the goal in one sentence, and the evidence quote underneath in a muted box. Two of the cards are visually linked as a **matched pair**. Below the grid, the stress-test list.

**Why.**
- `DECISION` This is the screen that sells the vision. It is the case study, generated, with its sources showing. Give it room.
- `LLM` One call produces the brief from the evidence pack + site map. It must output 8 personas with the fields above, and must pick entry URLs that were actually crawled.
- `DECISION` Two of the eight are a **matched pair**: identical except for one variable (for example the same shopper on desktop and on mobile). This guarantees at least one flag in the report is *provably* attributable ("fails only on mobile") rather than narrated. It costs nothing.

<details><summary>Device — what it means and why it's Steel</summary>

`STEEL` **Mobile mode.** Steel can start a session as a real mobile device: mobile viewport, touch events and a full mobile fingerprint, not a desktop browser with a spoofed user-agent string. Sites serve their actual mobile layout, hamburger menus and all. A persona marked *mobile* runs in a session created with `device_config={"device": "mobile"}`. This is one of the three things you cannot fake from a laptop.
</details>

<details><summary>Country — what it means and why it's Steel</summary>

`STEEL` **Residential geo proxy.** Steel routes a session through a real residential IP in a chosen country (`use_proxy={"geolocation": {"country": "CA"}}`). Sites then show that country's currency, shipping rules, consent banners or blocks. A persona marked *Canada* really arrives from Canada. Every persona gets a proxy of its own country, including the US ones, so country is the only thing that differs between two personas, never "proxy vs no proxy". Residential proxies cost money on Steel; unlocking them (a $10 balance) is a pre-event checklist item.
</details>

<details><summary>Identity — new vs returning, and why it's Steel</summary>

`STEEL` **Persistent Profiles.** A Steel Profile is a browser identity that keeps cookies, storage and history across sessions. A *returning* persona is created from a profile that already visited the site (we warm it up with a first visit, then launch the persona with that `profile_id`), so it arrives with the cart, consent choice and cookies a real repeat visitor would have. A *new* persona starts with a fresh profile. Sites often behave differently for the two (personalisation, saved carts, consent already given), which is exactly the kind of difference the research surfaces.
</details>

<details><summary>Engine — DOM agent vs vision agent (optional axis)</summary>

`STEEL` `DECISION` Two kinds of agent exist: DOM-based (reads the page structure, e.g. Browser Use) and vision-based (looks at screenshots and clicks coordinates, e.g. Claude computer use). Both run on the same Steel session through Steel's input API. DataDab uses one vision agent. If we ship both, a persona can be marked with an engine, and a stall that hits *every* engine is flagged as the site's fault, not the agent's. This is a should-have, not part of the MVP.
</details>

<details><summary>Why 8</summary>

`DECISION` Eight fits one wave under Steel's free-tier cap of 10 concurrent sessions, with two spare for retries, and eight cards fit on one screen. It is not a magic number; it is the largest swarm we can show live without batching.
</details>

---

## Screen 4 — The swarm

**What it does.** Runs the eight personas at once. Each persona becomes one Steel session with its device, country and profile applied, and an agent runs the persona's goal inside it, narrating what it tries.

**What the user sees.** A grid of eight live browser viewers, one per persona, each captioned with the persona name, its three chips, and a running line of narration ("looking for the cart… the ＋ button has no label… trying again"). Cards turn green on completion, red on a stall, grey if our tooling failed. A header line: *"6 running · 1 done · 1 stalled."*

**Why.**
- `STEEL` **Sessions API + concurrency.** Eight cloud browsers at once. This is the fleet-scale moment.
- `STEEL` **Live viewer embed.** Each card is Steel's embeddable live view of that session (`debug_url`, watch-only). The audience is watching real browsers, not a screen recording.
- `STEEL` Mobile mode, geo proxy and Profile are applied per card, as chosen in the test brief.
- `LLM` The agent's brain. Each step, the agent sees the page and decides what to click. This is the token-heavy part of the product; step caps and a per-session time budget keep it bounded.
- `DECISION` Agents **never submit payment**, never create accounts, never delete. A goal that reaches checkout stops there and counts as complete.

<details><summary>What the narration is and where it comes from</summary>

The agent framework emits one event per step (action taken, what it observed). The caption shows the latest event. A stall ends with the agent's own one-line reason ("overlay keeps intercepting clicks"), which becomes part of the finding. Narration is not a separate LLM call.
</details>

<details><summary>Stall vs tooling error, and why the distinction is on screen</summary>

`DECISION` A **stall** is the site's problem: the agent could not finish. A **harness error** is *our* problem: the session failed to start, the model timed out, the browser disconnected. Harness errors are shown grey and excluded from every score, so our flakiness never becomes a flag against the company. Stalled runs are retried once before they count. Judges will ask "was that the site or your bot?"; this is the answer.
</details>

---

## Screen 5 — Report: issues & flags

**What it does.** Turns the swarm's results into the deliverable: a ranked list of issues for the company to fix, each with who it affects, the evidence, and a proposed fix.

For every stall the findings engine works out:
1. **Cause**, from a fixed list (cookie wall, CAPTCHA, hidden navigation, icon-only control, ambiguous button, geo-block, infinite scroll, login wall, layout shift, timeout, other). Deterministic checks on the final page first (is there a consent overlay? a CAPTCHA frame? a login form?), then one LLM call for the rest.
2. **Who it affects**: which personas hit it, and therefore which customer segments.
3. **Evidence**: the research quote that predicted it (if any) and the session replay frozen at the stall step.
4. **Attribution**, for the matched pair: if one of the pair completed and the other stalled, the flag says exactly which variable caused it.
5. **A proposed fix**, concrete and naming the element ("the cart button has no accessible name; add `aria-label="Cart"`").

**What the user sees.** A headline score (0–100 readiness), then flags ranked by how many customers they touch. Clicking a flag opens: the description, the affected persona chips, the customer quote on the left, the replay on the right at the stall frame, the fix in a green box. A muted footer line lists any tooling errors that were excluded.

**Why.**
- `DECISION` Ranked by customers affected, not by technical severity. The company is buying "what should I fix first for my actual customers", which is the case-study outcome we're replacing.
- `STEEL` **Session replay + Agent Traces.** Every finding links to Steel's recording of that session, and the trace timeline gives the step index, so the replay opens at the moment of failure. Screenshot trails are what DataDab offers; a replay you can scrub is what Steel gives us.
- `DECISION` Quote and replay side by side. A finding that has both is the strongest evidence a site owner can get: a real customer said it, and here is it happening.
- `OURS` The findings engine is pure code plus one LLM call for unclear stalls; it is unit-tested on fixtures so the report is reproducible.

<details><summary>Corroborated vs agent-readiness flags</summary>

`DECISION` A flag is **corroborated** if the research predicted it and the swarm reproduced it. Otherwise it is an **agent-readiness** flag: the site stalls *agents* specifically, which is real too, because agents are the population that hit it. Both are shown; corroborated ones rank higher because they carry a human quote.
</details>

<details><summary>Stretch: the fix loop</summary>

`STEEL` **Steel Computer (beta).** On our own self-hosted demo store, a Steel Computer (a full cloud machine with a terminal and files) clones the store, applies the proposed fix, restarts it, and re-runs the failing persona. The score climbs live. This is the $500 bonus and the closing moment if the beta is usable; it is not part of the MVP.
</details>

---

## What the UI must achieve

- A stranger can paste a URL and, without anyone explaining, watch research and site map build, see eight personas with their evidence, watch the swarm, and read the flags.
- Every screen visibly maps to a stage of the diagram; no view exists outside the flow.
- Steel is on screen at every stage after input: live viewers on screens 2 and 4, device/country/identity chips on screens 3 and 4, replay on screen 5.
- The report's first flag has a quote and a replay; the matched-pair flag says "fails only on ___".
- Nothing spins for more than 5 seconds without a line of text saying what is happening.
- A cached mode replays a recorded run through all five screens without touching Steel, for the stage fallback.

## Demo targets

- **Headline:** a real e-commerce site, scouted in advance, with public reviews to research and an obvious cookie banner. Research and site map are cached for it; the swarm runs live.
- **Fix loop:** our own small store with three planted, one-line-fixable traps, used only for the stretch.

Neither alone works: only our store looks staged; only a live site is a coin flip.
