# Iris Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Iris front end as a fixture-driven, single-page React app that plays the full five-stage show (Input → Learning → Brief → Swarm → Report) exactly as the approved Claude Design frames, with the God's-Eye choreography, unit and end-to-end tests, and a Vercel deployment. No backend calls in this build.

**Architecture:** Vite + React 19 + TypeScript. One page that grows downward as stages land, driven by a `RunState` reducer fed by a `Player` that replays an authored demo script on a timeline. Textures (ASCII-from-image, Bayer dither) are canvas utilities; motion is `motion` (Framer Motion) plus CSS keyframes copied from the exports; the reticle, scan-line, number tick, text scramble and pixel-dissolve are small shared primitives. Every screen is a pure function of `RunState`, so a live stream can replace the Player later without touching the screens.

**Tech Stack:** Vite 8, React 19, TypeScript 5, Tailwind CSS 4 (`@tailwindcss/vite`), `motion` 13, `dotted-map` 3, Vitest 5 (jsdom + canvas mocks), Playwright 1.63, Vercel CLI (logged in as `smitsp11`, scope `smitsp11s-projects`).

**Sources of truth (read before each task):**
- `docs/design-brief.md` — tokens, motion vocabulary, choreography timings (§5), asset recipes (§6).
- `docs/ui-flow.md` — what each screen means and must achieve.
- `design/frames/*.dc.html` — the exported frames; inline styles are exact. `design/EXTRACTION.md` — verbatim style extraction per frame (produced by a subagent; if a value in EXTRACTION.md conflicts with the .dc.html, the .dc.html wins).
- `design/assets/` — dot-field.png, world-dots.png, computer-globe-*.png.
- `crucible/schemas.py` and `fixtures/demo_run.json` on `main` — the backend contract the frontend types mirror.

**Non-goals:** no websocket, no fetch, no backend integration; no mobile layout (stage/projector at 1440×900 and laptop 1280×800 only); no auth.

---

## File structure

```
web/
  index.html                       fonts preconnect + root
  package.json  vite.config.ts  tsconfig.json  vitest.config.ts  playwright.config.ts
  public/assets/                   copied from design/assets (dot-field.png, world-dots.png, computer-globe-monitor.png)
  src/
    main.tsx                       mounts <App/>
    App.tsx                        page shell: TopBar + stages that render as state arrives
    styles/tokens.css              CSS variables (palette, type), keyframes (irisPulse, irisScan, irisBlink), base
    types.ts                       TS mirrors of schemas.py + Iris additions (Source, Persona, StressTest, StreamItem)
    data/iris_demo.json            the authored demo show (site, sources, personas, runs, findings, scorecard)
    data/script.ts                 demo JSON → timed StreamItem[] (the choreography timeline)
    state/reducer.ts               StreamItem → RunState (pure)
    state/player.ts                plays a script on a clock: play/pause/speed/seek, dispatches items
    state/usePlayer.ts             React hook around Player; reads ?speed= and ?stage= for tests/rehearsal
    texture/ascii.ts               image → ASCII grid (pure, canvas-in)
    texture/dither.ts              image → Bayer-dithered canvas (pure)
    texture/AsciiImage.tsx         <pre> that renders ascii() of a src (or a seeded procedural texture when no src)
    texture/DitherImage.tsx        <canvas> that renders dither() of a src
    primitives/Reticle.tsx         4-corner bracket; moves between targets with layoutId
    primitives/ScanLine.tsx        orange line sweeping a panel (CSS irisScan)
    primitives/NumberTick.tsx      tweens a number with motion's animate()
    primitives/TextScramble.tsx    decode-in text effect
    primitives/PixelDissolve.tsx   16px block overlay that resolves to reveal children
    primitives/Chip.tsx  Pill.tsx  Mono.tsx  Serif.tsx   tiny typographic atoms
    components/TopBar.tsx          wordmark + stage bar + session counter (+ CACHED pill)
    screens/Input.tsx              Frame 1
    screens/Learning.tsx           Frame 2 (SourceWall, SiteMap)
    screens/Brief.tsx              Frame 3 (WorldDots, PersonaCard, StressTable)
    screens/Swarm.tsx              Frame 4 (FeedCard)
    screens/Report.tsx             Frame 5 (ScoreBlock, FlagRow, FlagDetail)
  test/                            vitest unit tests (reducer, script, ascii, dither, player)
  e2e/                             playwright: demo.spec.ts drives the whole show and screenshots each stage
```

Rule for every component: **props in, JSX out, no data fetching, no timers** (timers live only in `Player`). Every screen renders from `RunState` only.

---

## Task 1: Scaffold, tokens, fonts, background

**Files:**
- Create: `web/` via Vite, `web/src/styles/tokens.css`, `web/index.html` (edit), `web/vite.config.ts`, `web/public/assets/*`
- Test: `web/test/smoke.test.tsx`

- [ ] **Step 1: Scaffold and install**

```bash
cd /Users/smit/conductor/workspaces/pasta/belmopan
npm create vite@latest web -- --template react-ts
cd web
npm i motion dotted-map
npm i -D tailwindcss @tailwindcss/vite vitest @vitest/browser jsdom @testing-library/react @testing-library/jest-dom @playwright/test
npx playwright install chromium
mkdir -p public/assets && cp ../design/assets/dot-field.png ../design/assets/world-dots.png ../design/assets/computer-globe-monitor.png public/assets/
```

- [ ] **Step 2: Vite config with Tailwind and test settings**

```ts
// web/vite.config.ts
/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  test: {
    environment: "jsdom",
    setupFiles: ["./test/setup.ts"],
    include: ["test/**/*.test.{ts,tsx}"],
  },
});
```

```ts
// web/test/setup.ts
import "@testing-library/jest-dom/vitest";
// canvas is not implemented in jsdom; texture tests inject their own pixel readers.
```

- [ ] **Step 3: index.html with fonts (exact Google Fonts line from the exports)**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Iris</title>
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 4: tokens.css (values verbatim from design-brief §2 and the export `<style>` blocks)**

```css
/* web/src/styles/tokens.css */
@import "tailwindcss";

:root {
  --paper: #FAF7F2;
  --ink: #141414;
  --scan: #FF5A1F;
  --scan-soft: #FFE6DA;
  --ok: #1F9D55;
  --stall: #D93025;
  --muted: #8A8580;
  --line: rgba(20,20,20,0.18);
  --line-soft: rgba(20,20,20,0.10);
  --pastel-1: #FFD9CF; --pastel-2: #F3E9D2; --pastel-3: #E5DDF5; --pastel-4: #D8ECE3;
  --font-serif: "Instrument Serif", Georgia, serif;
  --font-sans: Inter, system-ui, sans-serif;
  --font-mono: "Geist Mono", ui-monospace, monospace;
}

html, body { margin: 0; padding: 0; }
body {
  color: var(--ink);
  font-family: var(--font-sans);
  background-color: var(--paper);
  background-image:
    radial-gradient(ellipse 72% 46% at 50% 58%, #FAF7F2 0%, rgba(250,247,242,0.9) 48%, rgba(250,247,242,0) 80%),
    url("/assets/dot-field.png");
  background-repeat: no-repeat, no-repeat;
  background-position: center 56%, center top;
  background-size: auto, 100% auto;
  background-attachment: fixed, fixed;
}
a { color: var(--scan); text-decoration: none; }
a:hover { color: var(--ink); }

@keyframes irisPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
@keyframes irisScan  { 0% { top: 2%; } 100% { top: 96%; } }
@keyframes irisBlink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.serif { font-family: var(--font-serif); font-weight: 400; letter-spacing: -0.015em; line-height: 0.96; }
.mono  { font-family: var(--font-mono); letter-spacing: 0.1em; text-transform: uppercase; }
.h1    { font-size: clamp(40px, 6vw, 76px); }
```

- [ ] **Step 5: Smoke test then commit**

```tsx
// web/test/smoke.test.tsx
import { render, screen } from "@testing-library/react";
import App from "../src/App";
it("renders the wordmark", () => { render(<App />); expect(screen.getByText("Iris")).toBeInTheDocument(); });
```

Replace `src/App.tsx` with a minimal shell: `export default function App(){ return <div className="serif" style={{fontSize:30}}>Iris</div> }` and import `./styles/tokens.css` in `main.tsx`.

Run: `cd web && npx vitest run` → Expected: `1 passed`. Run: `npm run build` → Expected: `dist/` built with no type errors.

```bash
git add web && git commit -m "feat(web): scaffold Vite+React+Tailwind, tokens, fonts, dot-field background"
```

---

## Task 2: Types mirroring schemas.py, plus Iris additions

**Files:**
- Create: `web/src/types.ts`
- Test: `web/test/types.test.ts`

- [ ] **Step 1: Write the types (backend fields verbatim from `crucible/schemas.py`; Iris additions marked)**

```ts
// web/src/types.ts
// Backend mirrors (crucible/schemas.py) --------------------------------------
export type Device = "desktop" | "mobile";
export type Identity = "fresh" | "returning";
export type EngineName = "browser_use" | "claude_cu" | "openai_cu";
export type Outcome = "none" | "step_ok" | "completed" | "stalled" | "harness_error";
export type TerminalOutcome = "completed" | "stalled" | "harness_error";
export type FailureCategory = "cookie_wall" | "captcha" | "hidden_nav" | "icon_only_control" | "ambiguous_cta"
  | "geo_block" | "infinite_scroll" | "login_wall" | "layout_shift" | "timeout" | "other";
export type AttributedTo = "device" | "identity" | "country" | "engine" | "site";
export type StageName = "explore" | "run" | "score" | "fix" | "done";

export interface Journey { id: string; name: string; goal: string; entry_url: string }
export interface SiteModel { url: string; brand: string; category: string; description: string; audience_guess: string[]; journeys: Journey[] }
export interface Config { device: Device; identity: Identity; country: string; engine: EngineName; label: string }
export interface RunEvent { type: "run_event"; run_id: string; session_id: string; journey_id: string; config: Config;
  step_index: number; timestamp: string; action: string; observation: string; screenshot_ref: string | null; outcome: Outcome }
export interface SessionStarted { type: "session_started"; run_id: string; session_id: string; journey_id: string; config: Config;
  viewer_url: string; replay_url: string; hls_url: string; timestamp: string }
export interface RunResult { type: "run_result"; run_id: string; journey_id: string; config: Config; session_id: string | null;
  outcome: TerminalOutcome; attempt: number; events: RunEvent[]; replay_url: string | null; hls_url: string | null;
  final_screenshot_ref: string | null; failure_step_index: number | null; replay_offset_s: number | null;
  harness_reason: string | null; stall_hint: string | null }
export interface StageMarker { type: "stage"; name: StageName; timestamp: string }
export interface Finding { id: string; journey_id: string; config: Config; category: FailureCategory; description: string;
  attributed_to: AttributedTo; engine_consensus: boolean; session_id: string | null; step_index: number | null;
  replay_url: string | null; replay_offset_s: number | null; proposed_fix: string }
export interface JourneyScore { journey_id: string; score: number; completed: number; stalled: number; harness_errors: number }
export interface ScoreCard { overall: number; static_score: number | null; per_journey: JourneyScore[] }

// Iris additions (frontend contract; Dev B mirrors these in the API later) ----
export interface Source { id: string; name: string; kind: "reviews" | "forum" | "appstore" | "help" | "competitor" | "social" | "support";
  pastel: 1 | 2 | 3 | 4; thumbnail: string | null }
export interface Quote { source_id: string; text: string; date: string; url: string | null }
export interface Persona { id: string; segment: string; config: Config; journey_id: string; goal: string; evidence: Quote; pastel: 1 | 2 | 3 | 4;
  run_id: string; pair_id: string | null }
export interface StressTest { probe: string; why: string; source: string }
export interface SiteNode { path: string; parent: string | null; journey: number | null }

export type SourceRead = { type: "source_read"; source_id: string; quotes: Quote[]; timestamp: string };
export type SiteModelItem = { type: "site_model"; site_model: SiteModel; nodes: SiteNode[] };
export type BriefItem = { type: "brief"; personas: Persona[]; stress_tests: StressTest[] };
export type ResultItem = { type: "result"; scorecard: ScoreCard; findings: Finding[]; affected: Record<string, { persona_ids: string[]; share: number }> };
export type StreamItem = StageMarker | SourceRead | SiteModelItem | BriefItem | SessionStarted | RunEvent | RunResult | ResultItem;

// Derived UI state ------------------------------------------------------------
export type FeedStatus = "running" | "completed" | "stalled" | "harness_error";
export interface Feed { run_id: string; session_id: string; persona_id: string; config: Config; journey_id: string;
  viewer_url: string; last_action: string; last_observation: string; step: number; status: FeedStatus; final_screenshot_ref: string | null }
export interface RunState {
  stage: StageName | "idle";
  url: string;
  sources: Source[];                       // all known sources (from brief data), order = wall order
  read: Record<string, Quote[]>;           // source_id -> quotes surfaced
  reading: string | null;                  // source_id under the reticle
  site: SiteModel | null; nodes: SiteNode[];
  personas: Persona[]; stress_tests: StressTest[];
  feeds: Record<string, Feed>;             // keyed by run_id (a retry replaces)
  focus: string | null;                    // run_id under the reticle in the swarm
  scorecard: ScoreCard | null; findings: Finding[]; affected: ResultItem["affected"];
}
```

- [ ] **Step 2: Type-level test (compiles = passes) and commit**

```ts
// web/test/types.test.ts
import type { RunState, StreamItem } from "../src/types";
it("types compile", () => {
  const item: StreamItem = { type: "stage", name: "explore", timestamp: "2026-09-13T00:00:00Z" };
  const s: Partial<RunState> = { stage: "idle" };
  expect(item.type).toBe("stage"); expect(s.stage).toBe("idle");
});
```

Run: `npx vitest run` → `2 passed`. Commit: `git commit -am "feat(web): types mirroring schemas + Iris stream additions"`.

---

## Task 3: The authored demo fixture

**Files:**
- Create: `web/src/data/iris_demo.json`
- Test: `web/test/fixture.test.ts`

The show must match the frames' sample data exactly (brand Northwind Outfitters, eight personas, quotes, flags). Author it once, here, and every screen reads it.

- [ ] **Step 1: Write the fixture**

