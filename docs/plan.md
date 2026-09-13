# Crucible — Build plan and work split (validated)

Companion to `docs/concept.md` (pitch) and `docs/superpowers/specs/2026-09-12-crucible-design.md` (design v3). This doc answers one question: **who builds what, in what order, and how the pieces meet.**

Hackathon window: 24h, Sept 12–13 2026. Team of 4: **Dev A = Jinay**, Devs B, C, D.

Target workload split: **A 40% · B 30% · C 15% · D 15%.** Section 8 shows the scope-point estimate that backs this.

---

## 1. The critical path (read this first)

Everything live depends on three things, and one person owns all three so there is no handoff on the critical path:

1. **The Steel session wrapper** (`crucible/steel.py`): create → connect over CDP → release, with mobile / profile / geo options.
2. **The engine adapters** (`crucible/engines/`): Browser Use first, then Claude computer use, then OpenAI computer use.
3. **The Runner** (`crucible/runner/`): the population matrix, wave scheduling under the 10-session cap, profile warm-up ordering, retries, harness-error isolation.

That is Dev A's seat. It is the only module that cannot be developed on fixtures, so every iteration burns Steel sessions and model tokens. Dev A also owns the Steel Computer fix loop as stretch, because it is the same skill set: Steel primitives, session plumbing, and re-running the matrix.

Dev B owns everything that **feeds** the core and **wraps** it: the Explore stage, both test targets, the orchestrator, and the FastAPI layer. Dev C owns the Scorer, pure Python on fixtures. Dev D owns the React front end and the Devpost package.

```
hour 0      0:30            3:30                 7:00              10:00            14:00           18:00     24:00
 |-schemas-|  Steel wrapper  |  Runner + matrix   |  Claude CU       |  stretch:      |                |
 |          |  + Browser Use |  (A)               |  (A)             |  OpenAI CU or  |                |
 |          |  (A) → M1      |                    |                  |  fix loop (A)  |                |
 |          |  API stub → mock site → Explore (B) ▶ orchestrator (B) ▶ demo store, cache, dry-run (B) ▶| demo   |
 |          |  Scorer on fixtures (C) ────────────────────────────────▶ real-stream tuning (C) ────────| freeze |
 |          |  React views on fixtures (D) ───────────────────────────▶ wire, polish, Devpost (D) ─────|        |
```

**Design choice that makes this split work:** Explore does **not** use an agent framework. It is a Playwright breadth-first crawler with a safety allowlist, plus one LLM call over the collected page summaries to produce the `SiteModel`. B never waits on A's engine adapters, and Explore is deterministic enough to cache and replay on stage.

---

## 2. Contracts locked in the first 30 minutes (all four together)

Do these in one room before anyone opens a module. Every cross-dev dependency below is a **signature**, not a working implementation, so nobody blocks on anyone after 0:30.

1. **`crucible/schemas.py`** — Pydantic models exactly as in the design doc: `SiteModel`, `Journey`, `Config`, `RunEvent`, `Finding`, `ScoreCard`. Add `RunResult` (terminal wrapper: `run_id`, `config`, `journey_id`, `session_id`, `outcome`, `events: [RunEvent]`, `replay_url`, `final_screenshot_ref`) and `SessionStarted` (`session_id`, `viewer_url`, `config`, `journey_id`).
2. **Engine interface** (`crucible/engines/base.py`, owner A):
   ```python
   class Engine(Protocol):
       name: str
       async def run_journey(self, session: SteelSession, journey: Journey, cfg: Config, step_cap: int) -> AsyncIterator[RunEvent]: ...
   ```
3. **Runner interface** (`crucible/runner/__init__.py`, owner A):
   ```python
   async def run_matrix(site: SiteModel, configs: list[Config], engines: dict[str, Engine]) -> AsyncIterator[RunEvent | SessionStarted | RunResult]: ...
   ```
4. **Scorer interface** (`crucible/scorer/__init__.py`, owner C):
   ```python
   async def score(site: SiteModel, results: list[RunResult]) -> tuple[ScoreCard, list[Finding]]: ...
   ```
5. **Explore interface** (`crucible/explore/__init__.py`, owner B):
   ```python
   async def explore(url: str, hint: str | None = None) -> SiteModel: ...
   ```
