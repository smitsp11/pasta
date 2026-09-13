# Dev A (Jinay) — Steel core implementation plan

Companion to `docs/plan.md` §3 (Dev A row) and the design in `docs/superpowers/specs/2026-09-12-crucible-design.md`. This is the build order, module design, and verification for the seat that owns `crucible/steel.py`, `crucible/engines/`, `crucible/runner/`, and the stretch `crucible/fixloop/`.

API names below were checked against the Steel Python SDK source, the Steel cookbook (Browser Use, Claude computer use desktop and mobile), the Browser Use docs, and the Claude API reference on Sept 12 2026. Items marked **VERIFY** could not be confirmed from docs and are the first things the pre-flight spikes settle.

---

## 0. Principles for this seat

1. **Sessions never leak.** Every Steel session is created inside an async context manager whose `__aexit__` releases it, and release is idempotent. A crash, a cancel, or a timeout all end in `release`. `client.sessions.release_all()` is the panic button, wired to a CLI flag.
2. **Engines are dumb, the Runner is smart.** An engine turns one `(session, journey)` into a stream of `RunEvent`s and nothing else. Step caps, timeouts, retries, and outcome classification beyond the engine's own done/fail signal live in the Runner.
3. **Fixtures first, Steel second.** A `FakeSteelSession` and a `FakeEngine` that replays a fixture stream let the Runner's scheduling, retry, and cancellation logic be unit-tested with zero credits. Steel is touched at M1, at integration, and at rehearsals.
4. **Every event carries what the Scorer and the UI need.** `session_id`, `step_index`, a timestamp, the current URL, and a screenshot ref. Attribution and jump-to-failure are downstream of this; if it is missing here, C and D cannot recover it.

---

## 1. Pre-flight (before hour 0, or 0:30–1:00 at worst)

```
pip install steel-sdk playwright browser-use anthropic pydantic python-dotenv
playwright install chromium
```

`.env`: `STEEL_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (stretch only).

Three throwaway scripts in `scripts/spike_*.py`, each under 30 lines, each run once. They exist to settle the **VERIFY** items, not to be kept.

| Spike | What it proves | VERIFY items it settles |
|---|---|---|
| `spike_session.py` | `Steel(steel_api_key=...)`, `sessions.create(...)`, print `id`, `websocket_url`, `debug_url`, `session_viewer_url`, `dimensions`; connect Playwright with `chromium.connect_over_cdp(f"{session.websocket_url}&apiKey={KEY}")`; `browser.contexts[0]`; open a page; release; confirm `status == "released"` via `sessions.retrieve` | The exact kwarg for the session lifetime. The SDK source shows `api_timeout` (ms, default 300000) as the session timeout; the REST field is `timeout`. Confirm which kwarg the installed version accepts |
| `spike_variants.py` | Create three sessions in a row: `device_config={"device": "mobile"}`, `use_proxy={"geolocation": {"country": "CA"}}`, `persist_profile=True`. Print `dimensions` for mobile, hit an IP-echo page for the proxy, print `profile_id` for the profile. Release all | Whether the account plan allows Steel-managed proxies (docs: Developer plan and up, per-GB billing; Hobby tier is datacenter IPs only). The design doc's "$10 to unlock" is this upgrade. Whether `dimensions` on a mobile session is populated by Steel (the mobile cookbook says it is) |
| `spike_profile.py` | Create session A with `persist_profile=True`, set a cookie via Playwright, release. Poll the profile until it is `READY`. Create session B with `profile_id=A.profile_id`, read the cookie back | The docs say the profile snapshot uploads **after release** and moves `UPLOADING` → `READY`. Find the SDK call to read profile status (expected `client.profiles.retrieve(profile_id)`) and how long READY takes. This number sets the gap between the baseline wave and the returning wave |

Also confirm in `spike_session.py` which Browser Use classes the installed version exposes. The Steel cookbook uses `BrowserSession(cdp_url=...)` passed as `browser_session=`; the current Browser Use docs use `Browser(cdp_url=...)` passed as `browser=`. Pin whichever works in `requirements.txt` and never upgrade during the event.

---

## 2. Module 1 — `crucible/steel.py` (0:30–2:00)

### Public surface

```python
class SteelSession:
    """One Steel browser session. Async context manager. Release is idempotent."""
    session_id: str
    viewer_url: str          # live embed for the grid: f"{debug_url}?interactive=false"
    replay_url: str          # session_viewer_url from the Session object (dashboard replay)
    hls_url: str             # f"https://api.steel.dev/v1/sessions/{id}/hls" for a custom player
    created_at: datetime     # from the Session object; replay offsets are computed against this
    profile_id: str | None   # set when persist_profile=True or profile_id= was passed
    dimensions: tuple[int, int]
    page: playwright.async_api.Page   # connected over CDP, first context

    async def __aenter__(self) -> "SteelSession": ...
    async def __aexit__(self, *exc) -> None: ...   # always releases
    async def release(self) -> None: ...            # safe to call twice
    async def screenshot_ref(self, step_index: int) -> str: ...  # saves PNG under runs/<id>/<step>.png, returns path