```json
{
  "url": "https://northwindoutfitters.com",
  "site_model": {
    "url": "https://northwindoutfitters.com", "brand": "Northwind Outfitters", "category": "ecommerce / outdoor apparel",
    "description": "Mid-size outdoor clothing store with a cookie consent modal, a promo-code field at checkout and a hamburger-only mobile nav.",
    "audience_guess": ["outdoor apparel shoppers", "returning gear buyers", "gift buyers"],
    "journeys": [
      {"id": "find_product", "name": "Find a jacket", "goal": "From the home page open the Jackets collection and open the Alpine Shell product page.", "entry_url": "https://northwindoutfitters.com/"},
      {"id": "add_to_cart", "name": "Add it to the cart", "goal": "Open the Alpine Shell product page, add it to the cart, then open the cart page and confirm it lists 1 item.", "entry_url": "https://northwindoutfitters.com/"},
      {"id": "reach_checkout", "name": "Reach checkout", "goal": "With one item in the cart, reach the checkout page and stop before payment.", "entry_url": "https://northwindoutfitters.com/cart"}
    ]
  },
  "nodes": [
    {"path": "/", "parent": null, "journey": null},
    {"path": "/collections/jackets", "parent": "/", "journey": 1},
    {"path": "/products/alpine-shell", "parent": "/collections/jackets", "journey": null},
    {"path": "/cart", "parent": "/products/alpine-shell", "journey": 2},
    {"path": "/checkout", "parent": "/cart", "journey": 3},
    {"path": "/collections/pants", "parent": "/", "journey": null},
    {"path": "/pages/shipping", "parent": "/", "journey": null}
  ],
  "sources": [
    {"id": "trustpilot", "name": "Trustpilot", "kind": "reviews", "pastel": 2, "thumbnail": null},
    {"id": "google", "name": "Google Reviews", "kind": "reviews", "pastel": 3, "thumbnail": null},
    {"id": "reddit", "name": "Reddit r/Outdoors", "kind": "forum", "pastel": 1, "thumbnail": null},
    {"id": "appstore", "name": "App Store", "kind": "appstore", "pastel": 3, "thumbnail": null},
    {"id": "help", "name": "Help Centre", "kind": "help", "pastel": 4, "thumbnail": null},
    {"id": "competitor", "name": "Competitor: Arc'teryx", "kind": "competitor", "pastel": 1, "thumbnail": null},
    {"id": "youtube", "name": "YouTube Reviews", "kind": "social", "pastel": 4, "thumbnail": null},
    {"id": "support", "name": "Support Tickets", "kind": "support", "pastel": 2, "thumbnail": null},
    {"id": "instagram", "name": "Instagram Comments", "kind": "social", "pastel": 3, "thumbnail": null}
  ],
  "reads": [
    {"source_id": "trustpilot", "quotes": [{"source_id": "trustpilot", "text": "checkout resets on my phone every time", "date": "Jun 2026", "url": "https://www.trustpilot.com/review/northwindoutfitters.com"}, {"source_id": "trustpilot", "text": "I tapped OK four times before it took. Gave up and bought elsewhere.", "date": "Jun 2026", "url": "https://www.trustpilot.com/review/northwindoutfitters.com"}]},
    {"source_id": "google", "quotes": [{"source_id": "google", "text": "sizing chart is buried three clicks deep", "date": "May 2026", "url": null}]},
    {"source_id": "reddit", "quotes": [{"source_id": "reddit", "text": "nobody says which shell is actually waterproof", "date": "Jun 2026", "url": null}, {"source_id": "reddit", "text": "coupon field rejects valid codes", "date": "Jun 2026", "url": null}]},
    {"source_id": "appstore", "quotes": [{"source_id": "appstore", "text": "delivery estimate changes at checkout", "date": "May 2026", "url": null}]},
    {"source_id": "help", "quotes": [{"source_id": "help", "text": "CAD pricing is not shown until payment", "date": "Apr 2026", "url": null}]},
    {"source_id": "competitor", "quotes": []},
    {"source_id": "youtube", "quotes": []},
    {"source_id": "support", "quotes": [{"source_id": "support", "text": "cannot order more than five of one item", "date": "Jun 2026", "url": null}]},
    {"source_id": "instagram", "quotes": []}
  ],
  "personas": [
    {"id": "p1", "segment": "First-time mobile shopper, Canada", "config": {"device": "mobile", "identity": "fresh", "country": "CA", "engine": "browser_use", "label": "mobile"}, "journey_id": "add_to_cart", "goal": "Find a jacket and add it to the cart.", "evidence": {"source_id": "trustpilot", "text": "the mobile site keeps resetting my cart", "date": "Jun 2026", "url": null}, "pastel": 1, "run_id": "r1", "pair_id": null},
    {"id": "p2", "segment": "Returning gear buyer, United States", "config": {"device": "desktop", "identity": "returning", "country": "US", "engine": "browser_use", "label": "returning"}, "journey_id": "find_product", "goal": "Reorder last winter's shell in a new size.", "evidence": {"source_id": "google", "text": "sizing chart is buried three clicks deep", "date": "May 2026", "url": null}, "pastel": 3, "run_id": "r2", "pair_id": null},
    {"id": "p3", "segment": "Coupon hunter, United States", "config": {"device": "desktop", "identity": "returning", "country": "US", "engine": "browser_use", "label": "returning"}, "journey_id": "reach_checkout", "goal": "Apply a promo code before paying.", "evidence": {"source_id": "reddit", "text": "coupon field rejects valid codes", "date": "Jun 2026", "url": null}, "pastel": 2, "run_id": "r3", "pair_id": "p4"},
    {"id": "p4", "segment": "Coupon hunter, United States", "config": {"device": "mobile", "identity": "returning", "country": "US", "engine": "browser_use", "label": "mobile"}, "journey_id": "reach_checkout", "goal": "Apply a promo code before paying.", "evidence": {"source_id": "reddit", "text": "coupon field rejects valid codes", "date": "Jun 2026", "url": null}, "pastel": 2, "run_id": "r4", "pair_id": "p3"},
    {"id": "p5", "segment": "Cold-weather researcher, Germany", "config": {"device": "desktop", "identity": "fresh", "country": "DE", "engine": "browser_use", "label": "country:DE"}, "journey_id": "find_product", "goal": "Compare waterproof ratings across two shells.", "evidence": {"source_id": "reddit", "text": "nobody says which shell is actually waterproof", "date": "Jun 2026", "url": null}, "pastel": 3, "run_id": "r5", "pair_id": null},
    {"id": "p6", "segment": "Gift buyer, United Kingdom", "config": {"device": "mobile", "identity": "fresh", "country": "GB", "engine": "browser_use", "label": "country:GB"}, "journey_id": "reach_checkout", "goal": "Buy a gift and ship it by Friday.", "evidence": {"source_id": "trustpilot", "text": "delivery estimate changes at checkout", "date": "May 2026", "url": null}, "pastel": 1, "run_id": "r6", "pair_id": null},
    {"id": "p7", "segment": "Price-sensitive local, Canada", "config": {"device": "mobile", "identity": "returning", "country": "CA", "engine": "browser_use", "label": "country:CA"}, "journey_id": "add_to_cart", "goal": "Check whether prices show in CAD.", "evidence": {"source_id": "help", "text": "CAD pricing is not shown until payment", "date": "Apr 2026", "url": null}, "pastel": 4, "run_id": "r7", "pair_id": null},
    {"id": "p8", "segment": "Club bulk buyer, United States", "config": {"device": "desktop", "identity": "returning", "country": "US", "engine": "browser_use", "label": "returning"}, "journey_id": "add_to_cart", "goal": "Order six jackets for a club trip.", "evidence": {"source_id": "support", "text": "cannot order more than five of one item", "date": "Jun 2026", "url": null}, "pastel": 2, "run_id": "r8", "pair_id": null}
  ],
  "stress_tests": [
    {"probe": "checkout on mobile", "why": "3 reviewers report resets", "source": "Trustpilot"},
    {"probe": "coupon field", "why": "rejects valid codes", "source": "Reddit"},
    {"probe": "country pricing", "why": "CAD not shown", "source": "Help centre"}
  ],
  "runs": [
    {"run_id": "r1", "persona_id": "p1", "session_id": "sess-r1", "start_url": "https://northwindoutfitters.com/collections/jackets", "outcome": "completed", "failure_step_index": null,
     "steps": [["opened the jackets collection", "/collections/jackets"], ["found the jacket… adding to cart", "/products/alpine-shell"], ["cart shows 1 item", "/cart"]]},
    {"run_id": "r2", "persona_id": "p2", "session_id": "sess-r2", "start_url": "https://northwindoutfitters.com/products/alpine-shell", "outcome": "completed", "failure_step_index": null,
     "steps": [["opened the size guide… chart is an image with no text… scrolling", "/products/alpine-shell"], ["found last season's size in order history", "/account/orders"], ["cart shows 1 item… opening checkout", "/cart"]]},
    {"run_id": "r3", "persona_id": "p3", "session_id": "sess-r3", "start_url": "https://northwindoutfitters.com/checkout", "outcome": "completed", "failure_step_index": null,
     "steps": [["typed promo code SPRING20… the field cleared itself… retyping", "/checkout"], ["promo code accepted on the third attempt", "/checkout"]]},
    {"run_id": "r4", "persona_id": "p4", "session_id": "sess-r4", "start_url": "https://northwindoutfitters.com/cart", "outcome": "stalled", "failure_step_index": 4,
     "steps": [["looking for the cart… the ＋ button has no label… trying again", "/products/alpine-shell"], ["tapped OK on the cookie dialog… still there", "/cart"], ["tapped OK again… overlay keeps intercepting clicks", "/cart"], ["overlay keeps intercepting clicks", "/cart"]]},
    {"run_id": "r5", "persona_id": "p5", "session_id": "sess-r5", "start_url": "https://northwindoutfitters.com/collections/jackets", "outcome": "completed", "failure_step_index": null,
     "steps": [["comparing Alpine Shell and Ridge Shell", "/collections/jackets"], ["compared both shells and reached the size guide", "/products/ridge-shell"]]},
    {"run_id": "r6", "persona_id": "p6", "session_id": "sess-r6", "start_url": "https://northwindoutfitters.com/checkout", "outcome": "completed", "failure_step_index": null,
     "steps": [["added the gift wrap option", "/cart"], ["reached order confirmation in 4 steps", "/checkout/confirmation"]]},
    {"run_id": "r7", "persona_id": "p7", "session_id": "sess-r7", "start_url": "https://northwindoutfitters.com/cart", "outcome": "stalled", "failure_step_index": 3,
     "steps": [["switched country to CA… prices still shown in USD", "/cart"], ["looking for a currency selector… none in the header", "/cart"], ["prices still in USD at checkout", "/checkout"]]},
    {"run_id": "r8", "persona_id": "p8", "session_id": "sess-r8", "start_url": "https://northwindoutfitters.com", "outcome": "harness_error", "failure_step_index": null,
     "steps": [["session ended before the first step", "/"]]}
  ],
  "findings": [
    {"id": "f1", "journey_id": "reach_checkout", "config": {"device": "mobile", "identity": "returning", "country": "US", "engine": "browser_use", "label": "mobile"}, "category": "cookie_wall", "description": "A consent overlay covers the page and its OK button is 16px on mobile.", "attributed_to": "device", "engine_consensus": false, "session_id": "sess-r4", "step_index": 4, "replay_url": "https://app.steel.dev/sessions/sess-r4", "replay_offset_s": 41, "proposed_fix": "Give the dialog role=\"dialog\" and an aria-label; make the accept button at least 44×44px on mobile."},
    {"id": "f2", "journey_id": "add_to_cart", "config": {"device": "desktop", "identity": "fresh", "country": "US", "engine": "browser_use", "label": "baseline"}, "category": "icon_only_control", "description": "The add-to-cart button is an unlabelled ＋ icon; agents cannot tell what it does.", "attributed_to": "site", "engine_consensus": true, "session_id": "sess-r1", "step_index": 2, "replay_url": "https://app.steel.dev/sessions/sess-r1", "replay_offset_s": 18, "proposed_fix": "Add aria-label=\"Add to cart\" (and ideally visible text) to the ＋ button."},
    {"id": "f3", "journey_id": "add_to_cart", "config": {"device": "mobile", "identity": "returning", "country": "CA", "engine": "browser_use", "label": "country:CA"}, "category": "geo_block", "description": "Canadian visitors are shown USD prices with no currency selector until the payment step.", "attributed_to": "country", "engine_consensus": false, "session_id": "sess-r7", "step_index": 3, "replay_url": "https://app.steel.dev/sessions/sess-r7", "replay_offset_s": 33, "proposed_fix": "Detect country from the session and show CAD on product and cart pages, with a visible currency selector in the header."},
    {"id": "f4", "journey_id": "find_product", "config": {"device": "mobile", "identity": "fresh", "country": "GB", "engine": "browser_use", "label": "country:GB"}, "category": "hidden_nav", "description": "On mobile the only route to collections is a hamburger menu with an empty aria-label.", "attributed_to": "device", "engine_consensus": false, "session_id": "sess-r6", "step_index": 1, "replay_url": "https://app.steel.dev/sessions/sess-r6", "replay_offset_s": 6, "proposed_fix": "Expose primary navigation links in the DOM on all viewports and give the menu toggle aria-expanded and an accessible name."}
  ],
  "affected": {
    "f1": {"persona_ids": ["p4", "p1", "p7"], "share": 0.41},
    "f2": {"persona_ids": ["p1", "p2", "p3", "p5", "p8"], "share": 0.63},
    "f3": {"persona_ids": ["p7", "p1"], "share": 0.18},
    "f4": {"persona_ids": ["p1", "p6", "p7"], "share": 0.29}
  },
  "scorecard": {"overall": 58, "static_score": 85, "per_journey": [
    {"journey_id": "find_product", "score": 66.7, "completed": 2, "stalled": 0, "harness_errors": 0},
    {"journey_id": "add_to_cart", "score": 50.0, "completed": 1, "stalled": 1, "harness_errors": 1},
    {"journey_id": "reach_checkout", "score": 57.1, "completed": 2, "stalled": 1, "harness_errors": 0}]}
}
```

- [ ] **Step 2: Fixture invariants test, then commit**

```ts
// web/test/fixture.test.ts
import demo from "../src/data/iris_demo.json";
it("fixture is internally consistent", () => {
  const personaIds = new Set(demo.personas.map(p => p.id));
  const runIds = new Set(demo.runs.map(r => r.run_id));
  expect(demo.personas).toHaveLength(8);
  for (const p of demo.personas) expect(runIds.has(p.run_id)).toBe(true);
  for (const r of demo.runs) expect(personaIds.has(r.persona_id)).toBe(true);
  const pair = demo.personas.filter(p => p.pair_id);
  expect(pair).toHaveLength(2);
  const [a, b] = pair;
  expect(a.config.device).not.toBe(b.config.device);
  expect(a.config.identity).toBe(b.config.identity); expect(a.config.country).toBe(b.config.country);
  for (const f of demo.findings) expect(Object.keys(demo.affected)).toContain(f.id);
  expect(demo.sources.map(s => s.id)).toEqual(demo.reads.map(r => r.source_id));
});
```

Run: `npx vitest run` → `3 passed`. Commit: `git commit -am "feat(web): authored Iris demo fixture"`.

---

## Task 4: Script — fixture → timed StreamItem[] (the choreography timeline)

**Files:**
- Create: `web/src/data/script.ts`
- Test: `web/test/script.test.ts`

Timings from design-brief §5. `t` is milliseconds from play start at speed 1.

- [ ] **Step 1: Write the failing test**

```ts
// web/test/script.test.ts
import { buildScript } from "../src/data/script";
import demo from "../src/data/iris_demo.json";
it("orders stages and spaces items per the choreography", () => {
  const s = buildScript(demo as any);
  const types = s.map(x => x.item.type);
  const stageNames = s.filter(x => x.item.type === "stage").map(x => (x.item as any).name);
  expect(stageNames).toEqual(["explore", "run", "score", "done"]);
  expect(types.indexOf("source_read")).toBeGreaterThan(types.indexOf("stage"));
  expect(types.indexOf("site_model")).toBeGreaterThan(types.indexOf("source_read"));
  expect(types.indexOf("brief")).toBeGreaterThan(types.indexOf("site_model"));
  expect(types.lastIndexOf("run_result")).toBeLessThan(types.indexOf("result"));
  for (let i = 1; i < s.length; i++) expect(s[i].t).toBeGreaterThanOrEqual(s[i - 1].t);
  const starts = s.filter(x => x.item.type === "session_started");
  expect(starts).toHaveLength(8);
  const total = s[s.length - 1].t;
  expect(total).toBeGreaterThan(30_000); expect(total).toBeLessThan(120_000);
});
```

- [ ] **Step 2: Implement**

