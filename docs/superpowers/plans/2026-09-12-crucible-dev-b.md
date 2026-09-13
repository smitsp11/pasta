# Crucible Dev B — Explore, targets, orchestrator, API: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver every Dev B row in `docs/plan.md` §3: a FastAPI stub Dev D builds against from hour 1:30, a mock site with known traps, a bounded zero-context Explore that yields a `SiteModel`, the orchestrator that runs explore → run_matrix → score behind the API, the real-target scouting, the self-hosted demo store, and the cache / hint / dry-run fallbacks for the stage.

**Architecture:** Explore is a Playwright breadth-first crawler (no agent framework) with a read-only allowlist and a stopping rule, followed by one structured-output Claude call over the page summaries. The orchestrator is an async generator that yields stream items; the API fans them out to websocket subscribers and keeps the last state per run. Everything B builds runs on fixtures and a local mock site; Steel credits are only spent at integration.

**Tech Stack:** Python 3.12, pydantic v2, FastAPI + websockets, Playwright async, anthropic `messages.parse` with a Pydantic `output_format` (model `claude-opus-5`), `python -m http.server` for the mock site, Flask for the demo store.

**Source of truth for interfaces:** `docs/plan.md` §2. Where this plan adds a field or an optional parameter, it says so and the addition is backward compatible.

---

### Task 0: Contracts B depends on (M0, 0:00–0:30, all four in the room)

**Skip check:** if `python -c "from crucible.schemas import SiteModel, RunResult, SessionStarted"` succeeds and `fixtures/demo_run.json` exists, skip to Task 1.

**Files:**
- Create: `pyproject.toml`, `.env.example`, `.gitignore`, `crucible/__init__.py`, `crucible/schemas.py`, `fixtures/make_fixtures.py`
- Test: `tests/schemas/test_schemas.py`

- [ ] **Step 1: Project files**

```toml
# pyproject.toml
[project]
name = "crucible"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["pydantic>=2.7", "anthropic>=1.0", "steel-sdk>=0.9", "playwright>=1.47", "browser-use>=0.5",
  "fastapi>=0.115", "uvicorn[standard]>=0.30", "python-dotenv>=1.0", "websockets>=13", "flask>=3.0"]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.24", "httpx>=0.27"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

```bash
# .env.example
STEEL_API_KEY=
ANTHROPIC_API_KEY=
CRUCIBLE_MODEL=claude-opus-5
```

```gitignore
.env
.venv/
__pycache__/
*.pyc
node_modules/
targets/cache/recordings/
```

Run: `python3.12 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]" && playwright install chromium`

- [ ] **Step 2: Write the failing schema test**

```python
# tests/schemas/test_schemas.py
from crucible.schemas import BASELINE, Config, RunEvent, RunResult, SessionStarted, SiteModel, StageMarker, Journey


def test_baseline_and_discriminators():
    assert (BASELINE.device, BASELINE.identity, BASELINE.country, BASELINE.engine, BASELINE.label) == \
        ("desktop", "fresh", "US", "browser_use", "baseline")
    j = Journey(id="j1", name="n", goal="g", entry_url="http://x/")
    assert SiteModel(url="http://x/", brand="X", category="ecommerce", description="d", journeys=[j]).journeys[0].id == "j1"
    ev = RunEvent(run_id="r", session_id="s", journey_id="j1", config=BASELINE, step_index=0, timestamp=0.0, action="click")
    assert ev.type == "run_event"
    assert SessionStarted(run_id="r", session_id="s", viewer_url="u", config=BASELINE, journey_id="j1").type == "session_started"
    assert RunResult(run_id="r", config=BASELINE, journey_id="j1", session_id="s", outcome="completed").type == "run_result"
    assert StageMarker(name="run").type == "stage"
```

Run: `pytest tests/schemas -q` → Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the schemas (fields exactly as `docs/plan.md` §2.1; `type` discriminators added because the WS contract in §2.7 streams mixed objects)**

```python
# crucible/schemas.py
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Device = Literal["desktop", "mobile"]
Identity = Literal["fresh", "returning"]
EngineName = Literal["browser_use", "claude_cu", "openai_cu"]
Outcome = Literal["none", "step_ok", "completed", "stalled", "harness_error"]
TerminalOutcome = Literal["completed", "stalled", "harness_error"]
Category = Literal["cookie_wall", "captcha", "hidden_nav", "icon_only_control", "ambiguous_cta", "geo_block",
                   "infinite_scroll", "login_wall", "layout_shift", "timeout", "other"]
AttributedTo = Literal["device", "identity", "country", "engine", "site"]
StageName = Literal["explore", "run", "score", "fix", "done"]


class Journey(BaseModel):
    id: str
    name: str
    goal: str = Field(description="Executable goal naming concrete pages/actions; stops before payment")
    entry_url: str


class SiteModel(BaseModel):
    url: str
    brand: str
    category: str
    description: str
    audience_guess: list[str] = []
    journeys: list[Journey]


class Config(BaseModel):
    device: Device = "desktop"
    identity: Identity = "fresh"
    country: str = "US"
    engine: EngineName = "browser_use"
    label: str = "baseline"


BASELINE = Config()


class RunEvent(BaseModel):
    type: Literal["run_event"] = "run_event"
    run_id: str
    session_id: str
    journey_id: str
    config: Config
    step_index: int
    timestamp: float
    action: str
    observation: str = ""
    screenshot_ref: Optional[str] = None
    outcome: Outcome = "none"


class SessionStarted(BaseModel):
    type: Literal["session_started"] = "session_started"
    run_id: str
    session_id: str
    viewer_url: str
    config: Config
    journey_id: str


class RunResult(BaseModel):
    type: Literal["run_result"] = "run_result"
    run_id: str
    config: Config
    journey_id: str
    session_id: str
    outcome: TerminalOutcome
    events: list[RunEvent] = []
    replay_url: str = ""
    final_screenshot_ref: Optional[str] = None
    final_probe: dict = Field(default_factory=dict)   # Dev A fills; Dev C reads
    error: Optional[str] = None


class StageMarker(BaseModel):
    type: Literal["stage"] = "stage"
    name: StageName


class Finding(BaseModel):
    id: str
    journey_id: str
    config: Config
    category: Category
    description: str
    attributed_to: AttributedTo
    engine_consensus: bool = False
    session_id: str
    step_index: int
    replay_url: str = ""
    proposed_fix: str


class JourneyScore(BaseModel):
    journey_id: str
    score: float
    completed: int
    stalled: int
    harness_errors: int


class ScoreCard(BaseModel):
    overall: float
    static_score: Optional[float] = None
    per_journey: list[JourneyScore]
```