6. **Fixtures** (`fixtures/`): one hand-written example of each schema, plus two full `RunResult`s (one `completed`, one `stalled` on a cookie wall), plus one full canned pipeline run (`fixtures/demo_run.json`). Mock data for C and D, golden tests for the Scorer.
7. **API contract** (`docs/api.md`, owner B):
   - `POST /runs {url, hint?, cached_site_model?}` → `{run_id}`
   - `GET /runs/{id}` → `{stage, site_model?, scorecard?, findings?}`
   - `WS /runs/{id}/events` → stream of `RunEvent`, `SessionStarted`, `{type: "stage", name}`
   - `GET /fixtures/demo` → `fixtures/demo_run.json`
8. **Repo layout** and the git rule: one branch per person, merge to `main` at least every 3 hours, `main` must always import and pass `pytest tests/scorer`.

```
crucible/
  schemas.py          # contract (all four; changes need everyone in the room)
  steel.py            # A: session lifecycle + mobile/profile/geo config
  engines/            # A: base.py, browser_use.py, claude_cu.py, openai_cu.py
  runner/             # A: matrix, waves, profile warm-up, retries, event bus
  fixloop/            # A (stretch): Steel Computer patch-and-rerun
  explore/            # B: Playwright BFS crawler + LLM → SiteModel
  orchestrator.py     # B: explore → run_matrix → score, one entry point
  api/                # B: FastAPI app + websocket
  scorer/             # C: classify, attribute, score, fixes, static contrast
web/                  # D: React + Tailwind
targets/
  mock_site/          # B: local static site with known traps (no Steel credits)
  demo_store/         # B: self-hosted storefront with 3 injected traps
  cache/              # B: cached SiteModel JSON for demo targets
fixtures/             # everyone
tests/                # C first (scorer), then whoever
```

---

## 3. Per-person ownership

### Dev A (Jinay) — Steel core: sessions, engines, Runner, fix loop  (~40%)

| Hours | Deliverable | Depends on |
|---|---|---|
| 0:30–2:00 | `steel.py`: `SteelSession` async context manager. Create with `device_config={"device": "mobile"}`, `persist_profile=True` / `profile_id=`, `use_proxy={"geolocation": {"country": ...}}`, `timeout=12min`; connect Playwright over CDP; **idempotent release** in `finally`, safe to call twice; expose `viewer_url`, `replay_url`, `session_id`. Ship this first. | Steel key, proxies unlocked |
| 2:00–3:30 | `engines/browser_use.py`: Browser Use attached to the Steel CDP session, one `RunEvent` per agent step, terminal outcome from the agent's done/fail signal, hard step cap. **M1 at 3:30: one journey on one Steel session, events print, session released, replay URL opens.** Use the real target's landing page for M1 if B's mock site is not up yet. | `steel.py` |
| 3:30–7:00 | `runner/`: build the matrix from `SiteModel.journeys` × configs; wave scheduler with `asyncio.Semaphore(10)`; **ordering constraint: the baseline run for a journey is created with `persist_profile=True` and must finish before the `returning` variant starts with its `profile_id`**; retry a `stalled` run once; harness-error detection (session create failure, engine exception, model timeout, CDP disconnect → `harness_error`, never `stalled`); step caps enforced in the runner, not trusted to engines; yields `SessionStarted` before the first `RunEvent` of each session, `RunResult` at the end | Browser Use adapter, B's mock site |
| 7:00–8:00 | Pair with B: orchestrator calls `run_matrix`; 2-config matrix on the mock site end to end | B |
| 8:00–11:00 | `engines/claude_cu.py`: Claude computer use on the same Steel session via the Steel cookbook recipe. Screenshot → model → action loop, mapped to the same `RunEvent` shape. Per-step token budget, lower step cap than Browser Use. Read the `claude-api` skill before wiring. **Unlocks `engine` attribution and `engine_consensus`.** | Runner stable |
| 11:00–14:00 | Integration on the real target: proxy countries that actually work (test CA, DE, GB; keep two), mobile mode renders the mobile layout, returning profile actually carries cookies (verify in the replay), concurrency negotiated with the Steel booth. Confirm whether the replay embed accepts a seek param and tell D. Watch the dashboard for leaked sessions | B's target pick |
| 14:00–18:00 | **Stretch, pick one at 14:00:** (a) `engines/openai_cu.py`, third engine, if Claude CU landed by 11:00; or (b) `fixloop/`: on a Steel Computer, clone B's demo store, apply the proposed patch for one finding, restart the server, re-run that journey × config through `run_matrix`, emit the new score. Choose (b) only if the 1 PM workshop confirmed Computer access and B's store is up by 10:00. If neither is feasible: hardening below | Steel Computer, B's demo store |
| 17:00–18:00 | Hardening: global run timeout, graceful cancel that releases every session, wave sizing that finishes the MVP matrix inside 4 minutes on stage | — |
| 18:00–24:00 | Runs the live part of every rehearsal; owns the Steel credit budget and the call to fall back to cached mode | — |