```ts
// web/src/data/script.ts
import type { RunEvent, RunResult, SessionStarted, StreamItem } from "../types";

export type Cue = { t: number; item: StreamItem };
type Demo = typeof import("./iris_demo.json");

const T = {
  research_first: 800, research_gap: 1500,     // §5.2 reticle hops per card
  site_first: 1200, site_gap: 650,             // §5.3 node reveals
  brief_after: 900,
  swarm_start_gap: 250, step_gap: 2200, run_stagger: 900,  // feeds mount fast, steps unfold slowly
  score_after: 1500, done_after: 2500,
};
const iso = (ms: number) => new Date(Date.UTC(2026, 8, 13, 0, 0, 0) + ms).toISOString();

export function buildScript(d: Demo): Cue[] {
  const cues: Cue[] = [];
  let t = 0;
  const push = (dt: number, item: StreamItem) => { t += dt; cues.push({ t, item }); };

  push(0, { type: "stage", name: "explore", timestamp: iso(t) });
  // Research and site map run in parallel: interleave by time, not by order.
  const research: Cue[] = []; let tr = t + T.research_first;
  for (const r of d.reads) { research.push({ t: tr, item: { type: "source_read", source_id: r.source_id, quotes: r.quotes as any, timestamp: iso(tr) } }); tr += T.research_gap; }
  const site: Cue[] = []; let ts = t + T.site_first;
  for (let i = 1; i <= d.nodes.length; i++) {           // reveal nodes one at a time by re-sending the growing list
    site.push({ t: ts, item: { type: "site_model", site_model: d.site_model as any, nodes: d.nodes.slice(0, i) as any } }); ts += T.site_gap;
  }
  const merged = [...research, ...site].sort((a, b) => a.t - b.t);
  cues.push(...merged); t = Math.max(tr, ts);

  push(T.brief_after, { type: "brief", personas: d.personas as any, stress_tests: d.stress_tests });
  push(T.brief_after + 1200, { type: "stage", name: "run", timestamp: iso(t) });

  const personaById = Object.fromEntries(d.personas.map(p => [p.id, p]));
  const runCues: Cue[] = []; let tStart = t;
  d.runs.forEach((run, i) => {
    const p = personaById[run.persona_id]; const cfg = p.config as any;
    const t0 = tStart + i * T.swarm_start_gap;
    runCues.push({ t: t0, item: { type: "session_started", run_id: run.run_id, session_id: run.session_id, journey_id: p.journey_id, config: cfg,
      viewer_url: `https://app.steel.dev/sessions/${run.session_id}/debug?interactive=false`, replay_url: `https://app.steel.dev/sessions/${run.session_id}`,
      hls_url: `https://api.steel.dev/v1/sessions/${run.session_id}/replay.m3u8`, timestamp: iso(t0) } as SessionStarted });
    const events: RunEvent[] = run.steps.map(([action, path], k) => ({ type: "run_event", run_id: run.run_id, session_id: run.session_id, journey_id: p.journey_id, config: cfg,
      step_index: k + 1, timestamp: iso(t0 + (k + 1) * T.step_gap), action, observation: `https://northwindoutfitters.com${path}`, screenshot_ref: null, outcome: "step_ok" }));
    events.forEach((ev, k) => runCues.push({ t: t0 + i * T.run_stagger + (k + 1) * T.step_gap, item: ev }));
    const tEnd = t0 + i * T.run_stagger + (events.length + 1) * T.step_gap;
    runCues.push({ t: tEnd, item: { type: "run_result", run_id: run.run_id, journey_id: p.journey_id, config: cfg, session_id: run.session_id, outcome: run.outcome as any,
      attempt: 1, events, replay_url: `https://app.steel.dev/sessions/${run.session_id}`, hls_url: null, final_screenshot_ref: null,
      failure_step_index: run.failure_step_index, replay_offset_s: run.failure_step_index ? run.failure_step_index * 10 + 1 : null,
      harness_reason: run.outcome === "harness_error" ? "session ended before the first step" : null, stall_hint: null } as RunResult });
  });
  runCues.sort((a, b) => a.t - b.t); cues.push(...runCues); t = runCues[runCues.length - 1].t;

  push(T.score_after, { type: "stage", name: "score", timestamp: iso(t) });
  push(T.score_after, { type: "result", scorecard: d.scorecard as any, findings: d.findings as any, affected: d.affected as any });
  push(T.done_after, { type: "stage", name: "done", timestamp: iso(t) });
  return cues;
}
```

Run: `npx vitest run` → `4 passed`. Commit: `git commit -am "feat(web): choreography script from fixture"`.

---

## Task 5: Reducer (pure) and Player (the only timers)

**Files:**
- Create: `web/src/state/reducer.ts`, `web/src/state/player.ts`, `web/src/state/usePlayer.ts`
- Test: `web/test/reducer.test.ts`, `web/test/player.test.ts`

- [ ] **Step 1: Reducer tests**

```ts
// web/test/reducer.test.ts
import { initialState, reduce } from "../src/state/reducer";
import { buildScript } from "../src/data/script";
import demo from "../src/data/iris_demo.json";

it("folds the whole script into a finished state", () => {
  const s = buildScript(demo as any).reduce((st, c) => reduce(st, c.item), initialState(demo as any));
  expect(s.stage).toBe("done");
  expect(Object.keys(s.read)).toHaveLength(9);
  expect(s.nodes).toHaveLength(7);
  expect(s.personas).toHaveLength(8);
  expect(Object.keys(s.feeds)).toHaveLength(8);
  expect(s.feeds["r4"].status).toBe("stalled"); expect(s.feeds["r8"].status).toBe("harness_error"); expect(s.feeds["r1"].status).toBe("completed");
  expect(s.feeds["r4"].last_action).toBe("overlay keeps intercepting clicks");
  expect(s.scorecard?.overall).toBe(58); expect(s.findings).toHaveLength(4);
});
it("reticle focus follows the latest event, and a retry replaces the feed", () => {
  let s = initialState(demo as any);
  const cfg = demo.personas[0].config as any;
  s = reduce(s, { type: "session_started", run_id: "r1", session_id: "a", journey_id: "j", config: cfg, viewer_url: "v", replay_url: "r", hls_url: "h", timestamp: "" });
  expect(s.focus).toBe("r1");
  s = reduce(s, { type: "session_started", run_id: "r1", session_id: "b", journey_id: "j", config: cfg, viewer_url: "v2", replay_url: "r", hls_url: "h", timestamp: "" });
  expect(Object.keys(s.feeds)).toEqual(["r1"]); expect(s.feeds["r1"].session_id).toBe("b");
});
```

- [ ] **Step 2: Reducer**

```ts
// web/src/state/reducer.ts
import type { Feed, RunState, StreamItem } from "../types";

export function initialState(demo: { url: string; sources: any[] }): RunState {
  return { stage: "idle", url: demo.url, sources: demo.sources, read: {}, reading: null, site: null, nodes: [],
    personas: [], stress_tests: [], feeds: {}, focus: null, scorecard: null, findings: [], affected: {} };
}

export function reduce(s: RunState, m: StreamItem): RunState {
  switch (m.type) {
    case "stage": return { ...s, stage: m.name, reading: m.name === "explore" ? s.reading : null, focus: m.name === "run" ? s.focus : null };
    case "source_read": return { ...s, reading: m.source_id, read: { ...s.read, [m.source_id]: m.quotes } };
    case "site_model": return { ...s, site: m.site_model, nodes: m.nodes };
    case "brief": return { ...s, personas: m.personas, stress_tests: m.stress_tests };
    case "session_started": {
      const persona = s.personas.find(p => p.run_id === m.run_id);
      const feed: Feed = { run_id: m.run_id, session_id: m.session_id, persona_id: persona?.id ?? "", config: m.config, journey_id: m.journey_id,
        viewer_url: m.viewer_url, last_action: "starting", last_observation: "", step: 0, status: "running", final_screenshot_ref: null };
      return { ...s, feeds: { ...s.feeds, [m.run_id]: feed }, focus: m.run_id };
    }
    case "run_event": {
      const f = s.feeds[m.run_id]; if (!f) return s;
      return { ...s, focus: m.run_id, feeds: { ...s.feeds, [m.run_id]: { ...f, last_action: m.action, last_observation: m.observation, step: m.step_index } } };
    }
    case "run_result": {
      const f = s.feeds[m.run_id]; if (!f) return s;
      const last = m.events[m.events.length - 1];
      return { ...s, focus: m.run_id, feeds: { ...s.feeds, [m.run_id]: { ...f, status: m.outcome, final_screenshot_ref: m.final_screenshot_ref,
        last_action: m.outcome === "harness_error" ? (m.harness_reason ?? "tooling error") : (last?.action ?? f.last_action) } } };
    }
    case "result": return { ...s, scorecard: m.scorecard, findings: m.findings, affected: m.affected };
    default: return s;
  }
}

export const counts = (s: RunState) => {
  const fs = Object.values(s.feeds);
  return { running: fs.filter(f => f.status === "running").length, done: fs.filter(f => f.status === "completed").length,
    stalled: fs.filter(f => f.status === "stalled").length, error: fs.filter(f => f.status === "harness_error").length, total: fs.length };
};
```

- [ ] **Step 3: Player tests (fake timers)**

```ts
// web/test/player.test.ts
import { Player } from "../src/state/player";
it("dispatches cues on the clock, honours speed, and can seek to a stage", () => {
  vi.useFakeTimers();
  const seen: string[] = [];
  const cues = [{ t: 0, item: { type: "stage", name: "explore" } }, { t: 1000, item: { type: "stage", name: "run" } }, { t: 3000, item: { type: "stage", name: "done" } }] as any;
  const p = new Player(cues, it => seen.push((it as any).name), { speed: 2 });
  p.play();
  vi.advanceTimersByTime(499); expect(seen).toEqual(["explore"]);
  vi.advanceTimersByTime(2); expect(seen).toEqual(["explore", "run"]);
  vi.advanceTimersByTime(1000); expect(seen).toEqual(["explore", "run", "done"]);
  const seen2: string[] = []; const p2 = new Player(cues, it => seen2.push((it as any).name), { speed: 1 });
  p2.seekToStage("run"); expect(seen2).toEqual(["explore", "run"]);   // seek dispatches everything up to and including that stage, instantly
  vi.useRealTimers();
});
```

- [ ] **Step 4: Player and hook**

```ts
// web/src/state/player.ts
import type { StageName, StreamItem } from "../types";
import type { Cue } from "../data/script";

export class Player {
  private i = 0; private timer: ReturnType<typeof setTimeout> | null = null; private t0 = 0; private elapsed = 0;
  constructor(private cues: Cue[], private dispatch: (it: StreamItem) => void, private opts: { speed: number } = { speed: 1 }) {}
  get done() { return this.i >= this.cues.length; }
  play() { if (this.timer || this.done) return; this.t0 = performance.now() - this.elapsed / this.opts.speed; this.tick(); }
  pause() { if (this.timer) clearTimeout(this.timer); this.timer = null; this.elapsed = (performance.now() - this.t0) * this.opts.speed; }
  setSpeed(speed: number) { const playing = !!this.timer; this.pause(); this.opts.speed = speed; if (playing) this.play(); }
  seekToStage(name: StageName) { this.pause(); while (this.i < this.cues.length) { const c = this.cues[this.i++]; this.dispatch(c.item); if (c.item.type === "stage" && c.item.name === name) break; } this.elapsed = this.cues[this.i - 1]?.t ?? 0; }
  private tick = () => {
    this.timer = null;
    const now = (performance.now() - this.t0) * this.opts.speed;
    while (this.i < this.cues.length && this.cues[this.i].t <= now) this.dispatch(this.cues[this.i++].item);
    if (this.done) return;
    this.timer = setTimeout(this.tick, Math.max(0, (this.cues[this.i].t - now) / this.opts.speed));
  };
}
```

```ts
// web/src/state/usePlayer.ts
import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import demo from "../data/iris_demo.json";
import { buildScript } from "../data/script";
import { initialState, reduce } from "./reducer";
import { Player } from "./player";
import type { StageName } from "../types";

