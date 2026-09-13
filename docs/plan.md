# Crucible — Build plan and work split

Companion to `docs/concept.md` (pitch) and `docs/superpowers/specs/2026-09-12-crucible-design.md` (design v3). This doc answers one question: **who builds what, in what order, and how the pieces meet.**

Hackathon window: 24h, Sept 12–13 2026. Team of 4: **Dev A = Jinay**, Devs B, C, D.

---

## 1. The critical path (read this first)

Everything live depends on three things, and one person owns all three so there is no handoff on the critical path:

1. **The Steel session wrapper** (`crucible/steel.py`): create → connect over CDP → release, with mobile / profile / geo options.
2. **The engine adapters** (`crucible/engines/`): Browser Use first, then Claude computer use, then OpenAI computer use. Each drives a journey on a Steel session and emits `RunEvent`s.
3. **The Runner** (`crucible/runner/`): the population matrix, wave scheduling under the 10-session cap, profile warm-up ordering, retries, harness-error isolation.

That is Dev A's seat. It is the most technical part and burns the most Steel credits, model tokens, and debugging time. Explore, Scorer, UI, and targets are parallel and build against fixtures until integration.

```
hour 0      0:30            3:00                 6:00              10:00            14:00           18:00     24:00
 |-schemas-|  Steel wrapper  |  Runner + matrix   |  Claude CU       |  OpenAI CU     |                |
 |          |  + Browser Use |  (A)               |  (A)             |  (A, stretch)  |                |
 |          |  (A) → M1      |                    |                  |                |                |
 |          |  Explore on Playwright + LLM (B) ───▶ orchestrator (B) ▶ integration lead (B) ──────────▶| demo   |
 |          |  Scorer on fixtures (C) ────────────────────────────────▶                                | freeze |
 |          |  UI on mock data (D) ───────────────────────────────────▶                                |        |
```

**Design choice that makes this split work:** Explore does **not** use an agent framework. It is a Playwright breadth-first crawler with a safety allowlist, plus one LLM call over the collected page summaries to produce the `SiteModel` and journeys. That means B never waits on A's engine adapters, and Explore is deterministic enough to cache and replay on stage.

---

## 2. Contracts locked in the first 30 minutes (all four together)

Do these in one room before anyone opens a module.

1. **`crucible/schemas.py`** — Pydantic models exactly as in the design doc: `SiteModel`, `Journey`, `Config`, `RunEvent`, `Finding`, `ScoreCard`. Add `RunResult` (terminal wrapper: `run_id`, `config`, `journey_id`, `session_id`, `outcome`, `events: [RunEvent]`, `replay_url`, `final_screenshot_ref`).
2. **Engine interface** (`crucible/engines/base.py`):
   ```python
   class Engine(Protocol):
       name: str
       async def run_journey(self, session: SteelSession, journey: Journey, cfg: Config, step_cap: int) -> AsyncIterator[RunEvent]: ...
   ```
3. **Runner interface** (`crucible/runner/__init__.py`):
   ```python
   async def run_matrix(site: SiteModel, configs: list[Config], engines: dict[str, Engine]) -> AsyncIterator[RunEvent | SessionStarted | RunResult]: ...
   ```
4. **Fixtures directory** (`fixtures/`): one hand-written example of each schema, plus two full event streams (one `completed`, one `stalled` on a cookie wall). Mock data for C and D, golden tests for the Scorer.
5. **API contract** (`docs/api.md`):
   - `POST /runs {url, hint?, cached_site_model?}` → `{run_id}`
   - `GET /runs/{id}` → `{stage, site_model?, scorecard?, findings?}`
   - `WS /runs/{id}/events` → stream of `RunEvent`, `{type: "session_started", session_id, viewer_url, config}`, `{type: "stage", name}`
   - `GET /fixtures/demo` → a full canned run
6. **Repo layout** and the git rule: one branch per person, merge to `main` at least every 3 hours, `main` must always import and pass `pytest tests/scorer`.

```
crucible/
  schemas.py          # contract (all four; changes need everyone in the room)
  steel.py            # A: session lifecycle + mobile/profile/geo config
  engines/            # A: base.py, browser_use.py, claude_cu.py, openai_cu.py
  runner/             # A: matrix, waves, profile warm-up, retries, event bus
  explore/            # B: Playwright BFS crawler + LLM → SiteModel
  orchestrator.py     # B: explore → run → score pipeline, one entry point
  scorer/             # C: classify, attribute, score, fixes, static contrast
  fixloop/            # C (stretch): Steel Computer patch-and-rerun
  api/                # D: FastAPI app + websocket
web/                  # D: React + Tailwind
targets/
  mock_site/          # B: local static site with known traps (no Steel credits)
  demo_store/         # C: self-hosted storefront with 3 injected traps
  cache/              # B: cached SiteModel JSON for demo targets
fixtures/             # everyone
tests/                # C first (scorer), then whoever
```