**Done when:** the MVP matrix (2 journeys × baseline + mobile + returning + one country = 8 sessions) runs on the real target inside one wave with no leaked sessions; Browser Use completes the baseline journey 2 of 3 tries; Claude CU completes it at least once; a killed run releases everything.

### Dev B — Explore, targets, orchestrator, API, integration lead  (~30%)

| Hours | Deliverable | Depends on |
|---|---|---|
| 0:30–1:30 | `api/` **stub**: FastAPI implementing `docs/api.md` against `fixtures/demo_run.json` only. The websocket replays the fixture stream with small delays. This is what D builds against from hour 1:30 | fixtures |
| 1:30–3:00 | `targets/mock_site/`: static local site (`python -m http.server`) with a cookie overlay, an icon-only cart button, a hamburger-only mobile nav, product list, cart, checkout. A and B develop against this | — |
| 3:00–7:00 | `explore/`: Playwright BFS crawler from the landing page. Per page: title, headings, nav links, buttons, forms, classified action types. Safety allowlist: click links, nav, tabs, menus, scroll; type only into search-like inputs; **never** submit a form whose button or nearby text matches purchase / delete / cancel / subscribe / unsubscribe / confirm; never type into password or payment fields. Stopping rule: 2 consecutive pages adding no new action types, or 25 pages, or 3 minutes. Then one LLM call over the page summaries → `SiteModel` with top 3 journeys with specific, executable goals ("on /collections/all, add the first product to the cart and open the cart page") | schemas |
| 7:00–8:00 | `orchestrator.py`: `run_pipeline(url, hint, cached_site_model=None)` runs `explore` → `run_matrix` → `score`, emitting `{type: "stage"}` markers. Swap the API stub to call it. Pair with A on the first end-to-end run on the mock site | A, C signatures |
| 8:00–10:00 | Scout 3 real e-commerce candidates (Shopify-style, cookie modal, decent Cloudflare static score, no login wall on product pages). Record each isitagentready.com score. Pick one, tell the team. *(Moved from hour 0:30 in the previous draft: the target is not needed until A's integration at 11:00, and this frees C.)* | — |
| 8:00–14:00 | **Integration lead.** Owns `main`, runs the M3 and M4 checks, chases whoever is blocking. Explore quality on the real target: `timeout` on baseline means the journey goal is under-specified, fix it here first | everyone |
| 10:00–13:00 | `targets/demo_store/`: small self-hosted storefront (Next.js commerce template or a 200-line Flask store) with 3 injected traps: icon-only cart button, consent modal with no accessible name, hamburger-only mobile nav. Reachable by Steel via a tunnel. Needed by A's fix loop at 14:00 and as the second demo target | — |
| 14:00–18:00 | Cache Explore for both demo targets into `targets/cache/`; user-hint shortcut; `--dry-run` flag on the orchestrator that replays a recorded run through the whole pipeline so D can rehearse without Steel | — |
| 18:00–24:00 | Rehearsals: plays the hostile judge; keeps the fallback list current | — |

**Done when:** Explore produces a usable `SiteModel` for the real target in under 3 minutes, Browser Use completes the baseline on its journey goals, both demo targets have cached site models, and the API forwards real pipeline events to D's UI.

### Dev C — Scorer  (~15%)

| Hours | Deliverable | Depends on |
|---|---|---|
| 0:30–1:30 | Write the fixtures with everyone, then own `tests/scorer/` from the first line | schemas |
| 1:30–5:30 | `scorer/classify.py`: deterministic classifiers first (URL unchanged after N actions → `timeout`; overlay with consent text intercepting clicks → `cookie_wall`; CAPTCHA iframe → `captcha`; proxy block page → `geo_block`), then an LLM pass over the final screenshot + last 5 events for the rest, returning `category` + one-line description. Unit tests against fixtures throughout | fixtures |
| 5:30–7:00 | `scorer/attribute.py`: variant stall vs. baseline → `attributed_to`; stall in baseline → `site`; same category across every engine → `engine_consensus`. `scorer/score.py`: per-journey weighted completion (baseline 2×, variants 1×), overall mean, harness errors excluded and reported separately | — |
| 7:00–8:30 | `scorer/static.py`: fetch the Cloudflare static score; `None` on any failure. `scorer/fixes.py`: proposed-fix text per category + offending element. Wire `score()` entry point | — |
| 8:30–10:00 | Prior-art slide (static vs. single-agent vs. controlled population) and the failure-taxonomy card for the Devpost | — |
| 10:00–14:00 | Integration: run `score()` on real `RunResult`s from A, fix classifier gaps, confirm every `Finding` carries `session_id` + `step_index` that lands on the stall frame | A |
| 14:00–18:00 | Taxonomy hardening on rehearsal data; second pass on fix text so each one names the offending element | — |
| 18:00–24:00 | Rehearsals: reads every finding aloud as a judge would; flags any that are not defensible | — |

**Done when:** `pytest tests/scorer` passes on fixtures, and on the real target at least one finding reads "fails only on mobile" (or another single variable) with a replay that shows the stall.

### Dev D — Front end + Devpost  (~15%)

| Hours | Deliverable | Depends on |
|---|---|---|
| 0:30–1:30 | Vite + React + Tailwind scaffold; load `fixtures/demo_run.json` statically until B's API stub is up at 1:30 | fixtures |
| 1:30–7:00 | Four views on the API stub: **journey map** (site model + 3 journeys), **live grid** (one card per session with embedded Steel live viewer iframe, config label, current step), **score card** (ours beside the Cloudflare static score, per-journey rows, harness errors in a muted side panel), **finding detail** (category, attribution badge, `engine_consensus` badge, proposed fix, replay iframe seeked to `step_index`, final screenshot fallback) | B's API stub |
| 7:00–9:00 | Switch to the real websocket: live grid mounts a viewer as soon as `SessionStarted` arrives; score card updates on the Score stage marker | B's orchestrator |
| 9:00–14:00 | Integration on the real target: viewers render, findings link to the right replay frame, no view breaks on a `harness_error` | everyone |
| 14:00–18:00 | Polish for the demo script: the "85 vs. ours" contrast is the biggest thing on screen; attribution badges readable from the back of the room; no spinner longer than 5s without a status line; `?demo=cached` flag that points the UI at B's dry-run | B's dry-run |
| 18:00–24:00 | Rehearsal driver, Devpost writeup, screenshots and the 3-minute video | — |

**Done when:** a stranger can paste a URL and, without anyone explaining, see the matrix run, the score land, and click into a stall.

---

## 4. Milestones (checkpoints where everyone syncs)

| Time | Milestone | Proof |
|---|---|---|
| **0:30** | M0 Contracts | `schemas.py`, the four interface signatures, `fixtures/`, `docs/api.md` merged to main |
| **3:30** | M1 Hello Steel | A: one Browser Use journey on a Steel session, `RunEvent`s print, session released, replay URL opens |
| **7:00** | M2 Vertical slices | Explore gives a `SiteModel` on the mock site; Runner runs a 2-config matrix on it; Scorer passes fixture tests; UI shows the whole flow on the API stub |
| **10:00** | M3 End-to-end on mock site | `run_pipeline("http://mock")` from the UI: grid → score → finding, no manual steps |
| **14:00** | M4 End-to-end on the real target | MVP matrix on the headline site; at least one attributed finding with a real replay. **"We could demo now."** |
| **18:00** | M5 Demo freeze | Cached Explore for both targets, dry-run fallback recorded, Claude CU in or cut, A's stretch item in or cut. No new features after this |
| **18:00–24:00** | M6 Rehearse ×5 | Run the 4-minute script five times; one person plays a hostile judge each time. Fix only what breaks on stage |

**Rule:** if M4 slips past 16:00, A drops the stretch item immediately and cuts Claude CU if it has not completed a journey by then. One engine with a clean demo beats three engines that stall on stage.

---

## 5. Parallelism check (who waits on whom, and what they do meanwhile)

| Dependency | Needed by | Unblocked from | If late |
|---|---|---|---|
| Schemas + signatures + fixtures (M0) | everyone | 0:30 | Nobody starts a module until this is merged; it is the only hard gate |
| B's API stub | D | 1:30 | D loads the fixture JSON statically; zero cost |
| B's mock site | A's Runner | 3:00 | A uses the real target landing page for M1 and the first Runner tests |
| A's `run_matrix` | B's orchestrator | 7:00 | B wires a fixture-replaying stub with the same signature; swaps at 7:00 |
| C's `score()` | B's orchestrator | 8:30 | Same: stub returning the fixture `ScoreCard` |
| B's orchestrator | D's real wiring | 7:00 | D keeps the stub websocket; nothing in the UI changes shape |
| A's real `RunResult`s | C's tuning | 10:00 | C keeps tuning on fixtures; adds fixtures from A's mock-site runs at 7:00 |
| B's demo store | A's fix loop | 10:00 | A picks OpenAI CU as the stretch item instead |
| A's replay-seek answer | D's finding detail | 11:00 | D ships the final-screenshot fallback regardless |

No dev has a dependency on another dev's *working code* before hour 7. Every cross-dev edge before then is a signature locked at 0:30 or a fixture.

---

## 6. Pre-event checklist (do before hour 0 if at all possible)

- [ ] Steel account, API key, **$10 spent to unlock residential proxies**; A confirms `use_proxy` geolocation works for CA and DE with a 20-line script
- [ ] Anthropic key (Claude CU + classifier LLM + Explore summariser); OpenAI key only if going for the third engine
- [ ] `pip install browser-use playwright steel-sdk fastapi uvicorn pydantic` and a smoke test that Browser Use attaches to a Steel session over CDP (A)
- [ ] Python 3.12 venv, `.env.example` committed, `.env` gitignored
- [ ] Node 20 + Vite scaffold so D doesn't spend hour 1 on tooling
- [ ] Questions for the 1 PM Steel workshop: elevated concurrency, proxy credits, Steel Computer beta scope, whether replay embeds accept a seek param (A asks)

---

## 7. Working agreements

- **Schema changes are all-hands.** Nobody edits `schemas.py` alone. Say it out loud, change it, everyone pulls.
- **Fixtures are the API.** If your module works on the fixtures, integration is a wiring job. If it doesn't, fix the fixture first, then the code.
- **Steel credits are A's budget.** B, C, D develop on the mock site and fixtures; only A hits Steel outside of integration and rehearsals. A checks the dashboard for leaked sessions every few hours.
- **Every finding must be reproducible from a replay link.** If you can't show the frame, it's not a finding yet.
- **Cut, don't stretch.** The should/stretch tiers exist to be dropped at 16:00 if M4 hasn't landed.

---

## 8. Workload estimate (scope points, 1 = trivial, 8 = hardest module in the project)

Everyone is present for 24h, so "workload" means scope and difficulty, not hours. Points below are the basis for the 40 / 30 / 15 / 15 split.

| Dev A (Jinay) | pts | Dev B | pts | Dev C | pts | Dev D | pts |
|---|---|---|---|---|---|---|---|
| Steel wrapper | 4 | API stub + real wiring | 5 | Classifiers + tests | 6 | Scaffold + 4 views | 7 |
| Browser Use adapter | 4 | Mock site | 2 | Attribution + score | 3 | Real websocket wiring | 3 |
| Runner | 8 | Explore | 7 | Static fetch + fixes | 2 | Real-target integration | 2 |
| Claude CU | 6 | Orchestrator | 3 | Real-stream tuning | 3 | Polish + cached mode | 2 |
| Real-target integration | 5 | Integration lead | 4 | Slides + hardening | 1 | Devpost + video | 2 |
| Stretch: OpenAI CU or fix loop | 6 | Scouting | 1 | | | | |
| Hardening + live ops | 4 | Demo store + tunnel | 4 | | | | |
| | | Cache + hint + dry-run | 4 | | | | |
| **Total** | **37** | | **30** | | **15** | | **16** |
| **Share** | **38%** | | **31%** | | **15%** | | **16%** |

Total 98 points. A's share rises to ~41% if both stretch items are attempted; the plan asks A to pick one at 14:00.