export function usePlayer() {
  const [state, dispatch] = useReducer(reduce, demo as any, initialState);
  const params = useMemo(() => new URLSearchParams(location.search), []);
  const speed = Number(params.get("speed") ?? 1);
  const [playing, setPlaying] = useState(false);
  const player = useRef<Player | null>(null);
  useEffect(() => { player.current = new Player(buildScript(demo as any), dispatch, { speed }); return () => player.current?.pause(); }, [speed]);
  useEffect(() => { const st = params.get("stage") as StageName | null; if (st) { player.current?.seekToStage(st); setPlaying(false); } }, [params]);
  return { state, playing, start: () => { player.current?.play(); setPlaying(true); }, pause: () => { player.current?.pause(); setPlaying(false); } };
}
```

Run: `npx vitest run` → `7 passed` (fake timers: in `player.ts` `performance.now` is patched by `vi.useFakeTimers` since Vitest 1; if the seek test's elapsed assertion flakes, assert only on dispatch order). Commit: `git commit -am "feat(web): reducer, player, usePlayer"`.

---

## Task 6: Textures — ASCII from image, Bayer dither

**Files:**
- Create: `web/src/texture/ascii.ts`, `web/src/texture/dither.ts`, `web/src/texture/AsciiImage.tsx`, `web/src/texture/DitherImage.tsx`, `web/src/texture/procedural.ts`
- Test: `web/test/ascii.test.ts`, `web/test/dither.test.ts`

Design-brief §6: ramp `" .:;i1tfLCG08@"`, 8×16px cells for ASCII; Bayer 4×4 to a 5-colour palette for dither. The pure functions take a luminance sampler so they are testable without canvas.

- [ ] **Step 1: Tests**

```ts
// web/test/ascii.test.ts
import { asciiFromLuma, RAMP } from "../src/texture/ascii";
it("maps luminance to the ramp, dark = dense", () => {
  const cols = 4, rows = 2;
  const luma = (x: number, y: number) => (y === 0 ? 0 : 1);   // top row black, bottom row white
  const out = asciiFromLuma(luma, cols, rows);
  expect(out).toHaveLength(2);
  expect(out[0]).toBe(RAMP[RAMP.length - 1].repeat(4));       // '@@@@'
  expect(out[1]).toBe(RAMP[0].repeat(4));                       // '    '
});
```

```ts
// web/test/dither.test.ts
import { bayerIndex, ditherPixel } from "../src/texture/dither";
it("bayer threshold and palette snap are deterministic", () => {
  expect(bayerIndex(0, 0)).toBe(0); expect(bayerIndex(1, 1)).toBe(10); expect(bayerIndex(3, 3)).toBe(5);
  const palette = ["#FAF7F2", "#141414"];
  expect(ditherPixel(0.95, 0, 0, palette)).toBe("#FAF7F2");
  expect(ditherPixel(0.05, 0, 0, palette)).toBe("#141414");
});
```

- [ ] **Step 2: Implement**

```ts
// web/src/texture/ascii.ts
export const RAMP = " .:;i1tfLCG08@";          // light → dark
export type Luma = (x: number, y: number) => number;   // 0 = black … 1 = white, sampled at cell centres
export function asciiFromLuma(luma: Luma, cols: number, rows: number): string[] {
  const lines: string[] = [];
  for (let y = 0; y < rows; y++) {
    let line = "";
    for (let x = 0; x < cols; x++) { const l = Math.min(1, Math.max(0, luma(x, y))); line += RAMP[Math.round((1 - l) * (RAMP.length - 1))]; }
    lines.push(line);
  }
  return lines;
}
export async function asciiFromImage(src: string, cols: number, rows: number): Promise<string[]> {
  const img = await load(src);
  const c = document.createElement("canvas"); c.width = cols; c.height = rows;
  const ctx = c.getContext("2d")!; ctx.drawImage(img, 0, 0, cols, rows);
  const { data } = ctx.getImageData(0, 0, cols, rows);
  return asciiFromLuma((x, y) => { const i = (y * cols + x) * 4; return (0.2126 * data[i] + 0.7152 * data[i + 1] + 0.0722 * data[i + 2]) / 255; }, cols, rows);
}
export const load = (src: string) => new Promise<HTMLImageElement>((res, rej) => { const im = new Image(); im.crossOrigin = "anonymous"; im.onload = () => res(im); im.onerror = rej; im.src = src; });
```

```ts
// web/src/texture/dither.ts
const BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]];
export const bayerIndex = (x: number, y: number) => BAYER4[y & 3][x & 3];
export function ditherPixel(luma: number, x: number, y: number, palette: string[]): string {
  const thresh = (bayerIndex(x, y) + 0.5) / 16;                     // 0..1
  const levels = palette.length - 1;
  const v = Math.min(levels, Math.floor(luma * levels + thresh));   // ordered dither across palette levels
  return palette[levels - v];                                        // palette[0] = lightest
}
export async function ditherImage(src: string, w: number, h: number, palette: string[]): Promise<HTMLCanvasElement> {
  const { load } = await import("./ascii");
  const img = await load(src);
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const ctx = c.getContext("2d")!; ctx.drawImage(img, 0, 0, w, h);
  const id = ctx.getImageData(0, 0, w, h); const out = ctx.createImageData(w, h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = (y * w + x) * 4; const l = (0.2126 * id.data[i] + 0.7152 * id.data[i + 1] + 0.0722 * id.data[i + 2]) / 255;
    const hex = ditherPixel(l, x, y, palette); out.data[i] = parseInt(hex.slice(1, 3), 16); out.data[i + 1] = parseInt(hex.slice(3, 5), 16); out.data[i + 2] = parseInt(hex.slice(5, 7), 16); out.data[i + 3] = 255;
  }
  ctx.putImageData(out, 0, 0); return c;
}
```

```ts
// web/src/texture/procedural.ts
// Seeded texture for cards with no source image (the exports use hand-made ramps; this makes them deterministic per id).
import { RAMP } from "./ascii";
export function proceduralAscii(seed: string, cols: number, rows: number): string[] {
  let h = 2166136261; for (const ch of seed) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619); }
  const rnd = () => { h ^= h << 13; h ^= h >>> 17; h ^= h << 5; return ((h >>> 0) % 1000) / 1000; };
  const cx = cols * (0.35 + rnd() * 0.3), cy = rows * (0.35 + rnd() * 0.3), r = Math.min(cols, rows) * (0.25 + rnd() * 0.2);
  const lines: string[] = [];
  for (let y = 0; y < rows; y++) { let line = ""; for (let x = 0; x < cols; x++) {
    const d = Math.hypot((x - cx) / 1.0, (y - cy) * 2) / r; const l = Math.min(1, Math.max(0, 1 - Math.exp(-d * 1.2) + rnd() * 0.08));
    line += RAMP[Math.round((1 - l) * (RAMP.length - 1))]; } lines.push(line); }
  return lines;
}
```

```tsx
// web/src/texture/AsciiImage.tsx
import { useEffect, useState } from "react";
import { asciiFromImage } from "./ascii";
import { proceduralAscii } from "./procedural";
const PASTEL = { 1: "var(--pastel-1)", 2: "var(--pastel-2)", 3: "var(--pastel-3)", 4: "var(--pastel-4)" } as const;
export function AsciiImage({ src, seed, cols = 48, rows = 14, pastel = 2, fontSize = 9, className, style }:
  { src?: string | null; seed: string; cols?: number; rows?: number; pastel?: 1 | 2 | 3 | 4; fontSize?: number; className?: string; style?: React.CSSProperties }) {
  const [lines, setLines] = useState<string[]>(() => proceduralAscii(seed, cols, rows));
  useEffect(() => { let on = true; if (src) asciiFromImage(src, cols, rows).then(l => on && setLines(l)).catch(() => {}); return () => { on = false; }; }, [src, cols, rows]);
  return (
    <pre className={className} style={{ margin: 0, fontFamily: "var(--font-mono)", fontSize, lineHeight: 1.15, color: "rgba(20,20,20,0.55)", whiteSpace: "pre", overflow: "hidden",
      background: `linear-gradient(160deg, ${PASTEL[pastel]} 0%, #FAF7F2 100%)`, padding: "10px 12px", ...style }}>{lines.join("\n")}</pre>
  );
}
```

```tsx
// web/src/texture/DitherImage.tsx
import { useEffect, useRef } from "react";
import { ditherImage } from "./dither";
export function DitherImage({ src, width, height, palette = ["#FAF7F2", "#D9D4CC", "#8A8580", "#141414"], style }:
  { src: string; width: number; height: number; palette?: string[]; style?: React.CSSProperties }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => { let on = true; ditherImage(src, width, height, palette).then(c => { if (!on || !ref.current) return; const ctx = ref.current.getContext("2d")!; ctx.imageSmoothingEnabled = false; ctx.drawImage(c, 0, 0); }).catch(() => {}); return () => { on = false; }; }, [src, width, height]);
  return <canvas ref={ref} width={width} height={height} style={{ imageRendering: "pixelated", ...style }} />;
}
```

Run: `npx vitest run` → `9 passed`. Commit: `git commit -am "feat(web): ascii + dither textures, procedural fallback"`.

---

## Task 7: Motion primitives and typographic atoms

**Files:**
- Create: `web/src/primitives/{Reticle,ScanLine,NumberTick,TextScramble,PixelDissolve,Chip,Pill,Mono,Serif}.tsx`
- Test: `web/test/primitives.test.tsx`

Sizes and colours come from the exports: reticle corners are 4px squares with 1.5px orange borders on a 12px box for the logo; for panels use 14px corners with 2px borders (see `design/EXTRACTION.md`, SourceCard reticle). Scan-line: 2px, `var(--scan)`, `irisScan 2.4s linear infinite`.

- [ ] **Step 1: Tests (behaviour, not pixels)**

```tsx
// web/test/primitives.test.tsx
import { render, screen, act } from "@testing-library/react";
import { Chip } from "../src/primitives/Chip";
import { Pill } from "../src/primitives/Pill";
import { TextScramble } from "../src/primitives/TextScramble";
import { NumberTick } from "../src/primitives/NumberTick";
it("chip uppercases mono text and pill maps status to colour", () => {
  render(<Chip>mobile</Chip>); expect(screen.getByText("mobile")).toHaveStyle({ textTransform: "uppercase" });
  render(<Pill status="stalled">STALLED</Pill>); expect(screen.getByText("STALLED")).toHaveStyle({ color: "#D93025" });
});
it("text scramble settles on the final text", async () => {
  vi.useFakeTimers(); render(<TextScramble duration={0.2} speed={0.02}>Watch them try.</TextScramble>);
  await act(async () => { vi.advanceTimersByTime(600); });
  expect(screen.getByText("Watch them try.")).toBeInTheDocument(); vi.useRealTimers();
});
it("number tick renders the target value when reduced motion", () => {
  render(<NumberTick value={58} instant />); expect(screen.getByText("58")).toBeInTheDocument();
});
```

- [ ] **Step 2: Implement**

```tsx
// web/src/primitives/Mono.tsx
export const Mono = ({ children, size = 11, color = "var(--muted)", style, ...rest }: React.HTMLAttributes<HTMLSpanElement> & { size?: number; color?: string }) =>
  <span className="mono" style={{ fontSize: size, fontWeight: 500, color, ...style }} {...rest}>{children}</span>;
```
```tsx
// web/src/primitives/Serif.tsx
export const Serif = ({ children, size, style, as: Tag = "h1" }: { children: React.ReactNode; size?: number | string; style?: React.CSSProperties; as?: "h1" | "h2" | "span" }) =>
  <Tag className="serif" style={{ margin: 0, fontSize: size ?? "clamp(40px, 6vw, 76px)", textWrap: "balance", ...style }}>{children}</Tag>;
```
```tsx
// web/src/primitives/Chip.tsx
export const Chip = ({ children, active = false }: { children: React.ReactNode; active?: boolean }) =>
  <span className="mono" style={{ fontSize: 11, fontWeight: 500, padding: "3px 6px", border: `1px solid ${active ? "var(--scan)" : "var(--line)"}`, color: active ? "var(--scan)" : "var(--ink)", background: "#FFFFFF" }}>{children}</span>;
```
```tsx
// web/src/primitives/Pill.tsx
import type { FeedStatus } from "../types";
const C: Record<FeedStatus, { color: string; bg: string; border: string }> = {
  running: { color: "#FF5A1F", bg: "rgba(255,90,31,0.08)", border: "#FF5A1F" }, completed: { color: "#1F9D55", bg: "rgba(31,157,85,0.08)", border: "#1F9D55" },
  stalled: { color: "#D93025", bg: "rgba(217,48,37,0.08)", border: "#D93025" }, harness_error: { color: "#8A8580", bg: "rgba(138,133,128,0.10)", border: "rgba(20,20,20,0.18)" } };
export const Pill = ({ status, children }: { status: FeedStatus; children: React.ReactNode }) =>
  <span className="mono" style={{ fontSize: 10, fontWeight: 500, padding: "3px 7px", color: C[status].color, background: C[status].bg, border: `1px solid ${C[status].border}`, display: "inline-flex", alignItems: "center", gap: 5, whiteSpace: "nowrap" }}>
    {status === "running" && <span style={{ width: 5, height: 5, borderRadius: "50%", background: "#FF5A1F", animation: "irisPulse 1.4s ease-in-out infinite" }} />}{children}</span>;
```
```tsx
// web/src/primitives/Reticle.tsx
import { motion } from "motion/react";
/** Four corner brackets. Give every Reticle in a group the same layoutId and render it only on the focused target: motion animates it between positions. */
export const Reticle = ({ size = 14, thickness = 2, inset = -6, layoutId = "reticle", color = "var(--scan)" }: { size?: number; thickness?: number; inset?: number; layoutId?: string; color?: string }) => {
  const c = (pos: React.CSSProperties) => <span style={{ position: "absolute", width: size, height: size, ...pos }} />;
  const b = `${thickness}px solid ${color}`;
  return (
    <motion.span layoutId={layoutId} transition={{ type: "spring", stiffness: 500, damping: 40, mass: 0.6 }} style={{ position: "absolute", inset, pointerEvents: "none", zIndex: 3 }} aria-hidden>
      {c({ top: 0, left: 0, borderTop: b, borderLeft: b })}{c({ top: 0, right: 0, borderTop: b, borderRight: b })}
      {c({ bottom: 0, left: 0, borderBottom: b, borderLeft: b })}{c({ bottom: 0, right: 0, borderBottom: b, borderRight: b })}
    </motion.span>);
};
export const LogoReticle = () => <span style={{ position: "relative", width: 12, height: 12, display: "block" }}><Reticle size={4} thickness={1.5} inset={0} layoutId="logo" /></span>;
```
```tsx
// web/src/primitives/ScanLine.tsx
export const ScanLine = ({ duration = 2.4 }: { duration?: number }) =>
  <span aria-hidden style={{ position: "absolute", left: 0, right: 0, top: "2%", height: 2, background: "var(--scan)", opacity: 0.9, boxShadow: "0 0 8px rgba(255,90,31,0.6)", animation: `irisScan ${duration}s linear infinite`, pointerEvents: "none" }} />;
```
```tsx
// web/src/primitives/NumberTick.tsx
import { animate } from "motion";
import { useEffect, useState } from "react";
export function NumberTick({ value, duration = 1.2, instant = false, format = (n: number) => String(Math.round(n)) }: { value: number; duration?: number; instant?: boolean; format?: (n: number) => string }) {
  const [n, setN] = useState(instant ? value : 0);
  useEffect(() => { if (instant) { setN(value); return; } const ctrl = animate(n, value, { duration, ease: "easeOut", onUpdate: setN }); return () => ctrl.stop(); }, [value, instant]);
  return <>{format(n)}</>;
}
```
```tsx
// web/src/primitives/TextScramble.tsx
import { useEffect, useState } from "react";
const CHARS = "!<>-_\\/[]{}—=+*^?#________";
export function TextScramble({ children, duration = 0.8, speed = 0.04, as: Tag = "span", className, style, trigger = true }:
  { children: string; duration?: number; speed?: number; as?: any; className?: string; style?: React.CSSProperties; trigger?: boolean }) {
  const [text, setText] = useState(trigger ? "" : children);
  useEffect(() => {
    if (!trigger) { setText(children); return; }
    const steps = Math.max(1, Math.floor(duration / speed)); let step = 0;
    const id = setInterval(() => {
      step++; const p = step / steps;
      setText(children.split("").map((ch, i) => ch === " " ? " " : i / children.length < p ? ch : CHARS[Math.floor(Math.random() * CHARS.length)]).join(""));
      if (step >= steps) { clearInterval(id); setText(children); }
    }, speed * 1000);
    return () => clearInterval(id);
  }, [children, trigger]);
  return <Tag className={className} style={style}>{text}</Tag>;
}
```
```tsx
// web/src/primitives/PixelDissolve.tsx
import { useMemo } from "react";
/** Overlay of 16px blocks in `color` that fade out with random delays over `duration`s, revealing children. Re-keys when `trigger` changes. */
export function PixelDissolve({ children, trigger, color = "#FAF7F2", block = 16, duration = 0.6, style }:
  { children: React.ReactNode; trigger: string | number; color?: string; block?: number; duration?: number; style?: React.CSSProperties }) {
  const cells = useMemo(() => Array.from({ length: 12 * 8 }, (_, i) => ({ i, d: Math.random() * duration })), [trigger, duration]);
  return (
    <span style={{ position: "relative", display: "block", ...style }}>
      {children}
      <span key={String(trigger)} aria-hidden style={{ position: "absolute", inset: 0, display: "grid", gridTemplateColumns: "repeat(12, 1fr)", gridTemplateRows: "repeat(8, 1fr)", pointerEvents: "none" }}>
        {cells.map(c => <span key={c.i} style={{ background: color, opacity: 1, animation: `irisBlink 0s linear ${c.d}s forwards`, animationName: "irisFade" }} />)}
      </span>
    </span>);
}
```
Add to `tokens.css`: `@keyframes irisFade { to { opacity: 0; } }` and change the cell style to `animation: \`irisFade 0.12s linear ${c.d}s forwards\``.

Run: `npx vitest run` → `12 passed`. Commit: `git commit -am "feat(web): reticle, scan-line, number tick, text scramble, pixel dissolve, atoms"`.

---

## Task 8: TopBar (port of `Iris Top Bar.dc.html`)

**Files:**
- Create: `web/src/components/TopBar.tsx`
- Modify: `web/src/App.tsx`
- Test: `web/test/topbar.test.tsx`

The export's structure is a sticky 64px grid `auto 1fr auto`, padding `0 28px`, `backdrop-filter: blur(2px)`, bottom border `rgba(20,20,20,0.1)`. Stage states: done = ink + green ✓; current = `#FF5A1F` on `rgba(255,90,31,0.08)` with a pulsing 5px dot; upcoming = `#8A8580`. Labels `LEARN · BRIEF · SWARM · FINDINGS · REPORT` in Geist Mono 11px / 500 / 0.1em; separators `·` at `rgba(20,20,20,0.22)`. Counter `[ n SESSIONS ]` 12px / 0.12em with a `1px solid rgba(20,20,20,0.18)` border, `6px 10px`. `[ CACHED ]` pill: muted text on `rgba(20,20,20,0.06)`, radius 999.

- [ ] **Step 1: Test**

```tsx
// web/test/topbar.test.tsx
import { render, screen } from "@testing-library/react";
import { TopBar } from "../src/components/TopBar";
it("marks stages and pluralises sessions", () => {
  render(<TopBar stage="run" sessions={8} cached />);
  expect(screen.getByText("SWARM")).toBeInTheDocument();
  expect(screen.getByText("[ 8 SESSIONS ]")).toBeInTheDocument();
  expect(screen.getByText("[ CACHED ]")).toBeInTheDocument();
  render(<TopBar stage="idle" sessions={1} />); expect(screen.getByText("[ 1 SESSION ]")).toBeInTheDocument();
});
```

- [ ] **Step 2: Implement**