---

## 3. Per-person ownership

### Dev A (Jinay) — Steel core: sessions, engines, Runner
*The live machinery. Everything the judges watch run in the grid comes from here.*

| Hours | Deliverable | Depends on |
|---|---|---|
| 0:30–2:00 | `steel.py`: `SteelSession` async context manager. Create with `device_config={"device": "mobile"}`, `persist_profile=True` / `profile_id=`, `use_proxy={"geolocation": {"country": ...}}`, `timeout=12min`; connect Playwright over CDP; **idempotent release** in `finally`, safe to call twice; expose `viewer_url`, `replay_url`, `session_id`. Ship this first. | Steel key, proxies unlocked |
| 2:00–3:30 | `engines/browser_use.py`: Browser Use attached to the Steel CDP session, one `RunEvent` per agent step (action, observation, screenshot ref), terminal outcome from the agent's own done/fail signal, hard step cap. **Milestone M1 at 3:30: one journey on one Steel session, events print, session released, replay URL opens.** | `steel.py` |
| 3:30–7:00 | `runner/`: build the matrix from `SiteModel.journeys` × configs; wave scheduler with `asyncio.Semaphore(10)`; **ordering constraint: the baseline run for a journey is created with `persist_profile=True` and must finish before the `returning` variant starts with its `profile_id`**; retry a `stalled` run once; harness-error detection (session create failure, engine exception, model timeout, CDP disconnect → `harness_error`, never `stalled`); step caps enforced in the runner, not trusted to engines; event bus that yields `RunEvent`, `SessionStarted`, `RunResult` in order | Browser Use adapter, mock site from B |
| 7:00–8:00 | Pair with B: orchestrator calls `run_matrix`; run the 2-config matrix on the mock site end to end | B |
| 8:00–11:00 | `engines/claude_cu.py`: Claude computer use on the same Steel session via the Steel cookbook recipe. Screenshot → model → action loop, mapped to the same `RunEvent` shape. Per-step token budget and a lower step cap than Browser Use. Read the `claude-api` skill before wiring. **Unlocks `engine` attribution and `engine_consensus`.** | Runner stable |
| 11:00–14:00 | Integration on the real target: proxy countries that actually work (test CA, DE, GB; keep two), mobile mode renders the mobile layout, returning profile actually carries cookies (verify in the replay), concurrency negotiated with the Steel booth. Watch the Steel dashboard for leaked sessions | C's target pick |
| 14:00–17:00 | `engines/openai_cu.py` (stretch, only if Claude CU landed by 11:00). Otherwise: hardening below | — |
| 17:00–18:00 | Hardening: global run timeout, graceful cancel that releases every session, wave sizing that finishes the MVP matrix inside 4 minutes on stage | — |
| 18:00–24:00 | Runs the live part of every rehearsal; owns the Steel credit budget and the decision to fall back to cached mode | — |

**Done when:** the MVP matrix (2 journeys × baseline + mobile + returning + one country = 8 sessions) runs on the real target inside one wave with no leaked sessions; Browser Use completes the baseline journey 2 of 3 tries; Claude CU completes it at least once so an `engine` attribution exists; a killed run releases everything.

**Why this seat is the heavy one:** it is the only module that cannot be developed on fixtures. Every iteration costs a Steel session and model tokens, three vendor SDKs have to agree on one event shape, and the profile warm-up ordering plus the 10-session cap make the scheduler the trickiest concurrency code in the project.

### Dev B — Explore + orchestrator + integration lead
*Owns "what is this site and what should agents try," and owns the pipeline wiring.*