Run: `pytest tests/schemas -q` → Expected: `1 passed`

- [ ] **Step 4: Generate `fixtures/demo_run.json` from the schemas (never hand-edit it)**

```python
# fixtures/make_fixtures.py
"""python fixtures/make_fixtures.py  → fixtures/site_model.json, run_result_*.json, demo_run.json"""
import json
import time
from pathlib import Path

from crucible.schemas import BASELINE, Config, Journey, RunEvent, RunResult, SessionStarted, SiteModel, StageMarker

OUT = Path(__file__).parent
MOBILE = Config(device="mobile", label="mobile")
CA = Config(country="CA", label="ca")

SITE = SiteModel(
    url="http://localhost:8008/", brand="Mock Shop", category="ecommerce",
    description="A tiny storefront with a cookie overlay, an icon-only cart button and a hamburger-only mobile nav.",
    audience_guess=["online shoppers"],
    journeys=[
        Journey(id="find_product", name="Find a product", goal="From the home page, open any product detail page.",
                entry_url="http://localhost:8008/"),
        Journey(id="add_to_cart", name="Add to cart",
                goal="Open any product page, add it to the cart, then open the cart page and confirm it lists 1 item.",
                entry_url="http://localhost:8008/"),
    ])


def _events(run_id, sid, jid, cfg, actions, final):
    t = time.time()
    evs = [RunEvent(run_id=run_id, session_id=sid, journey_id=jid, config=cfg, step_index=i, timestamp=t + i,
                    action=a, observation=f"after {a}", outcome="step_ok") for i, a in enumerate(actions)]
    evs.append(RunEvent(run_id=run_id, session_id=sid, journey_id=jid, config=cfg, step_index=len(actions),
                        timestamp=t + len(actions), action="finish", observation=final,
                        outcome="completed" if final == "done" else "stalled"))
    return evs


COMPLETED = RunResult(run_id="r-base-cart", config=BASELINE, journey_id="add_to_cart", session_id="sess-base-cart",
    outcome="completed", replay_url="https://app.steel.dev/sessions/sess-base-cart",
    events=_events("r-base-cart", "sess-base-cart", "add_to_cart", BASELINE, ["goto /", "click product", "click add to cart", "click cart"], "done"),
    final_probe={"final_url": "http://localhost:8008/cart", "url_changed": True, "title": "Cart", "consent_overlay": False,
                 "captcha_iframe": False, "block_text": False, "login_form": False, "body_excerpt": "Cart (1 item)"})
STALLED = RunResult(run_id="r-mobile-cart", config=MOBILE, journey_id="add_to_cart", session_id="sess-mobile-cart",
    outcome="stalled", replay_url="https://app.steel.dev/sessions/sess-mobile-cart",
    events=_events("r-mobile-cart", "sess-mobile-cart", "add_to_cart", MOBILE,
                   ["goto /", "click product", "click add to cart", "click add to cart", "click add to cart"], "blocked: overlay intercepts clicks"),
    final_probe={"final_url": "http://localhost:8008/product/1", "url_changed": True, "title": "Product 1", "consent_overlay": True,
                 "captcha_iframe": False, "block_text": False, "login_form": False, "body_excerpt": "We use cookies. Accept"})
HARNESS = RunResult(run_id="r-ca-find", config=CA, journey_id="find_product", session_id="sess-ca-find",
                    outcome="harness_error", error="SteelError: proxy allocation failed")


def demo_stream():
    items = [StageMarker(name="explore"), {"type": "site_model", "site_model": SITE.model_dump()}, StageMarker(name="run")]
    for r in (COMPLETED, STALLED, HARNESS):
        items.append(SessionStarted(run_id=r.run_id, session_id=r.session_id, config=r.config, journey_id=r.journey_id,
                                    viewer_url=f"https://app.steel.dev/sessions/{r.session_id}"))
        items.extend(r.events)
        items.append(r)
    items += [StageMarker(name="score"),
              {"type": "result", "scorecard": {"overall": 66.7, "static_score": 85, "per_journey": [
                  {"journey_id": "find_product", "score": 0.0, "completed": 0, "stalled": 0, "harness_errors": 1},
                  {"journey_id": "add_to_cart", "score": 66.7, "completed": 1, "stalled": 1, "harness_errors": 0}]},
               "findings": [{"id": "f-1", "journey_id": "add_to_cart", "config": MOBILE.model_dump(), "category": "cookie_wall",
                             "description": "A consent overlay covers the page and intercepts clicks.", "attributed_to": "device",
                             "engine_consensus": False, "session_id": "sess-mobile-cart", "step_index": 2,
                             "replay_url": "https://app.steel.dev/sessions/sess-mobile-cart",
                             "proposed_fix": "Give the consent dialog role=\"dialog\" and an aria-label; make its accept button 44x44px on mobile."}]},
              StageMarker(name="done")]
    return [i if isinstance(i, dict) else i.model_dump() for i in items]


if __name__ == "__main__":
    (OUT / "site_model.json").write_text(SITE.model_dump_json(indent=2))
    (OUT / "run_result_completed.json").write_text(COMPLETED.model_dump_json(indent=2))
    (OUT / "run_result_stalled_cookie.json").write_text(STALLED.model_dump_json(indent=2))
    (OUT / "run_result_harness_error.json").write_text(HARNESS.model_dump_json(indent=2))
    (OUT / "demo_run.json").write_text(json.dumps(demo_stream(), indent=2))
    print("fixtures written")
```

Run: `python fixtures/make_fixtures.py && python -c "import json; d=json.load(open('fixtures/demo_run.json')); print(d[0], d[-1])"`
Expected: `fixtures written` then `{'type': 'stage', 'name': 'explore'} {'type': 'stage', 'name': 'done'}`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .env.example .gitignore crucible fixtures tests/schemas
git commit -m "chore: M0 schemas and generated fixtures"
```

---

### Task 1: API stub on fixtures (0:30–1:30) — Dev D builds against this from 1:30

**Files:**
- Create: `docs/api.md`, `crucible/api/__init__.py`, `crucible/api/app.py`, `crucible/api/runs.py`
- Test: `tests/api/test_stub.py`

- [ ] **Step 1: Write the API contract (plan.md §2.7, plus the two composite items the orchestrator emits)**

```markdown
# Crucible API contract (owner: Dev B)

Base URL `http://localhost:8000`