```tsx
// web/src/components/TopBar.tsx
import { LogoReticle } from "../primitives/Reticle";
import type { StageName } from "../types";
const STEPS: { key: StageName | "brief"; label: string }[] = [{ key: "explore", label: "LEARN" }, { key: "brief", label: "BRIEF" }, { key: "run", label: "SWARM" }, { key: "score", label: "FINDINGS" }, { key: "done", label: "REPORT" }];
const ORDER = ["explore", "brief", "run", "score", "done"];
/** `brief` is a UI-only stage between explore and run: it is "current" once personas exist and the run stage has not started. */
export function TopBar({ stage, sessions, cached = false, hasBrief = false }: { stage: StageName | "idle"; sessions: number; cached?: boolean; hasBrief?: boolean }) {
  const current = stage === "explore" && hasBrief ? "brief" : stage;
  const idx = ORDER.indexOf(current as string);
  return (
    <div style={{ position: "sticky", top: 0, zIndex: 5, backdropFilter: "blur(2px)", borderBottom: "1px solid rgba(20,20,20,0.1)", background: "rgba(250,247,242,0.7)" }}>
      <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", alignItems: "center", gap: 20, padding: "0 28px", minHeight: 64 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}><LogoReticle /><span className="serif" style={{ fontSize: 30, lineHeight: 1 }}>Iris</span></div>
        <div className="mono" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 2, fontSize: 11, fontWeight: 500 }}>
          {STEPS.map((s, i) => {
            const state = idx < 0 ? "up" : i < idx ? "done" : i === idx ? "cur" : "up";
            return (<span key={s.key} style={{ display: "contents" }}>
              {i > 0 && <span style={{ color: "rgba(20,20,20,0.22)" }}>·</span>}
              <span style={{ display: "flex", alignItems: "center", gap: 6, padding: state === "cur" ? "6px 9px" : "6px 6px", whiteSpace: "nowrap",
                color: state === "done" ? "#141414" : state === "cur" ? "#FF5A1F" : "#8A8580", background: state === "cur" ? "rgba(255,90,31,0.08)" : "transparent" }}>
                {state === "done" && <span style={{ color: "#1F9D55" }}>✓</span>}
                {state === "cur" && <span style={{ width: 5, height: 5, background: "#FF5A1F", borderRadius: "50%", display: "block", animation: "irisPulse 1.4s ease-in-out infinite" }} />}
                {s.label}</span></span>);
          })}
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 10 }}>
          {cached && <span className="mono" style={{ fontSize: 12, fontWeight: 500, letterSpacing: "0.12em", color: "#8A8580", background: "rgba(20,20,20,0.06)", padding: "6px 10px", borderRadius: 999, whiteSpace: "nowrap" }}>[ CACHED ]</span>}
          <span className="mono" style={{ fontSize: 12, fontWeight: 500, letterSpacing: "0.12em", color: "#141414", border: "1px solid rgba(20,20,20,0.18)", padding: "6px 10px", whiteSpace: "nowrap" }}>{`[ ${sessions} SESSION${sessions === 1 ? "" : "S"} ]`}</span>
        </div>
      </div>
    </div>);
}
```

- [ ] **Step 3: App shell (stages render as state arrives; screens are added in Tasks 9–13)**

```tsx
// web/src/App.tsx
import { TopBar } from "./components/TopBar";
import { usePlayer } from "./state/usePlayer";
import { counts } from "./state/reducer";
export default function App() {
  const { state, start, playing } = usePlayer();
  const cached = new URLSearchParams(location.search).get("demo") === "cached";
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <TopBar stage={state.stage} sessions={counts(state).total} cached={cached} hasBrief={state.personas.length > 0} />
      <main style={{ flex: 1 }}>
        {/* Task 9: <Input onRun={start} .../>  Task 10: <Learning/>  Task 11: <Brief/>  Task 12: <Swarm/>  Task 13: <Report/> */}
        {!playing && <button onClick={start}>start</button>}
      </main>
    </div>);
}
```

Run: `npx vitest run` → `13 passed`; `npm run dev` and confirm the bar matches `design/frames/Iris Top Bar.dc.html` side by side (serve that folder on :8787 as in `design/README.md`). Commit: `git commit -am "feat(web): TopBar + app shell"`.


---

## Task 9: Screen 1 — Input (port of `Iris 01 Input.dc.html`)

**Files:**
- Create: `web/src/screens/Input.tsx`
- Modify: `web/src/App.tsx`
- Test: `web/test/input.test.tsx`

Exact values in `design/EXTRACTION.md` §1.

- [ ] **Step 1: Test**

```tsx
// web/test/input.test.tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { Input } from "../src/screens/Input";
it("submits the url and calls onRun once", () => {
  const onRun = vi.fn();
  render(<Input onRun={onRun} />);
  fireEvent.change(screen.getByPlaceholderText("https://northwindoutfitters.com"), { target: { value: "https://x.test" } });
  fireEvent.click(screen.getByText("RUN IRIS →"));
  expect(onRun).toHaveBeenCalledWith("https://x.test");
  expect(screen.getByText("Send your customers in first.")).toBeInTheDocument();
});
```

- [ ] **Step 2: Implement**

```tsx
// web/src/screens/Input.tsx
import { useState } from "react";
import { motion } from "motion/react";
import { Serif } from "../primitives/Serif";
export function Input({ onRun, collapsed = false }: { onRun: (url: string) => void; collapsed?: boolean }) {
  const [url, setUrl] = useState("");
  return (
    <motion.section layout initial={false} animate={{ minHeight: collapsed ? 0 : "calc(100vh - 64px)", paddingTop: collapsed ? 24 : 32, paddingBottom: collapsed ? 24 : 48 }}
      transition={{ duration: 0.6, ease: "easeInOut" }}
      style={{ position: "relative", display: "flex", alignItems: "center", justifyContent: "center", padding: "32px 32px 48px", overflow: "hidden" }}>
      <div style={{ position: "relative", zIndex: 2, width: "100%", maxWidth: 660, display: "flex", flexDirection: "column", alignItems: "center", gap: collapsed ? 16 : 34 }}>
        {!collapsed && <img src="/assets/computer-globe-monitor.png" alt="" style={{ position: "absolute", left: "50%", bottom: "calc(100% + 14px)", transform: "translateX(-50%)", height: "min(150px, 26vh)", width: "auto", maxWidth: "100%", opacity: 0.2, imageRendering: "pixelated", pointerEvents: "none", userSelect: "none" }} />}
        <Serif size={collapsed ? 28 : "clamp(40px, 6vw, 76px)"} style={{ position: "relative", zIndex: 1, textAlign: "center", lineHeight: 0.96 }}>Send your customers in first.</Serif>
        <form style={{ position: "relative", zIndex: 1, width: "100%", maxWidth: 580, display: "flex", flexWrap: "wrap", gap: 10 }} onSubmit={e => { e.preventDefault(); onRun(url || "https://northwindoutfitters.com"); }}>
          <input value={url} onChange={e => setUrl(e.target.value)} placeholder="https://northwindoutfitters.com" disabled={collapsed}
            style={{ flex: "1 1 300px", minWidth: 0, boxSizing: "border-box", fontFamily: "var(--font-mono)", fontSize: 16, color: "#141414", background: "#FFFFFF", border: "1px solid rgba(20,20,20,0.22)", padding: "15px 18px", outline: "none" }}
            onFocus={e => { e.currentTarget.style.borderColor = "#FF5A1F"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(255,90,31,0.12)"; }}
            onBlur={e => { e.currentTarget.style.borderColor = "rgba(20,20,20,0.22)"; e.currentTarget.style.boxShadow = "none"; }} />
          <button type="submit" disabled={collapsed} style={{ flex: "0 0 auto", fontFamily: "var(--font-mono)", fontSize: 13, fontWeight: 500, letterSpacing: "0.14em", color: "#FFFFFF", background: collapsed ? "#8A8580" : "#FF5A1F", border: "none", padding: "15px 28px", cursor: collapsed ? "default" : "pointer", whiteSpace: "nowrap" }}>RUN IRIS →</button>
        </form>
      </div>
    </motion.section>);
}
```

In `App.tsx` render `<Input onRun={url => start()} collapsed={state.stage !== "idle"} />` as the first child of `<main>` and remove the temporary start button. After the run starts the hero collapses to a compact header so the page can grow beneath it.

Run: `npx vitest run` → `14 passed`. Commit: `git commit -am "feat(web): Input screen"`.

---

## Task 10: Screen 2 — Learning (port of `Iris 02 Learning*.dc.html`)

**Files:**
- Create: `web/src/screens/Learning.tsx`, `web/src/screens/learning/SourceCard.tsx`, `web/src/screens/learning/SiteMap.tsx`, `web/src/screens/learning/layout.ts`
- Test: `web/test/learning.test.tsx`, `web/test/sitemap-layout.test.ts`

Exact values in `design/EXTRACTION.md` §2. The A→B diff is exactly what the reducer already produces (`reading` moves, `read` grows, `nodes` grows), so this screen is a pure render.

- [ ] **Step 1: Tests**

```ts
// web/test/sitemap-layout.test.ts
import { layoutNodes } from "../src/screens/learning/layout";
it("places nodes left-to-right by depth with journeys on the right edge and no two nodes at the same point", () => {
  const nodes = [{ path: "/", parent: null, journey: null }, { path: "/a", parent: "/", journey: 1 }, { path: "/a/b", parent: "/a", journey: null }, { path: "/c", parent: "/", journey: null }, { path: "/a/b/d", parent: "/a/b", journey: 2 }];
  const pos = layoutNodes(nodes);
  expect(pos["/"].x).toBe(10);
  expect(pos["/a"].x).toBeGreaterThan(pos["/"].x); expect(pos["/a/b/d"].x).toBeGreaterThan(pos["/a/b"].x);
  const pts = new Set(Object.values(pos).map(p => `${p.x},${p.y}`)); expect(pts.size).toBe(5);
});
```

```tsx
// web/test/learning.test.tsx
import { render, screen } from "@testing-library/react";
import { Learning } from "../src/screens/Learning";
import { initialState, reduce } from "../src/state/reducer";
import demo from "../src/data/iris_demo.json";
it("shows read quotes, the focused source, and counts", () => {
  let s = initialState(demo as any);
  s = reduce(s, { type: "stage", name: "explore", timestamp: "" });
  s = reduce(s, { type: "source_read", source_id: "trustpilot", quotes: demo.reads[0].quotes as any, timestamp: "" });
  s = reduce(s, { type: "site_model", site_model: demo.site_model as any, nodes: demo.nodes.slice(0, 3) as any });
  render(<Learning state={s} />);
  expect(screen.getByText("checkout resets on my phone every time")).toBeInTheDocument();
  expect(screen.getByText("2 PIECES OF EVIDENCE · 1 SOURCE")).toBeInTheDocument();
  expect(screen.getByText("3 PAGES · 1 JOURNEY")).toBeInTheDocument();
  expect(screen.getByText("TRUSTPILOT")).toHaveStyle({ color: "#FF5A1F" });
});
```

- [ ] **Step 2: Layout helper**

```ts
// web/src/screens/learning/layout.ts
import type { SiteNode } from "../../types";
export type Pos = { x: number; y: number };   // percent of the graph box
/** Depth-column layout: root at x=10, deeper columns spread to x=90; siblings spread vertically 12..88. */
export function layoutNodes(nodes: SiteNode[]): Record<string, Pos> {
  const depth: Record<string, number> = {};
  const d = (p: string): number => { if (depth[p] != null) return depth[p]; const n = nodes.find(x => x.path === p); depth[p] = n?.parent ? d(n.parent) + 1 : 0; return depth[p]; };
  nodes.forEach(n => d(n.path));
  const maxD = Math.max(0, ...Object.values(depth));
  const cols: Record<number, string[]> = {};
  nodes.forEach(n => (cols[depth[n.path]] ??= []).push(n.path));
  const pos: Record<string, Pos> = {};
  Object.entries(cols).forEach(([k, paths]) => {
    const x = maxD === 0 ? 10 : 10 + (80 * Number(k)) / maxD;
    paths.forEach((p, i) => { pos[p] = { x, y: paths.length === 1 ? 50 : 12 + (76 * i) / (paths.length - 1) }; });
  });
  return pos;
}
export const edgePath = (a: Pos, b: Pos) => `M ${a.x} ${a.y} C ${a.x + (b.x - a.x) * 0.45} ${a.y}, ${a.x + (b.x - a.x) * 0.55} ${b.y}, ${b.x} ${b.y}`;
```

- [ ] **Step 3: Components**

```tsx
// web/src/screens/learning/SourceCard.tsx
import { motion } from "motion/react";
import { AsciiImage } from "../../texture/AsciiImage";
import { Reticle } from "../../primitives/Reticle";
import type { Quote, Source } from "../../types";
const GRAD: Record<number, string> = { 1: "linear-gradient(140deg, #FFD9CF, #F3E9D2)", 2: "linear-gradient(140deg, #E5DDF5, #D8ECE3)", 3: "linear-gradient(140deg, #D8ECE3, #FFD9CF)", 4: "linear-gradient(140deg, #F3E9D2, #E5DDF5)" };
export function SourceCard({ source, quotes, focused, index }: { source: Source; quotes: Quote[] | undefined; focused: boolean; index: number }) {
  return (
    <motion.div layout initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.15, duration: 0.35 }} style={{ position: "relative", display: "flex", flexDirection: "column", gap: 7, minWidth: 0 }}>
      <div style={{ position: "relative", aspectRatio: "4 / 3", background: GRAD[((index % 4) + 1)], border: "1px solid rgba(20,20,20,0.12)", overflow: "hidden" }}>
        <AsciiImage src={source.thumbnail} seed={source.id} cols={28} rows={8} fontSize={7} style={{ background: "transparent", padding: 5, color: quotes ? "rgba(20,20,20,0.45)" : "rgba(20,20,20,0.4)", lineHeight: "7px" }} />
        {focused && <Reticle layoutId="research-reticle" size={11} thickness={2} inset={5} />}
      </div>
      <span className="mono" style={{ fontSize: 10, letterSpacing: "0.08em", lineHeight: 1.4, color: focused ? "#FF5A1F" : "#141414", textTransform: "uppercase" }}>{source.name}</span>
      {quotes?.slice(0, 1).map(q => (
        <motion.div key={q.text} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} style={{ display: "flex", gap: 6, background: "rgba(255,90,31,0.1)", padding: "6px 7px" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "#FF5A1F", flexShrink: 0 }}>&gt;</span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, lineHeight: 1.45, color: "#141414" }}>{q.text}</span>
        </motion.div>))}
    </motion.div>);
}
```

```tsx
// web/src/screens/learning/SiteMap.tsx
import { motion } from "motion/react";
import { AsciiImage } from "../../texture/AsciiImage";
import type { SiteNode } from "../../types";
import { edgePath, layoutNodes } from "./layout";
export function SiteMap({ url, nodes, scanning }: { url: string; nodes: SiteNode[]; scanning: boolean }) {
  const pos = layoutNodes(nodes);
  const host = url.replace(/^https?:\/\//, "").replace(/\/$/, "");
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16, alignItems: "stretch" }}>
      <div style={{ border: "1px solid rgba(20,20,20,0.14)", background: "#FAF7F2", display: "flex", flexDirection: "column", minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 10px", borderBottom: "1px solid rgba(20,20,20,0.12)" }}>
          <span style={{ display: "flex", gap: 4 }}>{[0, 1, 2].map(i => <span key={i} style={{ width: 6, height: 6, background: "rgba(20,20,20,0.22)", display: "block" }} />)}</span>
          <span className="mono" style={{ fontSize: 9, letterSpacing: "0.06em", color: "#8A8580", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", textTransform: "none" }}>{host}</span>
        </div>
        <div style={{ position: "relative", flex: 1, minHeight: 210, background: "linear-gradient(160deg, #F3E9D2, #FFD9CF)", overflow: "hidden" }}>
          <AsciiImage seed={host} cols={110} rows={30} fontSize={7} style={{ background: "transparent", padding: 8, lineHeight: "8.6px", letterSpacing: "0.02em", color: "rgba(20,20,20,0.42)" }} />
          <span aria-hidden style={{ position: "absolute", left: 0, right: 0, height: 2, background: "#FF5A1F", boxShadow: "0 0 10px rgba(255,90,31,0.55)", top: scanning ? undefined : "74%", animation: scanning ? "irisScanPanel 2.8s linear infinite" : "none" }} />
        </div>
      </div>
      <div style={{ position: "relative", minHeight: 250, minWidth: 0, padding: 8, boxSizing: "border-box", border: "1px solid rgba(20,20,20,0.1)" }}>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
          {nodes.filter(n => n.parent && pos[n.parent]).map(n => (
            <motion.path key={n.path} d={edgePath(pos[n.parent!], pos[n.path])} fill="none" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.3 }}
              stroke={n.journey ? "#FF5A1F" : "#141414"} strokeWidth={n.journey ? 0.45 : 0.35} opacity={n.journey ? 0.9 : 0.5} vectorEffect="non-scaling-stroke" />))}
        </svg>
        {nodes.map(n => (
          <motion.span key={n.path} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.2 }}
            style={{ position: "absolute", left: `${pos[n.path].x}%`, top: `${pos[n.path].y}%`, transform: "translate(-50%, -50%)", display: "flex", alignItems: "center", gap: 7, fontFamily: "var(--font-mono)", fontSize: 10,
              color: n.journey ? "#FF5A1F" : "#141414", background: "#FAF7F2", border: `1px solid ${n.journey ? "#FF5A1F" : "rgba(20,20,20,0.2)"}`, padding: "4px 7px", whiteSpace: "nowrap" }}>
            {n.path}{n.journey && <span style={{ fontSize: 8, letterSpacing: "0.1em", color: "#FF5A1F", opacity: 0.85 }}>JOURNEY {n.journey}</span>}
          </motion.span>))}
      </div>
    </div>);
}
```