| Hours | Deliverable | Depends on |
|---|---|---|
| 0:30–2:00 | `targets/mock_site/`: static local site (plain HTML, served with `python -m http.server`) with a cookie overlay, an icon-only cart button, a hamburger-only mobile nav, a product list, a cart page, and a checkout page. A and B both develop against this, not Steel credits | — |
| 2:00–6:00 | `explore/`: Playwright BFS crawler from the landing page. Per page: collect title, headings, nav links, buttons, forms, and a classified list of action types. Safety allowlist: click links, nav, tabs, menus, scroll; type only into inputs that look like search; **never** submit a form whose button or surrounding text matches purchase / delete / cancel / subscribe / unsubscribe / confirm; never type into password or payment fields. Stopping rule: 2 consecutive pages adding no new action types, or 25 pages, or 3 minutes. Then one LLM call over the page summaries → `SiteModel` with brand, category, audience, and top 3 journeys with specific, executable goals ("on /collections/all, add the first product to the cart and open the cart page") | schemas |
| 6:00–7:00 | `orchestrator.py`: `run_pipeline(url, hint, cached_site_model=None) -> AsyncIterator[event]` that runs Explore → `run_matrix` → Scorer and emits `{type: "stage"}` markers between them. This is the only thing D's API calls | A, C |
| 7:00–8:00 | Pair with A on the first end-to-end run on the mock site (M3 prep) | A |
| 8:00–14:00 | **Integration lead.** Owns `main`, runs the M3 and M4 checks, chases whoever is blocking. Explore quality on the real target: if the Scorer sees `timeout` on baseline, the journey goal is under-specified, fix it here first | everyone |
| 14:00–18:00 | Record and cache Explore for both demo targets into `targets/cache/`; user-hint shortcut that seeds the site model; `--dry-run` flag on the orchestrator that replays a recorded run through the whole pipeline so D can rehearse without Steel | — |
| 18:00–24:00 | Rehearsals: plays the hostile judge; keeps the fallback list current | — |

**Done when:** Explore produces a usable `SiteModel` for the real target in under 3 minutes, its journey goals are specific enough that Browser Use completes the baseline, and both demo targets have cached site models.

### Dev C — Scorer + targets + fix loop
*Owns "every stall is attributed and the score is defensible."*

| Hours | Deliverable | Depends on |
|---|---|---|
| 0:30–1:30 | Scout 3 real e-commerce candidates (Shopify-style, cookie modal, decent Cloudflare static score, no login wall on product pages). Record each isitagentready.com score. Pick one by 1:30 and tell the team; the other two are fallbacks | — |
| 1:30–5:00 | `scorer/classify.py`: deterministic classifiers first (URL unchanged after N actions → `timeout`; overlay with consent text intercepting clicks → `cookie_wall`; CAPTCHA iframe → `captcha`; proxy block page → `geo_block`), then an LLM pass over the final screenshot + last 5 events for the rest, returning `category` + one-line description. **Unit tests against `fixtures/` from the start** | schemas, fixtures |
| 5:00–6:00 | `scorer/attribute.py`: variant stall vs. baseline → `attributed_to`; stall present in baseline → `site`; same category across every engine → `engine_consensus`. `scorer/score.py`: per-journey weighted completion (baseline 2×, variants 1×), overall mean, harness errors excluded and reported separately | — |
| 6:00–7:00 | `scorer/static.py`: fetch the Cloudflare static score; return `None` on any failure. `scorer/fixes.py`: proposed-fix text per category + offending element | — |
| 7:00–10:00 | `targets/demo_store/`: small self-hosted storefront (Next.js commerce template or a 200-line Flask store) with 3 injected traps: icon-only cart button, consent modal with no accessible name, hamburger-only mobile nav. Reachable by Steel via a tunnel | — |
| 10:00–14:00 | Integration: run the Scorer on real event streams, fix classifier gaps, confirm every `Finding` carries a `session_id` + `step_index` that lands on the stall frame in the replay | A |
| 14:00–20:00 | **Stretch, only if the 1 PM workshop confirms Steel Computer access:** `fixloop/`: clone the store repo on a Steel Computer, apply a patch for one finding, restart, re-run that journey × config via the orchestrator, emit the new score. Otherwise: harden the taxonomy and write the prior-art slide | Steel Computer, demo store |

**Done when:** `pytest tests/scorer` passes on fixtures, and on the real target at least one finding reads "fails only on mobile" (or another single variable) with a replay that shows the stall.

### Dev D — API + UI
*Owns "what the judges see."*

| Hours | Deliverable | Depends on |
|---|---|---|
| 0:30–2:00 | `api/`: FastAPI app implementing `docs/api.md` against `fixtures/` only. `GET /fixtures/demo` returns a full canned run. Websocket replays the fixture event stream with small delays so the UI feels live | API contract |
| 2:00–6:00 | `web/`: Vite + React + Tailwind. Four views on mock data: **journey map** (site model + 3 journeys), **live grid** (one card per session with embedded Steel live viewer iframe, config label, current step), **score card** (ours beside the Cloudflare static score, per-journey rows, harness errors in a muted side panel), **finding detail** (category, attribution badge, `engine_consensus` badge, proposed fix, replay iframe seeked to `step_index`) | fixtures |
| 6:00–8:00 | Wire the API to B's orchestrator; websocket forwards real events; live grid mounts a viewer as soon as `session_started` arrives | B |
| 8:00–14:00 | Integration on the real target: viewers render, findings link to the right replay frame, score card updates when the Score stage finishes | everyone |
| 14:00–18:00 | Polish for the demo script: the "85 vs. ours" contrast is the biggest thing on screen; attribution badges readable from the back of the room; no spinner longer than 5s without a status line; `?demo=cached` mode that replays a recorded run if Steel dies on stage | B's dry-run |
| 18:00–24:00 | Rehearsal driver, Devpost writeup, screenshots and the 3-minute video | — |