@asynccontextmanager
async def open_session(cfg: Config, *, profile_id: str | None = None, persist_profile: bool = False,
                       timeout_ms: int = 12 * 60_000, inactivity_ms: int = 120_000) -> AsyncIterator[SteelSession]: ...

async def release_all() -> None: ...   # panic button; also exposed as `python -m crucible.steel --release-all`
```

### `Config` → Steel kwargs mapping

| `Config` field | Steel `sessions.create` kwarg | Notes |
|---|---|---|
| `device == "mobile"` | `device_config={"device": "mobile"}` | Steel sets UA, viewport, touch. Read `session.dimensions` back; do not hard-code |
| `device == "desktop"` | `dimensions={"width": 1280, "height": 800}` | Fixed so vision engines get a stable screenshot size |
| `country != "US"` | `use_proxy={"geolocation": {"country": cc}}` | Residential, per-GB billed. `US` baseline runs with no proxy (datacenter IP, free) |
| `identity == "returning"` | `profile_id=<baseline's profile_id>` | Only after the profile is READY |
| baseline of a journey that has a returning variant | `persist_profile=True` | Runner decides this, not the Config |
| always | `api_timeout=timeout_ms` (**VERIFY** name), `inactivity_timeout=inactivity_ms` | 12 min under the 15-min cap; inactivity release protects against a hung engine |
| always | `solve_captcha=False` | A CAPTCHA is a finding, not something to solve away |

### Behaviour

- `__aenter__`: create session → `async_playwright().start()` → `connect_over_cdp` → `contexts[0]` → use the existing page if any, else `new_page()`. If any step after create fails, release the session before re-raising so a half-open session is never returned.
- `release`: guarded by an `asyncio.Lock` and a `_released` flag. Closes Playwright first, then calls `sessions.release(id)`. Swallows "already released" errors from Steel. Logs the session id and credits used on release (`sessions.retrieve` gives `credits_used`, `proxy_bytes_used`).
- `screenshot_ref`: `page.screenshot()` to `runs/<session_id>/<step_index:03d>.png`; returns the path. Engines call this once per step so the Scorer's LLM classifier has the final frame.
- **Replay offset:** `replay_offset_s(ts) = (ts - created_at).total_seconds()`. Every `RunEvent.timestamp` is UTC; D can seek the HLS stream to this offset for jump-to-failure. This is the answer to the "does the replay accept a seek param" question: the dashboard replay does not document one, but the HLS endpoint plus this offset gives D a seekable player.
- Errors from `sessions.create` (quota, concurrency, proxy unavailable) raise `SteelUnavailable`, which the Runner maps to `harness_error`.

### Tests

`tests/steel/test_release.py` with the Steel client mocked: release called exactly once across double-`release()`, `__aexit__` after exception, and `asyncio.CancelledError`.

---

## 3. Module 2 — `crucible/engines/` (2:00–3:30 for Browser Use; 8:00–11:00 for Claude CU)

### 3.1 The contract every engine obeys (`engines/base.py`, locked at M0)