Add to `tokens.css`: `@keyframes irisScanPanel { 0% { top: 4%; } 100% { top: 94%; } }`.

```tsx
// web/src/screens/Learning.tsx
import { Serif } from "../primitives/Serif";
import { TextScramble } from "../primitives/TextScramble";
import type { RunState } from "../types";
import { SourceCard } from "./learning/SourceCard";
import { SiteMap } from "./learning/SiteMap";
const label: React.CSSProperties = { fontFamily: "var(--font-mono)", fontSize: 11, fontWeight: 500, letterSpacing: "0.18em", color: "#8A8580" };
const count: React.CSSProperties = { fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.14em", color: "#8A8580" };
const plural = (n: number, w: string) => `${n} ${w}${n === 1 ? "" : "S"}`;
export function Learning({ state }: { state: RunState }) {
  const evidence = Object.values(state.read).reduce((a, q) => a + q.length, 0);
  const sources = Object.values(state.read).filter(q => q.length > 0).length;
  const journeys = state.nodes.filter(n => n.journey).length;
  const scanning = state.stage === "explore";
  return (
    <section style={{ display: "flex", flexDirection: "column", gap: 40, padding: "44px 32px 64px", maxWidth: 1400, width: "100%", boxSizing: "border-box", margin: "0 auto" }}>
      <Serif size="clamp(38px, 4.6vw, 68px)" style={{ maxWidth: 900, lineHeight: 0.98 }}><TextScramble duration={0.9}>Learning your customers and your site.</TextScramble></Serif>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: 48, alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 16, minWidth: 0 }}>
          <span style={label}>[ RESEARCH ]</span>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 14 }}>
            {state.sources.map((s, i) => <SourceCard key={s.id} source={s} quotes={state.read[s.id]} focused={state.reading === s.id} index={i} />)}
          </div>
          <span style={count}>{`${evidence} PIECES OF EVIDENCE · ${plural(sources, "SOURCE")}`}</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 16, minWidth: 0 }}>
          <span style={label}>[ SITE MAP ]</span>
          <SiteMap url={state.url} nodes={state.nodes} scanning={scanning} />
          <span style={count}>{`${plural(state.nodes.length, "PAGE")} · ${plural(journeys, "JOURNEY")}`}</span>
        </div>
      </div>
    </section>);
}
```

Note the test expects `2 PIECES OF EVIDENCE` with a pluralised noun; `PIECES` is always plural in the label. Adjust the test string if the singular form is wanted later.

- [ ] **Step 4: Mount and verify**

In `App.tsx`: `{state.stage !== "idle" && <Learning state={state} />}`. Run: `npx vitest run` → `16 passed`. Run `npm run dev`, press RUN IRIS, watch: cards appear one by one, the reticle hops, quote strips slide in, nodes draw. Compare with `Iris 02 Learning.dc.html` and `Learning B` served on :8787.

Commit: `git commit -am "feat(web): Learning screen (source wall, site map)"`.

---

## Task 11: Screen 3 — Brief (port of `Iris 03 Brief.dc.html`)

**Files:**
- Create: `web/src/screens/Brief.tsx`, `web/src/screens/brief/PersonaCard.tsx`, `web/src/screens/brief/WorldDots.tsx`, `web/src/screens/brief/StressTable.tsx`
- Test: `web/test/brief.test.tsx`

Exact values in `design/EXTRACTION.md` §3. Blip positions are per country; multiple personas in one country get the additional offsets listed there.

- [ ] **Step 1: Test**

```tsx
// web/test/brief.test.tsx
import { render, screen } from "@testing-library/react";
import { Brief } from "../src/screens/Brief";
import demo from "../src/data/iris_demo.json";
it("renders eight personas, the matched pair label, and the stress table", () => {
  render(<Brief personas={demo.personas as any} stressTests={demo.stress_tests} />);
  expect(screen.getAllByText(/Coupon hunter, United States/)).toHaveLength(2);
  expect(screen.getByText("MATCHED PAIR · DEVICE")).toBeInTheDocument();
  expect(screen.getByText("checkout on mobile")).toBeInTheDocument();
  expect(screen.getAllByText("CA").length).toBeGreaterThanOrEqual(2);
});
```

- [ ] **Step 2: Components**

```tsx
// web/src/screens/brief/WorldDots.tsx
import { motion } from "motion/react";
import type { Persona } from "../../types";
const PIN: Record<string, { left: string; top: string; above?: boolean }[]> = {
  US: [{ left: "16%", top: "27.6%" }, { left: "22.9%", top: "33.1%" }, { left: "25.7%", top: "24.5%" }, { left: "29.4%", top: "25.4%" }],
  CA: [{ left: "15.8%", top: "19%", above: true }, { left: "27.9%", top: "23.2%", above: true }],
  GB: [{ left: "50%", top: "17.4%", above: true }], DE: [{ left: "53.7%", top: "16.7%" }],
};
export function WorldDots({ personas }: { personas: Persona[] }) {
  const used: Record<string, number> = {};
  const pins = personas.map(p => { const i = used[p.config.country] ?? 0; used[p.config.country] = i + 1; const slots = PIN[p.config.country] ?? PIN.US; return { id: p.id, country: p.config.country, ...slots[i % slots.length] }; });
  return (
    <div style={{ position: "relative", width: "fit-content", maxWidth: "100%", margin: "0 auto" }}>
      <img src="/assets/world-dots.png" alt="" style={{ display: "block", height: "33vh", width: "auto", maxWidth: "100%", opacity: 0.9 }} />
      {pins.map((p, i) => (
        <motion.span key={p.id} initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.3, duration: 0.3 }}
          style={{ position: "absolute", left: p.left, top: p.top, transform: "translate(-50%, -50%)", display: "flex", flexDirection: p.above ? "column-reverse" : "column", alignItems: "center", gap: 3 }}>
          <span style={{ width: 9, height: 9, background: "#FF5A1F", borderRadius: "50%", display: "block", animation: `irisBlip 2s ease-in-out ${i * 0.15}s infinite` }} />
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", color: "#FF5A1F" }}>{p.country}</span>
        </motion.span>))}
    </div>);
}
```

Add to `tokens.css`: `@keyframes irisBlip { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.35); opacity: 0.6; } }`.

```tsx
// web/src/screens/brief/PersonaCard.tsx
import { motion } from "motion/react";
import { AsciiImage } from "../../texture/AsciiImage";
import type { Persona } from "../../types";
const GRAD: Record<number, string> = { 1: "linear-gradient(150deg, #FFD9CF, #F3E9D2)", 2: "linear-gradient(150deg, #F3E9D2, #FFD9CF)", 3: "linear-gradient(150deg, #E5DDF5, #D8ECE3)", 4: "linear-gradient(150deg, #D8ECE3, #E5DDF5)" };
const chip = (accent: boolean): React.CSSProperties => ({ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", padding: "3px 6px", textTransform: "uppercase", color: accent ? "#FF5A1F" : "#141414", border: `1px solid ${accent ? "#FF5A1F" : "rgba(20,20,20,0.18)"}` });
export const chipsFor = (p: Persona) => [p.config.device, p.config.country, p.config.identity === "fresh" ? "new" : "returning"];
export function PersonaCard({ p, pairAxis, index }: { p: Persona; pairAxis: "device" | "identity" | "country" | null; index: number }) {
  const [device, country, identity] = chipsFor(p);
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.1, duration: 0.3 }}
      style={{ display: "flex", flexDirection: "column", gap: 10, border: `1px solid ${pairAxis ? "#FF5A1F" : "rgba(20,20,20,0.14)"}`, background: "#FAF7F2", padding: 12, minWidth: 0 }}>
      <div style={{ background: GRAD[p.pastel], border: "1px solid rgba(20,20,20,0.08)", overflow: "hidden" }}>
        <AsciiImage seed={p.segment + p.config.device} cols={24} rows={10} fontSize={8} style={{ background: "transparent", padding: 8, lineHeight: "8px", color: "rgba(20,20,20,0.5)" }} />
      </div>
      <span style={{ fontSize: 20, lineHeight: 1.2, letterSpacing: "-0.01em" }}>{p.segment}</span>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
        <span style={chip(pairAxis === "device")}>{device}</span><span style={chip(pairAxis === "country")}>{country}</span><span style={chip(pairAxis === "identity")}>{identity}</span>
      </div>
      <span style={{ fontSize: 13, lineHeight: 1.5, color: "#141414" }}>{p.goal}</span>
      <div style={{ background: "rgba(20,20,20,0.04)", padding: 8, display: "flex", flexDirection: "column", gap: 4 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, lineHeight: 1.5, color: "#141414" }}>"{p.evidence.text}"</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.06em", color: "#8A8580" }}>— {sourceName(p.evidence.source_id)}, {p.evidence.date}</span>
      </div>
    </motion.div>);
}
const NAMES: Record<string, string> = { trustpilot: "Trustpilot", google: "Google Reviews", reddit: "Reddit r/Outdoors", appstore: "App Store", help: "Help centre", competitor: "Arc'teryx", youtube: "YouTube", support: "Support tickets", instagram: "Instagram" };
export const sourceName = (id: string) => NAMES[id] ?? id;
```

```tsx
// web/src/screens/brief/StressTable.tsx
import type { StressTest } from "../../types";
const head = (extra: React.CSSProperties): React.CSSProperties => ({ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.14em", color: "#8A8580", padding: "10px 12px", borderBottom: "1px solid rgba(20,20,20,0.1)", ...extra });
const cell = (last: boolean, muted = false, extra: React.CSSProperties = {}): React.CSSProperties => ({ fontFamily: "var(--font-mono)", fontSize: 11, lineHeight: 1.5, color: muted ? "#8A8580" : "#141414", padding: "11px 12px", borderBottom: last ? "none" : "1px solid rgba(20,20,20,0.08)", ...extra });
export function StressTable({ rows }: { rows: StressTest[] }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, fontWeight: 500, letterSpacing: "0.18em", color: "#8A8580" }}>STRESS TESTS</span>
      <div style={{ display: "grid", gridTemplateColumns: "minmax(120px, 1fr) minmax(140px, 1.4fr) minmax(90px, 0.8fr)", borderTop: "1px solid rgba(20,20,20,0.16)" }}>
        <span style={head({ paddingLeft: 0 })}>PROBE</span><span style={head({})}>WHY</span><span style={head({ paddingRight: 0 })}>SOURCE</span>
        {rows.map((r, i) => { const last = i === rows.length - 1; return (<span key={r.probe} style={{ display: "contents" }}>
          <span style={cell(last, false, { paddingLeft: 0 })}>{r.probe}</span><span style={cell(last)}>{r.why}</span><span style={cell(last, true, { paddingRight: 0 })}>{r.source}</span></span>); })}
      </div>
    </div>);
}
```

```tsx
// web/src/screens/Brief.tsx
import { Serif } from "../primitives/Serif";
import { TextScramble } from "../primitives/TextScramble";
import type { Persona, StressTest } from "../types";
import { PersonaCard } from "./brief/PersonaCard";
import { StressTable } from "./brief/StressTable";
import { WorldDots } from "./brief/WorldDots";
function pairAxis(a: Persona, b: Persona): "device" | "identity" | "country" | null {
  return a.config.device !== b.config.device ? "device" : a.config.identity !== b.config.identity ? "identity" : a.config.country !== b.config.country ? "country" : null;
}
export function Brief({ personas, stressTests }: { personas: Persona[]; stressTests: StressTest[] }) {
  const byId = Object.fromEntries(personas.map(p => [p.id, p]));
  const rendered = new Set<string>();
  const items: React.ReactNode[] = [];
  personas.forEach((p, i) => {
    if (rendered.has(p.id)) return;
    const mate = p.pair_id ? byId[p.pair_id] : null;
    if (mate) {
      const axis = pairAxis(p, mate); rendered.add(p.id); rendered.add(mate.id);
      items.push(
        <div key={p.id + mate.id} style={{ position: "relative", gridColumn: "span 2", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, minWidth: 0 }}>
          <PersonaCard p={p} pairAxis={axis} index={i} /><PersonaCard p={mate} pairAxis={axis} index={i + 1} />
          <span style={{ position: "absolute", left: "50%", top: 58, transform: "translateX(-50%)", width: 40, height: 1, background: "#FF5A1F", pointerEvents: "none" }} />
          <span style={{ position: "absolute", left: "50%", top: 66, transform: "translateX(-50%)", fontFamily: "var(--font-mono)", fontSize: 8, letterSpacing: "0.12em", color: "#FF5A1F", background: "#FAF7F2", border: "1px solid #FF5A1F", padding: "3px 6px", whiteSpace: "nowrap", pointerEvents: "none" }}>MATCHED PAIR · {axis?.toUpperCase()}</span>
        </div>);
    } else { rendered.add(p.id); items.push(<PersonaCard key={p.id} p={p} pairAxis={null} index={i} />); }
  });
  return (
    <section style={{ display: "flex", flexDirection: "column", gap: 44, padding: "44px 32px 72px", maxWidth: 1400, width: "100%", boxSizing: "border-box", margin: "0 auto" }}>
      <Serif size="clamp(38px, 4.6vw, 68px)" style={{ maxWidth: 900, lineHeight: 0.98 }}><TextScramble duration={0.9}>Here's who we'll send.</TextScramble></Serif>
      <WorldDots personas={personas} />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 16, alignItems: "stretch", gridAutoRows: "1fr" }}>{items}</div>
      <StressTable rows={stressTests} />
    </section>);
}
```

Mount in `App.tsx`: `{state.personas.length > 0 && <Brief personas={state.personas} stressTests={state.stress_tests} />}`.

Run: `npx vitest run` → `17 passed`. Visual check against `Iris 03 Brief.dc.html`. Commit: `git commit -am "feat(web): Brief screen (map, personas, matched pair, stress table)"`.

---

## Task 12: Screen 4 — Swarm (port of `Iris 04 Swarm*.dc.html`)

**Files:**
- Create: `web/src/screens/Swarm.tsx`, `web/src/screens/swarm/FeedCard.tsx`
- Test: `web/test/swarm.test.tsx`

Exact values in `design/EXTRACTION.md` §4. Decisions: fixed 4 columns; DONE shell border green; tally derived from state.

- [ ] **Step 1: Test**

```tsx
// web/test/swarm.test.tsx
import { render, screen } from "@testing-library/react";
import { Swarm } from "../src/screens/Swarm";
import { initialState, reduce } from "../src/state/reducer";
import { buildScript } from "../src/data/script";
import demo from "../src/data/iris_demo.json";
it("renders eight feeds with derived tally and status overlays", () => {
  const s = buildScript(demo as any).reduce((st, c) => reduce(st, c.item), initialState(demo as any));
  render(<Swarm state={s} />);
  expect(screen.getByText("0 RUNNING · 5 DONE · 2 STALLED · 1 ERROR")).toBeInTheDocument();
  expect(screen.getAllByText("STALLED").length).toBeGreaterThanOrEqual(2);
  expect(screen.getByText("TOOLING ERROR · EXCLUDED")).toBeInTheDocument();
  expect(screen.getByText("overlay keeps intercepting clicks")).toBeInTheDocument();
});
```

- [ ] **Step 2: Components**