**Done when:** a stranger can paste a URL and, without anyone explaining, see the matrix run, the score land, and click into a stall.

---

## 4. Milestones (checkpoints where everyone syncs)

| Time | Milestone | Proof |
|---|---|---|
| **0:30** | M0 Contracts | `schemas.py`, `engines/base.py`, `runner/__init__.py` signature, `fixtures/`, `docs/api.md` merged to main |
| **3:30** | M1 Hello Steel | A: one Browser Use journey on a Steel session, `RunEvent`s print, session released, replay URL opens |
| **7:00** | M2 Vertical slices | Explore gives a `SiteModel` on the mock site; Runner runs a 2-config matrix on it; Scorer passes fixture tests; UI shows the whole flow on canned data |
| **10:00** | M3 End-to-end on mock site | `run_pipeline("http://mock")` from the UI: grid → score → finding, no manual steps |
| **14:00** | M4 End-to-end on the real target | MVP matrix on the headline site; at least one attributed finding with a real replay. **"We could demo now."** Everything after is should/stretch |
| **18:00** | M5 Demo freeze | Cached Explore for both targets, `?demo=cached` fallback recorded, Claude CU in or cut, OpenAI CU and fix loop in or cut. No new features after this |
| **18:00–24:00** | M6 Rehearse ×5 | Run the 4-minute script five times; one person plays a hostile judge each time. Fix only what breaks on stage |

**Rule:** if M4 slips past 16:00, cut OpenAI CU and the fix loop immediately, and cut Claude CU if it has not completed a journey by then. One engine with a clean demo beats three engines that stall on stage.

---

## 5. How the pieces meet (integration order)

1. **A ↔ B (hour 6–8):** the orchestrator calls `run_matrix(site, configs, engines)` and forwards what it yields. B needs `SessionStarted` events (with `viewer_url`) to reach D's grid before the first `RunEvent`.
2. **A ↔ C (hour 7+):** the Runner's `RunResult` is what the Scorer consumes. The Scorer never touches Steel; it needs `replay_url`, `final_screenshot_ref`, and per-event `step_index` from the Runner.
3. **B ↔ D (hour 6–8):** `run_pipeline` is the only entry point the API calls. The websocket forwards whatever it yields, untouched.
4. **B ↔ C (hour 8+):** journey `goal` text quality determines whether stalls are real. `timeout` on baseline means the journey is under-specified, not that the site is broken.
5. **A ↔ D (hour 8+):** the finding detail view needs the replay to seek to `step_index`. A confirms early whether Steel's replay embed accepts a seek/timestamp param; if not, D shows the final screenshot beside the replay.

---

## 6. Pre-event checklist (do before hour 0 if at all possible)

- [ ] Steel account, API key, **$10 spent to unlock residential proxies**; A confirms `use_proxy` geolocation works for CA and DE with a 20-line script
- [ ] Anthropic key (Claude CU + classifier LLM + Explore summariser); OpenAI key only if going for the third engine
- [ ] `pip install browser-use playwright steel-sdk fastapi uvicorn pydantic` and a smoke test that Browser Use attaches to a Steel session over CDP (A)
- [ ] Python 3.12 venv, `.env.example` committed, `.env` gitignored
- [ ] Node 20 + Vite scaffold so D doesn't spend hour 1 on tooling
- [ ] Three candidate targets bookmarked with their isitagentready.com scores (C)
- [ ] Questions for the 1 PM Steel workshop: elevated concurrency, proxy credits, Steel Computer beta scope, whether replay embeds accept a seek param (A asks)

---

## 7. Working agreements

- **Schema changes are all-hands.** Nobody edits `schemas.py` alone. Say it out loud, change it, everyone pulls.
- **Fixtures are the API.** If your module works on the fixtures, integration is a wiring job. If it doesn't, fix the fixture first, then the code.
- **Steel credits are A's budget.** B, C, D develop on the mock site and fixtures; only A hits Steel outside of integration and rehearsals. A checks the dashboard for leaked sessions every few hours.
- **Every finding must be reproducible from a replay link.** If you can't show the frame, it's not a finding yet.
- **Cut, don't stretch.** The should/stretch tiers exist to be dropped at 16:00 if M4 hasn't landed.