- `POST /runs`  body `{"url": str, "hint": str|null, "cached_site_model": SiteModel|null, "dry_run": bool, "recording": str|null}` → `{"run_id": str}`
- `GET /runs/{run_id}` → `{"stage": StageName, "site_model": SiteModel|null, "scorecard": ScoreCard|null, "findings": Finding[]}`
- `WS /runs/{run_id}/events` → one JSON object per message, discriminated by `type`:
  `stage {name}`, `site_model {site_model}`, `session_started`, `run_event`, `run_result`, `result {scorecard, findings}`.
  Ends with `{"type":"stage","name":"done"}`; late subscribers receive the full history first.
- `GET /fixtures/demo` → `fixtures/demo_run.json` verbatim (same stream shape).
```

- [ ] **Step 2: Write the failing test**

```python
# tests/api/test_stub.py
import json

from fastapi.testclient import TestClient

from crucible.api.app import app


def test_fixture_endpoint_and_dry_run_stream():
    c = TestClient(app)
    assert c.get("/fixtures/demo").json()[0]["type"] == "stage"
    run_id = c.post("/runs", json={"url": "http://x", "dry_run": True}).json()["run_id"]
    types = []
    with c.websocket_connect(f"/runs/{run_id}/events") as ws:
        while True:
            m = json.loads(ws.receive_text())
            types.append(m["type"])
            if m["type"] == "stage" and m["name"] == "done":
                break
    assert "run_result" in types and "result" in types and types[-1] == "stage"
    state = c.get(f"/runs/{run_id}").json()
    assert state["stage"] == "done" and state["scorecard"]["overall"] == 66.7 and len(state["findings"]) == 1
```

Run: `pytest tests/api -q` → Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the run registry**

```python
# crucible/api/__init__.py
```

```python
# crucible/api/runs.py
"""In-memory run registry: one background consumer per run, fan-out queues per websocket subscriber."""
from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import AsyncIterator, Callable, Optional

FIXTURE = Path("fixtures/demo_run.json")
RECORDINGS = Path("targets/cache/recordings")


class RunState:
    def __init__(self) -> None:
        self.stage = "explore"
        self.site_model: Optional[dict] = None
        self.scorecard: Optional[dict] = None
        self.findings: list[dict] = []
        self.history: list[dict] = []
        self.subscribers: list[asyncio.Queue] = []
        self.done = asyncio.Event()

    def snapshot(self) -> dict:
        return {"stage": self.stage, "site_model": self.site_model, "scorecard": self.scorecard, "findings": self.findings}


RUNS: dict[str, RunState] = {}


async def replay_stream(path: Path = FIXTURE, delay: float = 0.05) -> AsyncIterator[dict]:
    for item in json.loads(path.read_text()):
        await asyncio.sleep(delay)
        yield item


async def _consume(run_id: str, state: RunState, source: AsyncIterator[dict]) -> None:
    try:
        async for item in source:
            t = item.get("type")
            if t == "stage":
                state.stage = item["name"]
            elif t == "site_model":
                state.site_model = item["site_model"]
            elif t == "result":
                state.scorecard, state.findings = item["scorecard"], item["findings"]
            state.history.append(item)
            for q in list(state.subscribers):
                await q.put(item)
    finally:
        state.stage = "done"
        if not state.history or state.history[-1] != {"type": "stage", "name": "done"}:
            state.history.append({"type": "stage", "name": "done"})
            for q in list(state.subscribers):
                await q.put(state.history[-1])
        state.done.set()
        RECORDINGS.mkdir(parents=True, exist_ok=True)
        (RECORDINGS / f"{run_id}.json").write_text(json.dumps(state.history))


def start_run(make_source: Callable[[], AsyncIterator[dict]]) -> str:
    run_id = uuid.uuid4().hex[:8]
    state = RunState()
    RUNS[run_id] = state
    asyncio.create_task(_consume(run_id, state, make_source()))
    return run_id


async def subscribe(state: RunState) -> AsyncIterator[dict]:
    q: asyncio.Queue = asyncio.Queue()
    for item in state.history:          # late joiners get the past first
        await q.put(item)
    state.subscribers.append(q)
    try:
        while True:
            item = await q.get()
            yield item
            if item.get("type") == "stage" and item.get("name") == "done":
                return
    finally:
        state.subscribers.remove(q)
```

- [ ] **Step 4: Write the app (stub source; Task 4 swaps in the orchestrator)**

```python
# crucible/api/app.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from crucible.api import runs as R

app = FastAPI(title="Crucible")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
CACHE = Path("targets/cache")


class RunRequest(BaseModel):
    url: str
    hint: Optional[str] = None
    cached_site_model: Optional[dict] = None
    dry_run: bool = False
    recording: Optional[str] = None


def _pipeline_source(req: RunRequest):
    """Stub: replays the fixture. Replaced by the orchestrator in Task 4."""
    return R.replay_stream()


def _cached_site_model(url: str) -> Optional[dict]:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    p = CACHE / f"{host}.site.json"
    return json.loads(p.read_text()) if p.exists() else None


@app.get("/fixtures/demo")
def fixture_demo() -> list[dict]:
    return json.loads(R.FIXTURE.read_text())


@app.post("/runs")
async def create_run(req: RunRequest) -> dict:
    if req.dry_run:
        path = R.RECORDINGS / f"{req.recording}.json" if req.recording else R.FIXTURE
        stage = R.RECORDINGS / "stage.json"
        if not req.recording and stage.exists():
            path = stage                                    # M4 recording becomes the default fallback
        return {"run_id": R.start_run(lambda: R.replay_stream(path))}
    if req.cached_site_model is None:
        req.cached_site_model = _cached_site_model(req.url)
    return {"run_id": R.start_run(lambda: _pipeline_source(req))}


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> dict:
    if run_id not in R.RUNS:
        raise HTTPException(404)
    return R.RUNS[run_id].snapshot()


@app.websocket("/runs/{run_id}/events")
async def events(ws: WebSocket, run_id: str) -> None:
    await ws.accept()
    state = R.RUNS.get(run_id)
    if state is None:
        await ws.close(code=4004)
        return
    async for item in R.subscribe(state):
        await ws.send_text(json.dumps(item))
    await ws.close()