```tsx
// web/src/screens/swarm/FeedCard.tsx
import { motion } from "motion/react";
import { AsciiImage } from "../../texture/AsciiImage";
import { PixelDissolve } from "../../primitives/PixelDissolve";
import { Reticle } from "../../primitives/Reticle";
import type { Feed, Persona } from "../../types";
const GRAD: Record<number, string> = { 1: "linear-gradient(150deg, #FFD9CF, #F3E9D2)", 2: "linear-gradient(150deg, #F3E9D2, #FFD9CF)", 3: "linear-gradient(150deg, #E5DDF5, #D8ECE3)", 4: "linear-gradient(150deg, #D8ECE3, #E5DDF5)" };
const SHELL: Record<Feed["status"], React.CSSProperties> = {
  running: { border: "1px solid rgba(20,20,20,0.14)", background: "#FAF7F2" }, completed: { border: "1px solid rgba(31,157,85,0.5)", background: "#FAF7F2" },
  stalled: { border: "1px solid rgba(217,48,37,0.5)", background: "#FAF7F2" }, harness_error: { border: "1px solid rgba(20,20,20,0.12)", background: "rgba(20,20,20,0.02)" } };
const MARK: Record<Feed["status"], string> = { running: "#FF5A1F", completed: "#1F9D55", stalled: "#D93025", harness_error: "#8A8580" };
const pill = (status: Feed["status"]): React.CSSProperties => ({ display: "flex", alignItems: "center", gap: status === "completed" ? 4 : 5, fontFamily: "var(--font-mono)", fontSize: 8, letterSpacing: "0.1em", padding: "3px 5px", whiteSpace: "nowrap", flexShrink: 0,
  color: MARK[status], border: `1px solid ${status === "harness_error" ? "rgba(20,20,20,0.2)" : MARK[status]}` });
const LABEL: Record<Feed["status"], string> = { running: "RUNNING", completed: "✓ DONE", stalled: "STALLED", harness_error: "ERROR" };
export function FeedCard({ feed, persona, focused, index, scanSeconds }: { feed: Feed; persona: Persona | undefined; focused: boolean; index: number; scanSeconds: number }) {
  const err = feed.status === "harness_error"; const muted = err ? "#8A8580" : "#141414";
  const url = (feed.last_observation || `https://northwindoutfitters.com`).replace(/^https?:\/\//, "");
  const chips = persona ? [persona.config.device, persona.config.country, persona.config.identity === "fresh" ? "new" : "returning"] : [];
  return (
    <motion.div layout initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.08, duration: 0.3 }}
      style={{ position: "relative", display: "flex", flexDirection: "column", gap: 9, padding: 12, minWidth: 0, ...SHELL[feed.status] }}>
      {focused && <Reticle layoutId="swarm-reticle" size={13} thickness={2} inset={-5} />}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8 }}>
        <span style={{ fontSize: 14, lineHeight: 1.25, letterSpacing: "-0.005em", color: muted }}>{persona?.segment ?? feed.run_id}</span>
        <span style={pill(feed.status)}>{feed.status === "running" && <span style={{ width: 4, height: 4, background: "#FF5A1F", borderRadius: "50%", display: "block", animation: "irisPulse 1.4s ease-in-out infinite" }} />}{LABEL[feed.status]}</span>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>{chips.map(c => <span key={c} style={{ fontFamily: "var(--font-mono)", fontSize: 8, letterSpacing: "0.1em", textTransform: "uppercase", color: muted, border: `1px solid rgba(20,20,20,${err ? 0.14 : 0.18})`, padding: "2px 5px" }}>{c}</span>)}</div>
      <div style={{ flex: "none", aspectRatio: "16 / 10", border: `1px solid ${feed.status === "stalled" ? "rgba(217,48,37,0.3)" : feed.status === "completed" ? "rgba(31,157,85,0.3)" : err ? "rgba(20,20,20,0.1)" : "rgba(20,20,20,0.12)"}`, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 5, padding: "5px 7px", borderBottom: `1px solid rgba(20,20,20,${err ? 0.08 : 0.1})` }}>
          {[0, 1].map(i => <span key={i} style={{ width: 4, height: 4, background: `rgba(20,20,20,${err ? 0.16 : 0.22})`, display: "block" }} />)}
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 8, color: err ? "rgba(138,133,128,0.7)" : "#8A8580", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{url}</span>
        </div>
        {err ? (
          <div style={{ flex: 1, background: "rgba(20,20,20,0.06)", display: "flex", alignItems: "center", justifyContent: "center", padding: 8 }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.12em", color: "#8A8580", textAlign: "center" }}>TOOLING ERROR · EXCLUDED</span></div>
        ) : (
          <PixelDissolve trigger={feed.status} style={{ flex: 1, position: "relative", background: GRAD[persona?.pastel ?? 1], overflow: "hidden" }}>
            <AsciiImage seed={feed.run_id + feed.step} cols={60} rows={28} fontSize={7} style={{ background: "transparent", padding: 6, lineHeight: "8px", color: "rgba(20,20,20,0.44)" }} />
            {feed.status === "running" && <span aria-hidden style={{ position: "absolute", left: 0, right: 0, height: 1, background: "#FF5A1F", boxShadow: "0 0 8px rgba(255,90,31,0.5)", animation: `irisScan ${scanSeconds}s linear infinite` }} />}
            {feed.status === "stalled" && <span style={{ position: "absolute", inset: 0, background: "rgba(217,48,37,0.3)", display: "flex", alignItems: "center", justifyContent: "center" }}><span style={{ fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 500, letterSpacing: "0.16em", color: "#FFFFFF" }}>STALLED</span></span>}
            {feed.status === "completed" && <span style={{ position: "absolute", inset: 0, background: "rgba(31,157,85,0.32)", display: "flex", alignItems: "center", justifyContent: "center" }}><span style={{ fontSize: 44, lineHeight: 1, color: "#FFFFFF" }}>✓</span></span>}
          </PixelDissolve>)}
      </div>
      <div style={{ display: "flex", gap: 5 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: MARK[feed.status], flexShrink: 0 }}>&gt;</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, lineHeight: 1.45, color: muted }}>{feed.last_action}</span>
      </div>
    </motion.div>);
}
```

```tsx
// web/src/screens/Swarm.tsx
import { Serif } from "../primitives/Serif";
import { TextScramble } from "../primitives/TextScramble";
import { counts } from "../state/reducer";
import type { RunState } from "../types";
import { FeedCard } from "./swarm/FeedCard";
const SCAN = [2.2, 2.6, 1.9, 2.4, 2.1, 2.3, 2.0, 2.5];
export function Swarm({ state }: { state: RunState }) {
  const c = counts(state);
  const byRun = Object.fromEntries(state.personas.map(p => [p.run_id, p]));
  const feeds = state.personas.map(p => state.feeds[p.run_id]).filter(Boolean);   // persona order = grid order
  return (
    <section style={{ display: "flex", flexDirection: "column", gap: 24, padding: "32px 32px 40px", maxWidth: 1400, width: "100%", boxSizing: "border-box", margin: "0 auto" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <Serif size="clamp(38px, 4.6vw, 68px)" style={{ lineHeight: 0.98 }}><TextScramble duration={0.9}>Watch them try.</TextScramble></Serif>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, letterSpacing: "0.16em", color: "#8A8580" }}>{`${c.running} RUNNING · ${c.done} DONE · ${c.stalled} STALLED · ${c.error} ERROR`}</span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 16, alignItems: "stretch", gridAutoRows: "1fr" }}>
        {feeds.map((f, i) => <FeedCard key={f.run_id} feed={f} persona={byRun[f.run_id]} focused={state.focus === f.run_id} index={i} scanSeconds={SCAN[i % SCAN.length]} />)}
      </div>
    </section>);
}
```

Mount in `App.tsx`: `{Object.keys(state.feeds).length > 0 && <Swarm state={state} />}`.

Run: `npx vitest run` → `18 passed`. Visual check against Swarm A and B. Commit: `git commit -am "feat(web): Swarm screen (feed wall, reticle, status overlays)"`.

---

## Task 13: Screen 5 — Report (port of `Iris 05 Report.dc.html`)

**Files:**
- Create: `web/src/screens/Report.tsx`, `web/src/screens/report/FlagRow.tsx`, `web/src/screens/report/FlagDetail.tsx`
- Test: `web/test/report.test.tsx`

Exact values in `design/EXTRACTION.md` §5. The quote shown in the detail is the persona's evidence for the finding's run, and the replay caption uses `step_index` and `replay_offset_s`.

- [ ] **Step 1: Test**

```tsx
// web/test/report.test.tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { Report } from "../src/screens/Report";
import demo from "../src/data/iris_demo.json";
it("shows both scores, ranked flags, and switches detail on click", () => {
  render(<Report scorecard={demo.scorecard as any} findings={demo.findings as any} affected={demo.affected as any} personas={demo.personas as any} instant />);
  expect(screen.getByText("85")).toBeInTheDocument(); expect(screen.getByText("58")).toBeInTheDocument();
  expect(screen.getByText("1 RUN EXCLUDED · TOOLING ERROR")).toBeInTheDocument();
  const rows = screen.getAllByText(/OF SHOPPERS/); expect(rows[0]).toHaveTextContent("~63%");   // ranked by share desc
  fireEvent.click(screen.getByText("Cookie wall"));
  expect(screen.getByText(/OK button is 16px on mobile/)).toBeInTheDocument();
  expect(screen.getByText("STEP 4 · 00:41")).toBeInTheDocument();
});
```

- [ ] **Step 2: Components**

```tsx
// web/src/screens/report/FlagRow.tsx
import type { Finding, Persona } from "../../types";
const TITLE: Record<string, string> = { cookie_wall: "Cookie wall", icon_only_control: "Icon-only cart button", geo_block: "Geo-blocked pricing", hidden_nav: "Hidden mobile nav", captcha: "CAPTCHA wall", ambiguous_cta: "Ambiguous call to action", infinite_scroll: "Infinite scroll", login_wall: "Login wall", layout_shift: "Layout shift", timeout: "Timed out", other: "Other" };
export const flagTitle = (f: Finding) => TITLE[f.category] ?? f.category;
export const severity = (f: Finding) => f.attributed_to === "site" ? { text: "FAILS FOR EVERYONE", color: "#D93025", bg: "rgba(217,48,37,0.1)" } : { text: `FAILS ONLY ON ${f.attributed_to === "device" ? f.config.device : f.attributed_to === "country" ? f.config.country : f.attributed_to === "identity" ? "RETURNING" : "VISION AGENTS"}`.toUpperCase(), color: "#FF5A1F", bg: "rgba(255,90,31,0.12)" };
const GRAD: Record<number, string> = { 1: "linear-gradient(150deg, #FFD9CF, #F3E9D2)", 2: "linear-gradient(150deg, #F3E9D2, #FFD9CF)", 3: "linear-gradient(150deg, #E5DDF5, #D8ECE3)", 4: "linear-gradient(150deg, #D8ECE3, #E5DDF5)" };
export const Avatar = ({ pastel }: { pastel: number }) => (
  <span style={{ width: 22, height: 22, background: GRAD[pastel] ?? GRAD[1], overflow: "hidden", display: "block" }}>
    <pre style={{ margin: 0, fontFamily: "var(--font-mono)", fontSize: 5, lineHeight: "5px", color: "rgba(20,20,20,0.5)", whiteSpace: "pre" }}>{" ;tt; \n;fCCf;\n1LGGL1\nfCG0GC"}</pre></span>);