```python
class Engine(Protocol):
    name: str                       # "browser_use" | "claude_cu" | "openai_cu"
    default_step_cap: int           # browser_use 25, claude_cu 40, openai_cu 40

    async def run_journey(self, session: SteelSession, journey: Journey, cfg: Config,
                          step_cap: int) -> AsyncIterator[RunEvent]: ...
```

Event contract:

- Yield exactly one `RunEvent` per agent step with `outcome="step_ok"`, `action` (short human string, e.g. `click "Add to cart"`), `observation` (current URL plus the agent's one-line reasoning if available), `screenshot_ref`, `timestamp`.
- Yield one terminal event with `outcome` in `{completed, stalled}`. The engine reports its own belief; the Runner overrides to `harness_error` on exceptions and to `stalled` on step-cap or time-cap.
- Never raise for a site problem. Raise only for engine or infra failures (model API error, CDP disconnect). Those become `harness_error`.
- Stop before payment: every engine gets the same `PAYMENT_GUARD` text appended to its system prompt ("Stop and report completion when you reach the checkout or payment page. Never enter card details, never click Pay or Place order.") **and** a URL/button watchdog in `engines/guard.py` that the Runner runs on every event: if the URL matches `/pay|/payment|/checkout/complete|/order/confirm` or the last action text matches `pay|place order|confirm purchase`, the Runner ends the run as `completed` (reached checkout) and releases the session.

### 3.2 Browser Use adapter (`engines/browser_use.py`)

Facts from the cookbook and docs:

- `from browser_use import Agent, ChatAnthropic` and either `Browser(cdp_url=...)` → `browser=` or `BrowserSession(cdp_url=...)` → `browser_session=` (**VERIFY** in spike; pin the version).
- `Agent(task=..., llm=ChatAnthropic(model="claude-opus-5"), browser=..., max_steps=step_cap, max_actions_per_step=3, use_vision="auto", max_failures=2, step_timeout=45, extend_system_message=PAYMENT_GUARD)`.
- Hooks: `await agent.run(on_step_start=..., on_step_end=...)`, each `async def hook(agent)`. Inside a hook: `agent.history.urls()`, `agent.history.model_actions()`, `agent.history.model_outputs()`, `agent.history.number_of_steps()`.
- Terminal: `history.is_done()`, `history.is_successful()`, `history.final_result()`, `history.errors()`. Docs warn `is_successful` is agent-reported; that is fine, the Scorer verifies against the URL and screenshot.

Design: `agent.run()` is one awaitable, so the adapter bridges hooks to an `asyncio.Queue` and yields from the queue while `run()` executes in a task.

```python
async def run_journey(self, session, journey, cfg, step_cap):
    q: asyncio.Queue[RunEvent | None] = asyncio.Queue()
    step = 0

    async def on_step_end(agent):
        nonlocal step
        step += 1
        url = (agent.history.urls() or [None])[-1]
        actions = agent.history.model_actions()
        last_action = summarise(actions[-1]) if actions else "(none)"
        ref = await session.screenshot_ref(step)
        await q.put(RunEvent(step_index=step, action=last_action, observation=url or "",
                             screenshot_ref=ref, outcome="step_ok", timestamp=now(), **ids))

    agent = Agent(task=journey.goal, llm=self.llm, browser=Browser(cdp_url=session.cdp_url),
                  max_steps=step_cap, extend_system_message=PAYMENT_GUARD, ...)
    runner = asyncio.create_task(agent.run(on_step_end=on_step_end))
    runner.add_done_callback(lambda _: q.put_nowait(None))

    while (ev := await q.get()) is not None:
        yield ev
    history = await runner            # re-raises engine exceptions → Runner maps to harness_error
    outcome = "completed" if history.is_done() and history.is_successful() else "stalled"
    yield RunEvent(step_index=step + 1, action="done", observation=history.final_result() or "",
                   screenshot_ref=await session.screenshot_ref(step + 1), outcome=outcome, ...)
```

Model: `claude-opus-5` via Browser Use's `ChatAnthropic`. If credit burn on the DOM agent becomes a problem during integration, switching that one engine to `claude-sonnet-5` is a one-line change; that is your call at hour 11, not a default.

Hour 3:30 exit (M1): one journey on the mock site or the real target's landing page prints step events, ends in `completed` or `stalled`, the session shows `released` in the dashboard, and the replay URL opens.

### 3.3 Claude computer-use adapter (`engines/claude_cu.py`)

Facts from the Steel recipes and the Claude API reference:

- Tool: `{"type": "computer_20251124", "name": "computer", "display_width_px": W, "display_height_px": H, "display_number": 1}`. Beta header `computer-use-2025-11-24`. Call via `client.beta.messages.create(...)` with `betas=["computer-use-2025-11-24", "server-side-fallback-2026-07-01"]` and `fallbacks="default"` (server-side fallback on a `refusal` stop reason; it is on by default in this plan, drop it if you would rather handle refusals yourself).
- Model `claude-opus-5`. Thinking is adaptive by default; leave it on and set `output_config={"effort": "high"}`, which is the documented sweet spot for computer use. `max_tokens=4096` per turn is plenty since each turn is one action.
- Loop: send screenshot → model returns `stop_reason == "tool_use"` with a `computer` tool call → execute the action with Playwright → return `tool_result` containing an `image` block (base64 PNG) → repeat. Loop ends when the response has no tool call (text only) or when the text contains a completion marker (`TASK_COMPLETED:` / `TASK_FAILED:`, as in the Steel recipes). Hard cap = `step_cap`.
- Desktop screenshots at the session's fixed 1280×800. Mobile: read `session.dimensions` (the mobile recipe does exactly this) and clamp every coordinate to `[0, w-1] × [0, h-1]`.
- Input via Playwright on the CDP page, same as the mobile recipe, so both device modes share one dispatch table:

| Claude action | Playwright call |
|---|---|
| `screenshot` | `page.screenshot()` |
| `left_click {coordinate}` | `page.mouse.click(x, y)` |
| `double_click` | `page.mouse.dblclick(x, y)` |
| `right_click` | `page.mouse.click(x, y, button="right")` |
| `mouse_move` | `page.mouse.move(x, y)` |
| `left_click_drag {start_coordinate, coordinate}` | `mouse.move(sx, sy); mouse.down(); mouse.move(x, y); mouse.up()` |
| `type {text}` | `page.keyboard.type(text)` |
| `key {text}` | split on `+`, map `ctrl→Control`, `cmd→Meta`, `return→Enter`; `page.keyboard.press("Control+a")` |
| `scroll {coordinate, scroll_direction, scroll_amount}` | `mouse.move(x, y); mouse.wheel(0, ±amount*100)` (horizontal for left/right) |
| `wait {duration}` | `asyncio.sleep(min(duration, 3))` |
| anything else (`zoom`, `hold_key`, `triple_click`) | best-effort or `tool_result` with `is_error=True` and a one-line reason; never crash |

One `RunEvent` per tool call, `action` = the action name plus coordinates or text, `observation` = `page.url` plus any assistant text in that turn. Screenshot ref = the PNG just sent. Terminal outcome from the completion marker; no marker after `step_cap` iterations → `stalled`.

Cost guard: track `usage.input_tokens + usage.output_tokens` per run; abort as `harness_error` past a per-run budget (start at 400k tokens) so one runaway vision loop cannot eat the wave.

Hour 11:00 exit: Claude CU completes the baseline journey on the mock site once and runs on the real target under the Runner with the same `RunEvent` shape. `engine_consensus` becomes possible for C.

### 3.4 OpenAI computer-use adapter (`engines/openai_cu.py`, stretch)

Same shape as 3.3 with the OpenAI CUA loop from the Steel `openai-computer-use` recipe. Only start it if Claude CU landed by 11:00. Same dispatch table, same events, same guard.

---

## 4. Module 3 — `crucible/runner/` (3:30–7:00)

### 4.1 Matrix (`runner/matrix.py`)

```python
MVP_CONFIGS = [
    Config(device="desktop", identity="fresh",     country="US", engine="browser_use", label="baseline"),
    Config(device="mobile",  identity="fresh",     country="US", engine="browser_use", label="mobile"),
    Config(device="desktop", identity="returning", country="US", engine="browser_use", label="returning"),
    Config(device="desktop", identity="fresh",     country="CA", engine="browser_use", label="country:CA"),
]
SHOULD_CONFIGS = MVP_CONFIGS + [
    Config(..., country="DE", label="country:DE"),
    Config(..., engine="claude_cu", label="engine:claude_cu"),
]

def build_matrix(site: SiteModel, configs: list[Config]) -> list[RunSpec]:
    # one RunSpec per journey × config; baseline first; `needs_profile_from` set on returning variants
```

`RunSpec` (internal, not in the shared schema): `run_id`, `journey`, `cfg`, `persist_profile: bool`, `needs_profile_from: run_id | None`, `attempt: int`.

### 4.2 Scheduler (`runner/scheduler.py`)

The one real constraint: a returning variant needs the baseline's profile, and the profile is only READY some seconds after the baseline **releases**. So the schedule is two phases per journey, not one flat wave.

```
phase 1: all baselines (persist_profile=True where a returning variant exists)  ─┐  ≤10 concurrent
phase 2: every variant; returning variants first await profile READY             ─┘  (Semaphore)
```

Implementation: a single `asyncio.Semaphore(max_concurrency)` (default 8 to leave two slots for retries), a dict `profile_ready: dict[run_id, asyncio.Future[str]]` that phase-1 runs resolve after release plus a `wait_profile_ready(profile_id)` poll, and `asyncio.gather` over phase-2 specs that `await` their future before acquiring the semaphore. Phase 2 starts as soon as **that journey's** baseline is done, not when all baselines are done.

Per run, in order:

1. `open_session(cfg, profile_id=..., persist_profile=...)` → yield `SessionStarted(session_id, viewer_url, cfg, journey_id)` **before** the engine starts, so D's grid mounts the viewer immediately.
2. `asyncio.wait_for(engine.run_journey(...), timeout=RUN_BUDGET_S)` with `RUN_BUDGET_S = 10 * 60` (under the 12-min session timeout). Forward every event; run the payment guard on each; count steps and cut at `step_cap` even if the engine misbehaves.
3. Build `RunResult(events, outcome, session_id, replay_url, final_screenshot_ref, replay_offset_s of the last event)`.
4. Release (the context manager does it). On `persist_profile`, resolve the profile future after READY.

### 4.3 Outcome and retry policy (`runner/outcomes.py`)

| Condition | Outcome | Retry? |
|---|---|---|
| Engine yields terminal `completed` | `completed` | no |
| Engine yields terminal `stalled` | `stalled` | once (fresh session; same profile for returning) |
| Payment guard fired | `completed` | no |
| Step cap or `RUN_BUDGET_S` hit | `stalled` (`timeout` hint for C) | once |
| `SteelUnavailable`, CDP disconnect, engine exception, model API 5xx/429 after SDK retries, token budget blown | `harness_error` | once |
| Second attempt also `harness_error` | `harness_error` | no; shown outside the score |

Retries are new sessions with `attempt += 1` and a fresh `run_id` suffix; both attempts' events are kept, the last attempt's `RunResult` is what the Scorer sees.

### 4.4 Event bus (`runner/__init__.py`)

`run_matrix` is one async generator. Internally every run pushes to a shared `asyncio.Queue`; the generator drains it until the scheduler task completes. Consumers (B's orchestrator, D's websocket) see a single ordered stream of `SessionStarted | RunEvent | RunResult`. Back-pressure is not a concern at 8 sessions × ~1 event/5 s.

### 4.5 Cancellation and cleanup

`run_matrix` is wrapped in a `try/finally` that cancels all run tasks and awaits them; each run's `finally` releases its session. A `SIGINT` in the CLI triggers the same path. `python -m crucible.steel --release-all` for anything that slips through; run it before every rehearsal.

### 4.6 Wave-time budget (for the 4-minute stage demo)

MVP = 2 journeys × 4 configs = 8 sessions. Phase 1 = 2 baselines in parallel; phase 2 = 6 variants in parallel. If a Browser Use journey takes ~90 s on the mock site and ~150 s on a real store, plus ~20 s session start and ~20 s profile READY, the whole matrix is roughly two run-lengths end to end, about 5 to 6 minutes on a real target. The demo script has Explore cached, so this is the live part. Levers if it is too slow: lower `step_cap` for the demo journeys, run only the checkout journey through the returning variant, and ask the booth for concurrency so retries do not queue.

### 4.7 Tests (zero Steel credits)

`tests/runner/` with `FakeSteelSession` (records create/release calls, fake `page`) and `FakeEngine` (replays a fixture `RunResult`'s events, optionally raising at step N):

- ordering: returning variant never starts before its baseline's profile future resolves
- concurrency: never more than `max_concurrency` sessions open
- retry: `stalled` retried once, `harness_error` retried once, `completed` never
- caps: engine that never terminates is cut at `step_cap` and at `RUN_BUDGET_S` (use a tiny budget in the test)
- cancel: cancelling `run_matrix` mid-wave releases every opened fake session exactly once
- guard: an event whose URL matches the payment pattern ends the run as `completed`

These are the tests that let you sleep at 4 a.m. when a session leaks on stage; write them before touching the real target.

---

## 5. Hour-by-hour with exit criteria

| Hours | Work | Exit criterion |
|---|---|---|
| 0:00–0:30 | Contracts with the team: schemas, `Engine`, `run_matrix`, fixtures | Merged to `main` |
| 0:30–1:00 | Spikes (§1) | Three VERIFY answers written into this doc's §9 |
| 1:00–2:00 | `steel.py` + release tests | `pytest tests/steel` green; one real session created and released from the CLI |
| 2:00–3:30 | Browser Use adapter | **M1**: one journey, events print, session released, replay opens |
| 3:30–5:30 | Runner: matrix, scheduler, outcomes, event bus | `pytest tests/runner` green with fakes |
| 5:30–7:00 | Runner on Steel against B's mock site: baseline + mobile + returning, 1 journey | All three sessions visible in the dashboard, all released, `RunResult`s written to `fixtures/from_runner/` for C |
| 7:00–8:00 | Pair with B: `run_matrix` under the orchestrator | Mock-site pipeline end to end (M3 prep) |
| 8:00–11:00 | Claude CU adapter | Completes the mock-site baseline once; runs under the Runner; `engine:claude_cu` config in `SHOULD_CONFIGS` |
| 11:00–14:00 | Real target: proxy countries (try CA, DE, GB; keep the two that load), mobile layout confirmed in the viewer, returning profile carries cookies (check the cookie banner does not reappear), concurrency from the booth | **M4**: MVP matrix on the real site, no leaked sessions, ≥1 attributed finding for C |
| 14:00 | Decide: OpenAI CU (if Claude CU was done by 11:00) or fix loop (if Computer access confirmed and B's store is up) or neither | Written in the team channel |
| 14:00–17:00 | The chosen stretch item | Runs under the Runner or is cut at 16:00 |
| 17:00–18:00 | Hardening: global run timeout, cancel path on a real wave, wave sizing for the demo, `--release-all` in the rehearsal checklist | A killed wave leaves zero live sessions |
| 18:00–24:00 | Live half of five rehearsals; credit budget; the fallback call | Five clean runs or a recorded fallback |

---

## 6. Fix loop stretch (`crucible/fixloop/`, only if picked at 14:00)

Sketch, to be replaced by what the 1 PM workshop says about the Steel Computer beta:

1. Input: one `Finding` with `proposed_fix` and the demo store's repo URL.
2. On a Steel Computer: clone the repo, apply the patch (the three trap fixes are pre-written in `targets/demo_store/patches/` keyed by finding category, so the "fix" is deterministic on stage), restart the dev server, expose it through the tunnel.
3. Call `run_matrix(site, [the failing config])` for the one journey; emit the new `RunResult` to the orchestrator; C's `score()` produces the delta.
4. Total budget 4 minutes on stage. If the Computer takes longer than 90 s to boot in rehearsal, fall back to applying the patch locally and only re-running on Steel.

---

## 7. Credit and token budget

Rough numbers to plan against, refine after the spikes:

| Item | Per unit | Units in a full rehearsal | Rehearsals planned |
|---|---|---|---|
| Steel session-minutes | metered per minute | 8 sessions × ~3 min = ~24 | 5 rehearsals + integration ≈ 10 waves |
| Residential proxy | per GB | 2 sessions × ~5 MB | negligible |
| Browser Use on `claude-opus-5` | ~15 steps × ~8k input tokens | 8 runs ≈ 1M input tokens ≈ $5 | ~$50 across the day |
| Claude CU on `claude-opus-5` | ~30 turns × ~3k tokens with images | 2 runs ≈ 200k tokens ≈ $1–2 | ~$20 |

Keep a running total in `runs/credits.log` (the Runner appends `credits_used` from `sessions.retrieve` on release). If the Steel booth gives elevated concurrency, raise `max_concurrency` and nothing else changes.

---

## 8. What can go wrong in this seat specifically

| Risk | Signal | Mitigation |
|---|---|---|
| Browser Use version drift (class or hook names) | Import error at 2:00 | Pin in the spike; keep the adapter surface tiny so a rename is a 5-line fix |
| Profile never reaches READY | Returning runs hang on the future | `wait_profile_ready` times out at 90 s → returning variant runs as `harness_error` with reason `profile_not_ready`; the rest of the matrix is unaffected |
| Proxy plan not enabled | `SteelUnavailable` on `use_proxy` | Country variants become `harness_error`, the demo still runs with device + identity; upgrade the plan at the booth |
| Mobile session ignores `device_config` | `dimensions` look desktop-sized | Fall back to `dimensions={"width": 390, "height": 844}` plus a mobile UA via `stealth_config`, and say so on the slide |
| Vision loop burns the wave | Claude CU run past 5 min | Token budget + step cap in §3.3; vision runs only on the two demo journeys |
| Session leak on stage | Dashboard shows live sessions after a wave | `--release-all` before and after every rehearsal; the cancel test in §4.7 |
| CDP disconnect mid-run | Playwright raises | Mapped to `harness_error`, retried once on a fresh session |

---

## 9. VERIFY log

Settled from the installed SDKs on Sept 12 (steel-sdk 0.19.0, browser-use 0.13.10, anthropic 0.76.0, Python 3.12.13):

- [x] Session lifetime kwarg: **`api_timeout`** (ms). `timeout` on `sessions.create` is the HTTP request timeout. `inactivity_timeout` also exists.
- [x] Browser Use CDP attach: **`Browser(cdp_url=...)`** passed as **`browser=`**; `Agent.run(max_steps, on_step_start, on_step_end)`; history exposes `urls`, `model_actions`, `model_thoughts`, `is_done`, `is_successful`, `final_result`, `errors`, `screenshot_paths`. Pinned `browser-use==0.13.10`.
- [x] Profile status: **`client.profiles.get(profile_id).status`** (`ProfileGetResponse`). Time to READY: measured by `scripts/spike_profile.py` → ______ s
- [x] Anthropic SDK: `computer_20251124` tool type present; `beta.messages.create` accepts `output_config` and `betas` natively; `fallbacks` is passed via `extra_body`.
- [ ] Proxy enabled on the account (CA, DE, GB tested by `scripts/spike_variants.py`) → ______
- [ ] Mobile session `dimensions` as reported by Steel → ______
- [ ] HLS endpoint plays in D's player and seeks to `replay_offset_s` → ______ (tell D by 11:00)
- [ ] Booth: concurrency granted ______, Steel Computer access ______

## 10. Build status

- `crucible/steel.py`, `crucible/engines/{base,guard,browser_use,claude_cu,fake}.py`, `crucible/runner/` (matrix, outcomes, scheduler, CLI), `crucible/testing.py`: written, 41 unit tests green with zero Steel credits.
- `fixtures/` generated from the fake pipeline (`scripts/make_fixtures.py`), including `demo_run.json` for D and C.
- Spikes written (`scripts/spike_*.py`), **not yet run**: they need `STEEL_API_KEY` in `.env`.
- M1 (one live Browser Use journey on Steel) is the next step and needs `STEEL_API_KEY` + `ANTHROPIC_API_KEY`.