```

- [ ] **Step 5: Run the test, boot for Dev D, commit**

Run: `pytest tests/api -q` → Expected: `1 passed`
Run: `uvicorn crucible.api.app:app --reload --port 8000` and `curl -s localhost:8000/fixtures/demo | head -c 120`
Expected: `[{"type": "stage", "name": "explore"}, ...`. Tell Dev D the stub is up.

```bash
git add docs/api.md crucible/api tests/api
git commit -m "feat(api): FastAPI stub with fixture-replaying websocket and recordings"
```

---

### Task 2: Mock site with known traps (1:30–3:00) — Dev A and B develop against this

**Files:**
- Create: `targets/mock_site/index.html`, `product.html`, `cart.html`, `checkout.html`, `site.js`, `site.css`, `README.md`

- [ ] **Step 1: Write the pages**

```html
<!-- targets/mock_site/index.html -->
<!doctype html><html><head><meta charset="utf-8"><title>Mock Shop</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="site.css"><script defer src="site.js"></script></head>
<body>
<header><a href="/index.html" class="brand">Mock Shop</a>
  <button id="menu" class="hamburger" aria-label="">☰</button>
  <nav id="nav"><a href="/index.html">Home</a><a href="/product.html?id=1">Products</a><a href="/cart.html">Cart</a></nav>
  <a href="/cart.html" class="cart-icon">🛒</a></header>
<main><h1>Products</h1>
  <ul class="grid">
    <li><a href="/product.html?id=1"><span>Blue Mug</span><b>$12</b></a></li>
    <li><a href="/product.html?id=2"><span>Red Mug</span><b>$14</b></a></li>
  </ul></main>
<div id="consent"><p>We use cookies to improve your experience.</p><button id="consent-ok">OK</button></div>
</body></html>
```

```html
<!-- targets/mock_site/product.html -->
<!doctype html><html><head><meta charset="utf-8"><title>Product</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="site.css"><script defer src="site.js"></script></head>
<body>
<header><a href="/index.html" class="brand">Mock Shop</a><button id="menu" class="hamburger" aria-label="">☰</button>
<nav id="nav"><a href="/index.html">Home</a><a href="/cart.html">Cart</a></nav><a href="/cart.html" class="cart-icon">🛒</a></header>
<main><h1 id="title">Blue Mug</h1><p>$12</p>
  <button id="add" class="icon-only" title="">＋</button>   <!-- trap 2: icon-only, no accessible name -->
</main>
<div id="consent"><p>We use cookies to improve your experience.</p><button id="consent-ok">OK</button></div>
</body></html>
```

```html
<!-- targets/mock_site/cart.html -->
<!doctype html><html><head><meta charset="utf-8"><title>Cart</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="site.css"><script defer src="site.js"></script></head>
<body><header><a href="/index.html" class="brand">Mock Shop</a><nav id="nav"><a href="/index.html">Home</a></nav></header>
<main><h1>Cart</h1><p id="count">Cart (0 items)</p><a href="/checkout.html" class="btn">Checkout</a></main></body></html>
```

```html
<!-- targets/mock_site/checkout.html -->
<!doctype html><html><head><meta charset="utf-8"><title>Checkout</title><link rel="stylesheet" href="site.css"></head>
<body><main><h1>Checkout</h1><p>Payment page (no form on purpose: agents must stop here).</p></main></body></html>
```

```js
// targets/mock_site/site.js
const consent = document.getElementById('consent'), ok = document.getElementById('consent-ok');
if (consent && localStorage.getItem('consent') === '1') consent.remove();       // trap 1: overlay on every page
if (ok) ok.onclick = () => { localStorage.setItem('consent', '1'); consent.remove(); };
const menu = document.getElementById('menu'), nav = document.getElementById('nav');
if (menu) menu.onclick = () => nav.classList.toggle('open');                   // trap 3: hamburger-only nav on mobile
const add = document.getElementById('add');
if (add) add.onclick = () => { localStorage.setItem('cart', String(+(localStorage.getItem('cart') || 0) + 1)); add.textContent = '✓'; };
const count = document.getElementById('count');
if (count) count.textContent = `Cart (${localStorage.getItem('cart') || 0} items)`;
```

```css
/* targets/mock_site/site.css */
body{font-family:system-ui;margin:0} header{display:flex;gap:12px;padding:12px;border-bottom:1px solid #ddd;align-items:center}
.grid{display:flex;gap:16px;list-style:none;padding:16px} .grid li a{display:block;padding:12px;border:1px solid #ccc}
#consent{position:fixed;inset:0;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;color:#fff}
#consent p{margin-right:12px} #consent-ok{font-size:14px}
.hamburger{display:none;background:none;border:0;font-size:22px} .icon-only{font-size:22px;width:44px;height:44px}
@media (max-width:600px){ nav{display:none} nav.open{display:flex;flex-direction:column} .hamburger{display:block}
  #consent-ok{font-size:8px;width:16px;height:16px;overflow:hidden} }
```

```markdown
# targets/mock_site/README.md
Serve:  python -m http.server 8008 --directory targets/mock_site
Expose to Steel:  cloudflared tunnel --url http://localhost:8008   (or ngrok http 8008); use the https URL as the site URL.
Traps: (1) consent overlay on every page, tiny OK button on mobile; (2) icon-only add-to-cart button; (3) hamburger-only nav on mobile.
```

- [ ] **Step 2: Serve and check by hand**

Run: `python -m http.server 8008 --directory targets/mock_site`; open `http://localhost:8008/` at desktop width and at 375px.
Expected: overlay until OK; nav hidden on mobile until ☰; ＋ increments the cart; `/cart.html` shows the count; `/checkout.html` has no form.

- [ ] **Step 3: Commit**

```bash
git add targets/mock_site
git commit -m "feat(targets): mock site with three agent traps"
```

---

### Task 3: Explore — bounded crawler + one structured LLM call (3:00–7:00)

**Files:**
- Create: `crucible/explore/__init__.py`, `crucible/explore/crawl.py`, `crucible/explore/summarize.py`
- Test: `tests/explore/test_stop_rule.py`, `tests/explore/test_crawl.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/explore/test_stop_rule.py
from crucible.explore.crawl import StopRule, is_safe_href


def test_stops_after_two_pages_with_no_new_action_types():
    r = StopRule(max_pages=25, max_seconds=180)
    assert r.should_stop({"link:product", "form:search"}) is False
    assert r.should_stop({"link:product"}) is False      # 1 stale page
    assert r.should_stop({"form:search"}) is True        # 2 stale pages in a row


def test_stops_at_page_cap():
    r = StopRule(max_pages=2, max_seconds=180)
    r.should_stop({"a"})
    assert r.should_stop({"b"}) is True


def test_is_safe_href_blocks_destructive_and_offsite_links():
    assert is_safe_href("https://s.test/collections/all", "https://s.test/") is True
    assert is_safe_href("https://other.test/x", "https://s.test/") is False
    for bad in ("/account/logout", "/cart/clear", "/subscribe", "/unsubscribe", "/delete", "/cancel", "mailto:x", "tel:1", "#top"):
        assert is_safe_href(bad, "https://s.test/") is False
```

```python
# tests/explore/test_crawl.py
import pytest
from playwright.async_api import async_playwright

from crucible.explore.crawl import crawl

HOME = """<html><head><title>Shop</title></head><body>
<nav><a href="/p1">Products</a></nav><form><input type="search" name="q"></form>
<a href="/p1"><span>Blue Mug</span></a><button aria-label="">🛒</button><button>Add to cart</button></body></html>"""
P1 = """<html><head><title>Blue Mug</title></head><body><h1>Blue Mug</h1><button>Add to cart</button><a href="/cart">Cart</a></body></html>"""
CART = """<html><head><title>Cart</title></head><body><h1>Cart</h1><a href="/checkout">Checkout</a></body></html>"""
ROUTES = {"https://s.test/": HOME, "https://s.test/p1": P1, "https://s.test/cart": CART}


@pytest.mark.asyncio
async def test_crawl_collects_pages_and_action_types():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page()
        await page.route("**/*", lambda r: r.fulfill(status=200, content_type="text/html",
                                                     body=ROUTES.get(r.request.url, "<html></html>")))
        pages = await crawl(page, "https://s.test/", max_pages=10, max_seconds=30)
        await b.close()
    urls = [pg["url"] for pg in pages]
    assert "https://s.test/" in urls and "https://s.test/p1" in urls
    home = next(pg for pg in pages if pg["url"] == "https://s.test/")
    assert {"form:search", "button:add-to-cart", "button:icon-only"} <= set(home["action_types"])
```

Run: `pytest tests/explore -q` → Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 2: Write the crawler (read-only by construction: it only follows same-origin `<a href>` by GET; it never clicks buttons or submits forms)**

```python
# crucible/explore/crawl.py
from __future__ import annotations

import re
import time
from collections import deque
from urllib.parse import urljoin, urlparse

from playwright.async_api import Page

_DANGER = re.compile(r"logout|sign-?out|delete|remove|cancel|unsubscribe|subscribe|clear|/pay", re.I)
_ADD = re.compile(r"add to (cart|bag|basket)|buy now", re.I)
_SEARCH = re.compile(r"search|query|\bq\b", re.I)
_LOGIN = re.compile(r"log ?in|sign ?in|password", re.I)
_MENU = re.compile(r"menu|navigation", re.I)


def is_safe_href(href: str, base: str) -> bool:
    if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
        return False
    absu = urljoin(base, href)
    if urlparse(absu).netloc != urlparse(base).netloc:
        return False
    return not _DANGER.search(urlparse(absu).path)


class StopRule:
    """Stop when 2 consecutive pages add no new action type, or at max_pages, or at max_seconds."""

    def __init__(self, max_pages: int, max_seconds: int):
        self.max_pages, self.max_seconds = max_pages, max_seconds
        self.seen: set[str] = set()
        self.stale = self.pages = 0
        self.t0 = time.time()

    def should_stop(self, action_types: set[str]) -> bool:
        self.pages += 1
        new = action_types - self.seen
        self.seen |= action_types
        self.stale = 0 if new else self.stale + 1
        return self.stale >= 2 or self.pages >= self.max_pages or time.time() - self.t0 > self.max_seconds


_JS_SUMMARY = r"""() => {
  const txt = el => (el.innerText || el.getAttribute('aria-label') || el.getAttribute('title') || '').trim();
  return {
    title: document.title,
    headings: [...document.querySelectorAll('h1,h2')].slice(0, 8).map(txt),
    links: [...document.querySelectorAll('a[href]')].slice(0, 150).map(a => ({href: a.getAttribute('href'), text: txt(a).slice(0, 60)})),
    buttons: [...document.querySelectorAll('button,[role=button],input[type=submit]')].slice(0, 60)
      .map(b => ({text: txt(b).slice(0, 60),
                  // an icon/emoji-only button has no letters or digits and no aria-label
                  labelled: /[\p{L}\p{N}]/u.test(txt(b)) || !!b.getAttribute('aria-label')})),
    forms: [...document.querySelectorAll('form')].slice(0, 10)
      .map(f => [...f.querySelectorAll('input,select,textarea')].map(i => (i.name || i.type || '') + ':' + (i.type || '')).join(',')),
    excerpt: (document.body.innerText || '').slice(0, 800),
  };
}"""


def classify_actions(summary: dict) -> set[str]:
    types: set[str] = set()
    for l in summary["links"]:
        p = (l["href"] or "").lower()
        if any(k in p for k in ("product", "/p/", "item", "collection", "shop", "catalog")): types.add("link:product")
        elif any(k in p for k in ("cart", "bag", "basket")): types.add("link:cart")
        elif "checkout" in p: types.add("link:checkout")
        else: types.add("link:nav")
    for b in summary["buttons"]:
        t = b["text"]
        if _ADD.search(t): types.add("button:add-to-cart")
        elif _MENU.search(t): types.add("button:menu")
        elif not b["labelled"]: types.add("button:icon-only")
        else: types.add("button:other")
    for f in summary["forms"]:
        if _SEARCH.search(f): types.add("form:search")
        elif _LOGIN.search(f): types.add("form:login")
        else: types.add("form:other")
    return types


async def summarize_page(page: Page) -> dict:
    s = await page.evaluate(_JS_SUMMARY)
    s["url"] = page.url
    s["action_types"] = sorted(classify_actions(s))
    return s


async def crawl(page: Page, start: str, max_pages: int = 25, max_seconds: int = 180) -> list[dict]:
    rule = StopRule(max_pages, max_seconds)
    seen = {start.rstrip("/") + "/"}
    q: deque[str] = deque([start])
    out: list[dict] = []
    while q:
        url = q.popleft()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            await page.wait_for_timeout(500)
        except Exception:
            continue
        s = await summarize_page(page)
        out.append(s)
        if rule.should_stop(set(s["action_types"])):
            break
        for l in s["links"]:
            if is_safe_href(l["href"] or "", url):
                absu = urljoin(url, l["href"]).split("#")[0]
                key = absu.rstrip("/") + "/"
                if key not in seen:
                    seen.add(key)
                    q.append(absu)
    return out
```

Run: `pytest tests/explore -q` → Expected: `4 passed`

- [ ] **Step 3: Write the summariser (one structured Claude call) and the entry point**

```python
# crucible/explore/summarize.py
from __future__ import annotations

import json
import os

import anthropic

from crucible.schemas import SiteModel

MODEL = os.getenv("CRUCIBLE_MODEL", "claude-opus-5")

PROMPT = """You are mapping a website for automated agent testing. Below are summaries of {n} pages crawled
breadth-first from {url}.{hint}

Produce a SiteModel. Rules for `journeys` (exactly 3, ids find_product / add_to_cart / reach_checkout, in that order):
- Each `goal` must be executable by a browser agent starting at `entry_url`, name concrete pages/actions, and STOP
  before any payment, account creation or destructive action. Example:
  "On the products page open the first product, click add to cart, then open the cart page and confirm it lists 1 item."
- `entry_url` must be one of the crawled URLs.

Pages:
{pages}"""


async def summarize(url: str, pages: list[dict], hint: str | None) -> SiteModel:
    client = anthropic.AsyncAnthropic()
    slim = [{k: p[k] for k in ("url", "title", "headings", "action_types", "excerpt")}
            | {"links": p["links"][:25], "buttons": [b["text"] for b in p["buttons"][:15]]} for p in pages]
    msg = PROMPT.format(n=len(pages), url=url, pages=json.dumps(slim)[:60_000],
                        hint=f"\nOperator hint: {hint}" if hint else "")
    resp = await client.messages.parse(model=MODEL, max_tokens=4000,
                                       messages=[{"role": "user", "content": msg}], output_format=SiteModel)
    site = resp.parsed_output
    crawled = {p["url"] for p in pages}
    for j in site.journeys:
        if j.entry_url not in crawled:
            j.entry_url = url
    site.url = url
    return site
```

```python
# crucible/explore/__init__.py
"""explore(url, hint) per docs/plan.md §2.5. `page` is an optional extra: pass a Steel page so the audience
watches Explore live on stage; omit it to use a local Chromium and spend no Steel credits."""
from __future__ import annotations

from typing import Optional

from playwright.async_api import Page, async_playwright

from crucible.explore.crawl import crawl
from crucible.explore.summarize import summarize
from crucible.schemas import SiteModel


async def explore(url: str, hint: Optional[str] = None, page: Optional[Page] = None) -> SiteModel:
    if page is not None:
        return await summarize(url, await crawl(page, url), hint)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        try:
            pages = await crawl(await b.new_page(), url)
        finally:
            await b.close()
    return await summarize(url, pages, hint)
```

- [ ] **Step 4: Run on the mock site and cache the result**

Run (mock site on :8008):
```bash
mkdir -p targets/cache && python -c "
import asyncio
from dotenv import load_dotenv; load_dotenv()
from crucible.explore import explore
site = asyncio.run(explore('http://localhost:8008/'))
open('targets/cache/localhost:8008.site.json','w').write(site.model_dump_json(indent=2)); print(site.model_dump_json(indent=2))"
```
Expected: three journeys `find_product`, `add_to_cart`, `reach_checkout` with entry URLs on `localhost:8008` and goals naming pages; under 30 seconds. Give Dev A this file (URLs rewritten to the tunnel) for the M2 matrix.

- [ ] **Step 5: Commit**

```bash
git add crucible/explore tests/explore targets/cache/localhost:8008.site.json
git commit -m "feat(explore): bounded read-only crawler + structured SiteModel"
```

---

### Task 4: Orchestrator and real API wiring (7:00–8:00, pair with Dev A)

**Files:**
- Create: `crucible/orchestrator.py`
- Modify: `crucible/api/app.py` (`_pipeline_source`)
- Test: `tests/api/test_orchestrator_stubbed.py`

Dependencies per plan.md §5: writing it needs only the M0 signatures (`run_matrix`, `score`); running it end to end 🔴 waits for Dev A's `run_matrix` (due 7:00). `score()` stays a fixture stub until Dev C merges at 8:30.

- [ ] **Step 1: Write the failing test (all three stages stubbed)**

```python
# tests/api/test_orchestrator_stubbed.py
from pathlib import Path

import pytest

from crucible import orchestrator as O
from crucible.schemas import RunResult, ScoreCard, SiteModel

SITE = SiteModel.model_validate_json(Path("fixtures/site_model.json").read_text())
RES = RunResult.model_validate_json(Path("fixtures/run_result_completed.json").read_text())


@pytest.mark.asyncio
async def test_pipeline_emits_stages_in_order(monkeypatch):
    async def fake_explore(url, hint=None, page=None): return SITE
    async def fake_run_matrix(site, configs, engines, **kw): yield RES
    async def fake_score(site, results): return ScoreCard(overall=100, per_journey=[]), []
    monkeypatch.setattr(O, "explore", fake_explore)
    monkeypatch.setattr(O, "run_matrix", fake_run_matrix)
    monkeypatch.setattr(O, "score", fake_score)
    items = [i async for i in O.run_pipeline("http://x", engines={"browser_use": object()})]
    types = [(i["type"], i.get("name")) for i in items]
    assert types[0] == ("stage", "explore") and ("site_model", None) in types
    assert ("stage", "run") in types and ("run_result", None) in types
    assert types[-2] == ("result", None) and types[-1] == ("stage", "done")
```

Run: `pytest tests/api/test_orchestrator_stubbed.py -q` → Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 2: Write the orchestrator**

```python
# crucible/orchestrator.py
"""run_pipeline(url, hint, cached_site_model): explore → run_matrix → score, as one async generator of stream dicts."""
from __future__ import annotations

import argparse
import asyncio
import json
from typing import AsyncIterator, Optional

from crucible.explore import explore
from crucible.runner import run_matrix
from crucible.schemas import BASELINE, Config, RunResult, SiteModel, StageMarker
from crucible.scorer import score

MVP_CONFIGS = [BASELINE, Config(device="mobile", label="mobile"),
               Config(identity="returning", label="returning"), Config(country="CA", label="ca")]


def default_engines() -> dict:
    from crucible.engines.browser_use import BrowserUseEngine   # Dev A
    engines = {"browser_use": BrowserUseEngine()}
    try:
        from crucible.engines.claude_cu import ClaudeCUEngine   # Dev A, hour 11
        engines["claude_cu"] = ClaudeCUEngine()
    except Exception:
        pass
    return engines


async def run_pipeline(url: str, hint: Optional[str] = None, cached_site_model: Optional[dict] = None,
                       configs: Optional[list[Config]] = None, engines: Optional[dict] = None) -> AsyncIterator[dict]:
    engines = engines or default_engines()
    configs = configs or [c for c in MVP_CONFIGS if c.engine in engines]

    yield StageMarker(name="explore").model_dump()
    site = SiteModel.model_validate(cached_site_model) if cached_site_model else await explore(url, hint)
    yield {"type": "site_model", "site_model": site.model_dump()}

    yield StageMarker(name="run").model_dump()
    results: dict[tuple[str, str], RunResult] = {}
    async for item in run_matrix(site, configs, engines):
        yield item.model_dump()
        if isinstance(item, RunResult):
            results[(item.journey_id, item.config.label)] = item   # a retried cell keeps its last result

    yield StageMarker(name="score").model_dump()
    card, findings = await score(site, list(results.values()))
    yield {"type": "result", "scorecard": card.model_dump(), "findings": [f.model_dump() for f in findings]}
    yield StageMarker(name="done").model_dump()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url"); ap.add_argument("--hint"); ap.add_argument("--site-json")
    ap.add_argument("--configs", choices=["mvp2", "mvp"], default="mvp")
    a = ap.parse_args()
    cached = json.load(open(a.site_json)) if a.site_json else None
    cfgs = MVP_CONFIGS[:2] if a.configs == "mvp2" else None

    async def go():
        async for item in run_pipeline(a.url, a.hint, cached, cfgs):
            print(json.dumps(item)[:200])
    asyncio.run(go())


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Wire the API**

Replace `_pipeline_source` in `crucible/api/app.py`:

```python
from crucible.orchestrator import run_pipeline


def _pipeline_source(req: RunRequest):
    return run_pipeline(req.url, req.hint, req.cached_site_model)
```

- [ ] **Step 4: Tests, then the first end-to-end run with Dev A**

Run: `pytest tests/api -q` → Expected: `2 passed`

Until Dev C merges `score()` (8:30), add this stub at the top of `crucible/orchestrator.py` under a flag so M3 prep is not blocked:

```python
import os
if os.getenv("CRUCIBLE_STUB_SCORE"):
    async def score(site, results):                      # noqa: F811
        d = json.load(open("fixtures/demo_run.json"))
        r = next(i for i in d if i["type"] == "result")
        from crucible.schemas import Finding, ScoreCard
        return ScoreCard.model_validate(r["scorecard"]), [Finding.model_validate(f) for f in r["findings"]]
```

Run (Dev A's `run_matrix` merged, mock tunnel up): `CRUCIBLE_STUB_SCORE=1 python -m crucible.orchestrator https://<tunnel>/ --site-json targets/cache/localhost:8008.site.json --configs mvp2`
Expected order: `stage explore` → `site_model` → `stage run` → `session_started` / `run_event` … / `run_result` → `stage score` → `result` → `stage done`. Remove the stub when C merges.

- [ ] **Step 5: Commit**

```bash
git add crucible/orchestrator.py crucible/api/app.py tests/api/test_orchestrator_stubbed.py
git commit -m "feat: orchestrator explore→run→score wired into the API"
```

---

### Task 5: Scout the real target (8:00–10:00) — Dev A waits on this at 11:00

**Files:**
- Create: `targets/cache/static_scores.json`, `targets/README.md`, `targets/cache/<host>.site.json` ×3

- [ ] **Step 1:** Pick 3 mid-size e-commerce candidates (Shopify-style, cookie modal, product pages without login). For each, run Explore exactly as in Task 3 Step 4 with the real URL and save `targets/cache/<host>.site.json`. Note crawl time and whether each journey reads as executable.
- [ ] **Step 2:** Get each candidate's Cloudflare static score at https://isitagentready.com and record it (Dev C's `static.py` reads this file by hostname):

```json
{ "shop-a.example": 85, "shop-b.example": 62, "shop-c.example": 71 }
```

- [ ] **Step 3:** Pick the one with the highest static score and an obvious cookie modal (best contrast on stage). Write `targets/README.md` with pick, runner-up, fallback, and each one's crawl time. Announce in the team channel.
- [ ] **Step 4:** `git add targets && git commit -m "chore(targets): scouted real targets with static scores" && git push origin HEAD:main`

---

### Task 6: Integration lead (8:00–14:00)

Runs alongside Tasks 5–6. Owns `main` and the M3 (10:00) and M4 (14:00) checks in plan.md §4.

- [ ] **Step 1 (every merge):** `pytest tests/schemas tests/api tests/explore -q` green on `main`; `python -c "import crucible.orchestrator"` succeeds.
- [ ] **Step 2 (M3 at 10:00):** from Dev D's UI, paste the mock tunnel URL, press Run, and watch grid → score → finding with no manual step. If it fails, find which seat's contract broke and route it; do not patch another seat's module yourself.
- [ ] **Step 3 (Explore quality on the real target):** if a baseline run ends in `timeout`, the journey goal is under-specified. Fix it in `summarize.py`'s prompt (more concrete page names), re-run Explore, re-cache. This is the first thing to check before blaming the Runner.
- [ ] **Step 4 (M4 at 14:00):** MVP matrix on the headline site with at least one attributed finding and a real replay. Copy that run's recording to `targets/cache/recordings/stage.json` (Task 7 makes it the default dry-run).

---

### Task 7: Self-hosted demo store with three fixable traps (10:00–13:00) — needed by Dev A's fix loop at 14:00

**Files:**
- Create: `targets/demo_store/app.py`, `targets/demo_store/templates/base.html`, `index.html`, `product.html`, `cart.html`, `checkout.html`, `targets/demo_store/static/site.css`, `targets/demo_store/README.md`

- [ ] **Step 1: Write the Flask store (server-side cart so the fix loop can patch templates and restart)**

```python
# targets/demo_store/app.py
from flask import Flask, redirect, render_template, session, url_for

app = Flask(__name__)
app.secret_key = "crucible-demo"
PRODUCTS = {1: ("Blue Mug", 12), 2: ("Red Mug", 14)}


@app.get("/")
def index():
    return render_template("index.html", products=PRODUCTS)


@app.get("/product/<int:pid>")
def product(pid: int):
    name, price = PRODUCTS[pid]
    return render_template("product.html", pid=pid, name=name, price=price)


@app.post("/cart/add/<int:pid>")
def add(pid: int):
    session["cart"] = session.get("cart", 0) + 1
    return redirect(url_for("cart"))


@app.get("/cart")
def cart():
    return render_template("cart.html", count=session.get("cart", 0))


@app.get("/checkout")
def checkout():
    return render_template("checkout.html")


if __name__ == "__main__":
    app.run(port=8009)
```

```html
<!-- targets/demo_store/templates/base.html -->
<!doctype html><html><head><meta charset="utf-8"><title>{% block title %}Demo Store{% endblock %}</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/static/site.css"></head>
<body>
<header><a href="/" class="brand">Demo Store</a>
  <button class="hamburger" onclick="document.getElementById('nav').classList.toggle('open')" aria-label="">☰</button>
  <nav id="nav"><a href="/">Home</a><a href="/cart">Cart</a></nav></header>
<main>{% block body %}{% endblock %}</main>
<!-- TRAP 1 (fix: add role="dialog" aria-label="Cookie consent" and remove the mobile shrink in site.css) -->
<div id="consent"><p>We use cookies to improve your experience.</p>
  <button onclick="document.getElementById('consent').remove()">OK</button></div>
</body></html>
```

```html
<!-- targets/demo_store/templates/index.html -->
{% extends "base.html" %}{% block body %}<h1>Products</h1>
<ul class="grid">{% for pid, (name, price) in products.items() %}
<li><a href="/product/{{ pid }}"><span>{{ name }}</span><b>${{ price }}</b></a></li>{% endfor %}</ul>{% endblock %}
```

```html
<!-- targets/demo_store/templates/product.html -->
{% extends "base.html" %}{% block title %}{{ name }}{% endblock %}{% block body %}
<h1>{{ name }}</h1><p>${{ price }}</p>
<form method="post" action="/cart/add/{{ pid }}">
  <!-- TRAP 2 (fix: aria-label="Add to cart" or visible text) -->
  <button class="icon-only" title="">＋</button>
</form>{% endblock %}
```

```html
<!-- targets/demo_store/templates/cart.html -->
{% extends "base.html" %}{% block body %}<h1>Cart</h1><p>Cart ({{ count }} items)</p><a href="/checkout" class="btn">Checkout</a>{% endblock %}
```

```html
<!-- targets/demo_store/templates/checkout.html -->
{% extends "base.html" %}{% block body %}<h1>Checkout</h1><p>Payment page. No form on purpose: agents stop here.</p>{% endblock %}
```

```css
/* targets/demo_store/static/site.css */
body{font-family:system-ui;margin:0} header{display:flex;gap:12px;padding:12px;border-bottom:1px solid #ddd;align-items:center}
.grid{display:flex;gap:16px;list-style:none;padding:16px} .grid li a{display:block;padding:12px;border:1px solid #ccc}
#consent{position:fixed;inset:0;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;color:#fff}
.hamburger{display:none;background:none;border:0;font-size:22px} .icon-only{font-size:22px;width:44px;height:44px}
/* TRAP 3 (fix: keep nav links visible on mobile) */
@media (max-width:600px){ nav{display:none} nav.open{display:flex;flex-direction:column} .hamburger{display:block}
  #consent button{font-size:8px;width:16px;height:16px;overflow:hidden} }
```

```markdown
# targets/demo_store/README.md
Run:    flask --app targets/demo_store/app run --port 8009
Tunnel: cloudflared tunnel --url http://localhost:8009
Three one-line fixes for Dev A's fix loop (each trap is marked TRAP n in the source):
1. templates/base.html  → add role="dialog" aria-label="Cookie consent" to #consent; delete the mobile shrink rule in site.css
2. templates/product.html → add aria-label="Add to cart" to the ＋ button
3. static/site.css → replace `nav{display:none}` with `nav{display:flex}` in the mobile block
```

- [ ] **Step 2: Run, tunnel, and prove the traps**

Run: `flask --app targets/demo_store/app run --port 8009`, tunnel it, then Explore + `python -m crucible.orchestrator https://<tunnel>/ --configs mvp2`.
Expected: baseline completes `add_to_cart`; mobile stalls (consent). Cache the site model as `targets/cache/<tunnel-host>.site.json`.

- [ ] **Step 3: Commit and tell Dev A (waiting at 13:00)**

```bash
git add targets/demo_store
git commit -m "feat(targets): self-hosted demo store with three marked, fixable traps"
git push origin HEAD:main
```

---

### Task 8: Cache, hint shortcut, dry-run (14:00–18:00)

Most of this landed early: the API already loads `targets/cache/<host>.site.json` when `cached_site_model` is null (Task 1), records every run to `targets/cache/recordings/<run_id>.json` (Task 1), and `dry_run` replays `recordings/stage.json` when present, else the fixture (Task 1). The hint flows through `explore(url, hint)` (Task 3).

- [ ] **Step 1:** Cache Explore for both demo targets (headline site from Task 5, demo store from Task 7) by running Explore once more on each and saving `targets/cache/<host>.site.json`. Commit them.
- [ ] **Step 2:** After M4 (🔴 waits for Dev A's first full real-target run): copy `targets/cache/recordings/<that run_id>.json` to `targets/cache/recordings/stage.json`. Verify: `POST /runs {"dry_run": true}` replays it end to end in under 60 seconds and Dev D's `?demo=cached` shows the full flow with no backend work beyond the API.
- [ ] **Step 3:** Add a `--dry-run` flag to `crucible/orchestrator.py`'s `main()` that prints `replay_stream(RECORDINGS / "stage.json")` items, so the fallback can be rehearsed from a terminal too.
- [ ] **Step 4:** `pytest tests/api -q` green; `git commit -am "feat: cached site models, stage recording, dry-run fallback" && git push origin HEAD:main`.

---

### Task 9: Rehearsals (18:00–24:00)

- [ ] **Step 1:** Play the hostile judge in each of the five rehearsals: ask "what changed because of the proxy?", "why not Agent Checker?", "is that finding real or your agent's fault?" and note any answer that needed more than one sentence.
- [ ] **Step 2:** Keep `targets/README.md` current: headline target, fallback target, and the exact command to switch the UI to cached mode.

---

## Self-review against `docs/plan.md`

| plan.md Dev B row | Task here |
|---|---|
| 0:30–1:30 API stub on fixtures | Task 1 (Task 0 supplies the fixture if M0 has not) |
| 1:30–3:00 mock site | Task 2 |
| 3:00–7:00 Explore: crawler, allowlist, stopping rule, LLM → SiteModel | Task 3 |
| 7:00–8:00 orchestrator + swap stub | Task 4 |
| 8:00–10:00 scout 3 candidates, record static scores | Task 5 |
| 8:00–14:00 integration lead, Explore quality | Task 6 |
| 10:00–13:00 demo store behind a tunnel | Task 7 |
| 14:00–18:00 cache, hint, dry-run | Task 8 |
| 18:00–24:00 rehearsals | Task 9 |

Interfaces match §2: `explore(url, hint)` with an additive optional `page`; `run_matrix(site, configs, engines)` and `score(site, results)` called by their M0 signatures; API endpoints per §2.7 plus the `site_model` and `result` composite items the orchestrator emits (documented in `docs/api.md`).