export function FlagRow({ f, selected, share, people, onSelect }: { f: Finding; selected: boolean; share: number; people: Persona[]; onSelect: () => void }) {
  const sev = severity(f);
  return (
    <div role="button" onClick={onSelect} style={{ display: "flex", flexDirection: "column", gap: 9, padding: "16px 0", borderBottom: "1px solid rgba(20,20,20,0.1)", background: selected ? "rgba(255,90,31,0.05)" : "transparent", cursor: "pointer" }}>
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10, padding: "0 12px" }}>
        <span style={{ fontSize: 17, letterSpacing: "-0.01em" }}>{flagTitle(f)}</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", color: sev.color, background: sev.bg, padding: "3px 6px", whiteSpace: "nowrap" }}>{sev.text}</span>
        {f.engine_consensus && <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", color: "#FFFFFF", background: "#141414", padding: "3px 6px" }}>EVERY ENGINE</span>}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8, padding: "0 12px" }}>
        <span style={{ display: "flex", gap: 4 }}>{people.map(p => <Avatar key={p.id} pastel={p.pastel} />)}</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em", color: "#8A8580" }}>{`~${Math.round(share * 100)}% OF SHOPPERS`}</span>
      </div>
    </div>);
}
```

```tsx
// web/src/screens/report/FlagDetail.tsx
import { AsciiImage } from "../../texture/AsciiImage";
import { Reticle } from "../../primitives/Reticle";
import { sourceName } from "../brief/PersonaCard";
import type { Finding, Persona } from "../../types";
const mmss = (s: number | null) => { const n = Math.max(0, Math.round(s ?? 0)); return `${String(Math.floor(n / 60)).padStart(2, "0")}:${String(n % 60).padStart(2, "0")}`; };
export function FlagDetail({ f, persona }: { f: Finding; persona: Persona | undefined }) {
  const url = (f.replay_url ?? "").replace(/^https?:\/\//, "");
  const q = persona?.evidence;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24, minWidth: 0 }}>
      <span style={{ fontSize: 24, lineHeight: 1.35, letterSpacing: "-0.01em", maxWidth: 640, textWrap: "pretty" }}>{f.description}</span>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 20, alignItems: "stretch" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 12, border: "1px solid rgba(20,20,20,0.14)", background: "#FAF7F2", padding: 14, minWidth: 0 }}>
          <div style={{ background: "linear-gradient(150deg, #FFD9CF, #F3E9D2)", border: "1px solid rgba(20,20,20,0.08)", height: 84, overflow: "hidden" }}>
            <AsciiImage seed={q?.source_id ?? "evidence"} cols={110} rows={13} fontSize={7} style={{ background: "transparent", padding: 6, lineHeight: "8px", color: "rgba(20,20,20,0.42)" }} /></div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em", color: "#8A8580", textTransform: "uppercase" }}>{q ? `${sourceName(q.source_id)} · ${q.date}` : "NO CUSTOMER QUOTE · AGENT-READINESS FLAG"}</span>
          {q && <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, lineHeight: 1.6, color: "#141414" }}>"{q.text}"</span>}
          {q?.url && <a href={q.url} target="_blank" rel="noreferrer" style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em", color: "#FF5A1F" }}>READ THE REVIEW ↗</a>}
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12, border: "1px solid rgba(20,20,20,0.14)", background: "#FAF7F2", padding: 14, minWidth: 0 }}>
          <div style={{ border: "1px solid rgba(20,20,20,0.12)", display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "6px 8px", borderBottom: "1px solid rgba(20,20,20,0.1)" }}>
              {[0, 1].map(i => <span key={i} style={{ width: 5, height: 5, background: "rgba(20,20,20,0.22)", display: "block" }} />)}
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 8, color: "#8A8580", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{url}</span></div>
            <div style={{ position: "relative", height: 150, background: "linear-gradient(150deg, #F3E9D2, #FFD9CF)", overflow: "hidden" }}>
              <AsciiImage seed={f.session_id ?? f.id} cols={110} rows={22} fontSize={7} style={{ background: "transparent", padding: 6, lineHeight: "8px", color: "rgba(20,20,20,0.42)" }} />
              <span style={{ position: "absolute", left: "46%", top: "58%", width: 34, height: 20, border: "1px solid rgba(20,20,20,0.45)", background: "rgba(250,247,242,0.9)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-mono)", fontSize: 8, color: "#141414" }}>OK
                <Reticle layoutId={`replay-${f.id}`} size={9} thickness={2} inset={-7} /></span>
            </div>
          </div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.12em", color: "#FF5A1F" }}>{`STEP ${f.step_index ?? "–"} · ${mmss(f.replay_offset_s)}`}</span>
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 14, border: "1px solid rgba(31,157,85,0.45)", background: "rgba(31,157,85,0.07)", padding: 18 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 500, letterSpacing: "0.16em", color: "#1F9D55" }}>PROPOSED FIX</span>
        <span style={{ fontSize: 15, lineHeight: 1.6, color: "#141414", maxWidth: 640, textWrap: "pretty" }}>{f.proposed_fix}</span>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          <a href={f.replay_url ?? "#"} target="_blank" rel="noreferrer" className="btn-primary" style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 500, letterSpacing: "0.12em", color: "#FFFFFF", background: "#FF5A1F", border: "none", padding: "13px 22px", whiteSpace: "nowrap" }}>OPEN REPLAY ↗</a>
          <button onClick={() => navigator.clipboard?.writeText(f.proposed_fix)} className="btn-secondary" style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 500, letterSpacing: "0.12em", color: "#141414", background: "transparent", border: "1px solid rgba(20,20,20,0.3)", padding: "13px 22px", cursor: "pointer", whiteSpace: "nowrap" }}>COPY FIX</button>
        </div>
      </div>
    </div>);
}
```

Add to `tokens.css`: `.btn-primary:hover { background: #E44B12 !important; } .btn-secondary:hover { border-color: #141414 !important; } .btn-primary:active, .btn-secondary:active { transform: translateY(1px); }`.

```tsx
// web/src/screens/Report.tsx
import { useMemo, useState } from "react";
import { NumberTick } from "../primitives/NumberTick";
import { Serif } from "../primitives/Serif";
import { TextScramble } from "../primitives/TextScramble";
import type { Finding, Persona, ResultItem, ScoreCard } from "../types";
import { FlagDetail } from "./report/FlagDetail";
import { FlagRow } from "./report/FlagRow";
export function Report({ scorecard, findings, affected, personas, instant = false }: { scorecard: ScoreCard; findings: Finding[]; affected: ResultItem["affected"]; personas: Persona[]; instant?: boolean }) {
  const ranked = useMemo(() => [...findings].sort((a, b) => (affected[b.id]?.share ?? 0) - (affected[a.id]?.share ?? 0)), [findings, affected]);
  const [sel, setSel] = useState<string>(ranked[0]?.id);
  const f = ranked.find(x => x.id === sel) ?? ranked[0];
  const byId = Object.fromEntries(personas.map(p => [p.id, p]));
  const bySession = Object.fromEntries(personas.map(p => [`sess-${p.run_id}`, p]));
  const excluded = scorecard.per_journey.reduce((a, j) => a + j.harness_errors, 0);
  const agents = personas.length; const journeys = scorecard.per_journey.length;
  const num: React.CSSProperties = { fontFamily: "var(--font-mono)", fontSize: "clamp(72px, 10vw, 132px)", lineHeight: 0.86, letterSpacing: "-0.04em" };
  const cap: React.CSSProperties = { fontFamily: "var(--font-mono)", fontSize: 11, lineHeight: 1.6, letterSpacing: "0.12em" };
  return (
    <section style={{ display: "flex", flexDirection: "column", gap: 44, padding: "48px 32px 72px", maxWidth: 1400, width: "100%", boxSizing: "border-box", margin: "0 auto" }}>
      <Serif size="clamp(38px, 4.6vw, 68px)" style={{ maxWidth: 900, lineHeight: 0.98 }}><TextScramble duration={0.9}>What broke, for whom, and why.</TextScramble></Serif>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 28, borderTop: "1px solid rgba(20,20,20,0.16)", borderBottom: "1px solid rgba(20,20,20,0.16)", padding: "26px 0" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, minWidth: 0 }}>
            <span style={{ ...num, color: "#8A8580" }}>{scorecard.static_score == null ? "—" : <NumberTick value={scorecard.static_score} instant={instant} duration={1.0} />}</span>
            <span style={{ ...cap, color: "#8A8580" }}>CLOUDFLARE STATIC SCORE · robots.txt, llms.txt, headers</span></div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, minWidth: 0 }}>
            <span style={{ ...num, color: "#FF5A1F" }}><NumberTick value={scorecard.overall} instant={instant} duration={1.2} /></span>
            <span style={{ ...cap, color: "#141414" }}>{`IRIS MEASURED · ${agents} real agents, ${journeys} journeys`}</span></div>
        </div>
        {excluded > 0 && <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.14em", color: "#8A8580" }}>{`${excluded} RUN${excluded === 1 ? "" : "S"} EXCLUDED · TOOLING ERROR`}</span>}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 1fr) minmax(0, 2fr)", gap: 40, alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", minWidth: 0, borderTop: "1px solid rgba(20,20,20,0.14)" }}>
          {ranked.map(x => <FlagRow key={x.id} f={x} selected={x.id === f?.id} share={affected[x.id]?.share ?? 0} people={(affected[x.id]?.persona_ids ?? []).map(id => byId[id]).filter(Boolean)} onSelect={() => setSel(x.id)} />)}
        </div>
        {f && <FlagDetail f={f} persona={f.session_id ? bySession[f.session_id] : undefined} />}
      </div>
    </section>);
}
```

Mount in `App.tsx`: `{state.scorecard && <Report scorecard={state.scorecard} findings={state.findings} affected={state.affected} personas={state.personas} />}`.

Run: `npx vitest run` → `19 passed`. Visual check against `Iris 05 Report.dc.html`. Commit: `git commit -am "feat(web): Report screen (scores, flags, detail, fix)"`.

---

## Task 14: Page choreography — stage transitions, auto-scroll, stage bar, cached pill

**Files:**
- Modify: `web/src/App.tsx`
- Test: `web/test/app.test.tsx`

Design-brief §5. Each stage section enters with a pixel-dissolve; the page scrolls to the newest stage; the top bar's BRIEF step lights when personas land; FINDINGS lights during `score`; REPORT on `done`.

- [ ] **Step 1: Test**

```tsx
// web/test/app.test.tsx
import { render, screen, act, fireEvent } from "@testing-library/react";
import App from "../src/App";
it("plays the whole show at high speed and reaches the report", async () => {
  vi.useFakeTimers();
  window.history.replaceState({}, "", "/?speed=50");
  render(<App />);
  fireEvent.click(screen.getByText("RUN IRIS →"));
  for (let i = 0; i < 40; i++) await act(async () => { vi.advanceTimersByTime(250); });
  expect(screen.getByText("What broke, for whom, and why.")).toBeInTheDocument();
  expect(screen.getAllByText(/OF SHOPPERS/).length).toBe(4);
  vi.useRealTimers();
});
```

- [ ] **Step 2: App**

```tsx
// web/src/App.tsx
import { useEffect, useRef } from "react";
import { AnimatePresence, motion } from "motion/react";
import { TopBar } from "./components/TopBar";
import { PixelDissolve } from "./primitives/PixelDissolve";
import { counts } from "./state/reducer";
import { usePlayer } from "./state/usePlayer";
import { Input } from "./screens/Input";
import { Learning } from "./screens/Learning";
import { Brief } from "./screens/Brief";
import { Swarm } from "./screens/Swarm";
import { Report } from "./screens/Report";

function Stage({ id, children }: { id: string; children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => { ref.current?.scrollIntoView({ behavior: "smooth", block: "start" }); }, []);
  return (
    <motion.div ref={ref} id={id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }} style={{ scrollMarginTop: 64 }}>
      <PixelDissolve trigger={id} duration={0.6}>{children}</PixelDissolve>
    </motion.div>);
}

export default function App() {
  const { state, start } = usePlayer();
  const cached = new URLSearchParams(location.search).get("demo") === "cached";
  const barStage = state.stage === "score" ? "score" : state.stage;
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <TopBar stage={barStage} sessions={counts(state).total} cached={cached} hasBrief={state.personas.length > 0 && state.stage === "explore"} />
      <main style={{ flex: 1 }}>
        <Input onRun={() => start()} collapsed={state.stage !== "idle"} />
        <AnimatePresence>
          {state.stage !== "idle" && <Stage key="learn" id="learn"><Learning state={state} /></Stage>}
          {state.personas.length > 0 && <Stage key="brief" id="brief"><Brief personas={state.personas} stressTests={state.stress_tests} /></Stage>}
          {Object.keys(state.feeds).length > 0 && <Stage key="swarm" id="swarm"><Swarm state={state} /></Stage>}
          {state.scorecard && <Stage key="report" id="report"><Report scorecard={state.scorecard} findings={state.findings} affected={state.affected} personas={state.personas} /></Stage>}
        </AnimatePresence>
      </main>
    </div>);
}
```

`TopBar` must map: `explore` → LEARN current (or BRIEF when `hasBrief`); `run` → SWARM; `score` → FINDINGS; `done` → REPORT. Update the `ORDER` logic in `TopBar.tsx` so `score` maps to index 3 and `done` to index 4 (already true given `STEPS`), and when `stage === "done"` render the REPORT chip without the pulsing dot (the export's dotless variant).

- [ ] **Step 3: Run everything**

Run: `npx vitest run` → `20 passed`. Run `npm run dev` at 1440×900: the full show plays in about 60 seconds; every stage matches its frame; the reticle hops between source cards and between feed cards; numbers tick on the report. Then `npm run build` → no type errors.

Commit: `git commit -am "feat(web): stage choreography, auto-scroll, stage bar mapping"`.

---

## Task 15: End-to-end tests with Playwright (screenshots per stage)

**Files:**
- Create: `web/playwright.config.ts`, `web/e2e/demo.spec.ts`
- Modify: `web/package.json` scripts

- [ ] **Step 1: Config**

```ts
// web/playwright.config.ts
import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "e2e", timeout: 90_000, retries: 0,
  use: { baseURL: "http://127.0.0.1:4173", viewport: { width: 1440, height: 900 }, screenshot: "only-on-failure" },
  webServer: { command: "npm run build && npm run preview -- --host 127.0.0.1 --port 4173", url: "http://127.0.0.1:4173", reuseExistingServer: true, timeout: 120_000 },
});
```

Add scripts to `package.json`: `"test": "vitest run"`, `"e2e": "playwright test"`, `"preview": "vite preview"`.

- [ ] **Step 2: The spec (drives the show, asserts each stage, saves screenshots for the reviewer)**

```ts
// web/e2e/demo.spec.ts
import { expect, test } from "@playwright/test";

test("the full show plays through and each stage renders", async ({ page }) => {
  await page.goto("/?speed=6");
  await expect(page.getByText("Send your customers in first.")).toBeVisible();
  await page.screenshot({ path: "e2e/screens/01-input.png" });
  await page.getByRole("button", { name: "RUN IRIS →" }).click();

  await expect(page.getByText("Learning your customers and your site.")).toBeVisible();
  await expect(page.getByText("checkout resets on my phone every time")).toBeVisible({ timeout: 20_000 });
  await page.screenshot({ path: "e2e/screens/02-learning.png", fullPage: false });

  await expect(page.getByText("Here's who we'll send.")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("MATCHED PAIR · DEVICE")).toBeVisible();
  await page.screenshot({ path: "e2e/screens/03-brief.png" });

  await expect(page.getByText("Watch them try.")).toBeVisible({ timeout: 30_000 });
  await expect(page.locator("text=RUNNING").first()).toBeVisible();
  await page.screenshot({ path: "e2e/screens/04-swarm-running.png" });
  await expect(page.getByText("TOOLING ERROR · EXCLUDED")).toBeVisible({ timeout: 40_000 });

  await expect(page.getByText("What broke, for whom, and why.")).toBeVisible({ timeout: 40_000 });
  await expect(page.getByText("IRIS MEASURED · 8 real agents, 3 journeys")).toBeVisible();
  await expect(page.getByText("58")).toBeVisible({ timeout: 5_000 });
  await page.screenshot({ path: "e2e/screens/05-report.png", fullPage: true });
  await expect(page.getByText("REPORT")).toHaveCSS("color", "rgb(255, 90, 31)");
});

test("seek to a stage renders it instantly (rehearsal / screenshot mode)", async ({ page }) => {
  await page.goto("/?stage=run");
  await expect(page.getByText("Watch them try.")).toBeVisible();
  await expect(page.locator("text=RUNNING")).toHaveCount(0);           // seeking past 'run' marker only; feeds arrive after it
  await page.goto("/?stage=done");
  await expect(page.getByText("What broke, for whom, and why.")).toBeVisible();
  await expect(page.getAllByText(/OF SHOPPERS/)).toHaveCount(4);
});
```

Note on the second test: `seekToStage("run")` dispatches up to and including the `run` marker, so no feeds yet; `seekToStage("done")` dispatches everything. If the first assertion is too brittle, assert on the heading only.

- [ ] **Step 3: Run and commit**

Run: `cd web && npx playwright test` → Expected: `2 passed`, and five PNGs in `web/e2e/screens/`. Open them and compare against `design/frames/`. Commit the screenshots too: `git add web/e2e && git commit -m "test(web): playwright e2e for the full show with stage screenshots"`.

---

## Task 16: Deploy to Vercel (new project `iris`)

**Files:**
- Create: `web/vercel.json`

- [ ] **Step 1: SPA rewrite so query-only routes work from any path**

```json
{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
```

- [ ] **Step 2: Link and deploy (CLI is logged in as `smitsp11`, scope `smitsp11s-projects`)**

```bash
cd web
vercel link --yes --scope smitsp11s-projects --project iris
vercel --prod --yes
```

Expected: a `https://iris-<hash>-smitsp11s-projects.vercel.app` production URL printed. Vercel auto-detects Vite (`vite build`, output `dist`).

- [ ] **Step 3: Verify the deployment headlessly**

```bash
URL=$(vercel ls iris --scope smitsp11s-projects 2>/dev/null | grep -o 'https://[^ ]*' | head -1)
curl -s -o /dev/null -w "%{http_code}\n" "$URL"          # 200
curl -s "$URL" | grep -c "Iris"                            # ≥ 1
```

Then run the Playwright spec against it once: `PLAYWRIGHT_BASE_URL=$URL npx playwright test e2e/demo.spec.ts` (add `baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:4173"` to the config and skip `webServer` when the env var is set).

- [ ] **Step 4: Commit**

`git add web/vercel.json && git commit -m "chore(web): vercel config"`. Record the production URL in `web/README.md`.

---

## Task 17: Docs — contract additions and README

**Files:**
- Create: `web/README.md`, `docs/api.md`

- [ ] **Step 1: `web/README.md`**: how to run (`npm run dev`), test (`npm test`, `npm run e2e`), the URL params (`?speed=`, `?stage=`, `?demo=cached`), the deploy command, and a one-paragraph pointer to `docs/design-brief.md` and `design/EXTRACTION.md`.
- [ ] **Step 2: `docs/api.md`**: the stream contract the front end consumes, so Dev B's API can produce it later. Backend items unchanged from `crucible/schemas.py` (`stage`, `session_started`, `run_event`, `run_result`); Iris additions: `source_read {source_id, quotes[]}`, `site_model {site_model, nodes[]}`, `brief {personas[], stress_tests[]}`, `result {scorecard, findings[], affected{}}`. Copy the TS shapes from `web/src/types.ts` verbatim.
- [ ] **Step 3:** `git commit -am "docs: web README and stream contract"`.

---

## Self-review against the brief and the frames

- Tokens, fonts, dot-field, keyframes — Task 1 (§2 of the brief; `EXTRACTION.md` §0).
- Textures generated live (ASCII, dither) with procedural fallback — Task 6 (§6).
- Motion vocabulary: reticle, scan-line, tick, scramble, pixel-dissolve — Task 7; choreography order and timings — Tasks 4 and 14 (§5).
- Five frames ported with exact styles — Tasks 9–13 (`EXTRACTION.md` §1–5); B-states are reducer states, not separate screens.
- Stage-readable constraints (headline ≥56px, score numerals largest on page) — carried by the export values.
- Persistent frame and one-page navigation — Tasks 8 and 14.
- Cached mode — the whole build is cached mode; `?demo=cached` shows the pill (§"What the UI must achieve").
- Tests: 20 unit tests plus 2 end-to-end runs with stage screenshots — Tasks 1–15.
- Deploy: Vercel project `iris` — Task 16.
- Type consistency: `Feed.status` uses `FeedStatus` everywhere; `Reticle` props (`size`, `thickness`, `inset`, `layoutId`) match all call sites; `AsciiImage` props (`src?`, `seed`, `cols`, `rows`, `fontSize`, `pastel?`, `style`) match all call sites; `counts()` fields `running/done/stalled/error/total` match Swarm and TopBar usage.
