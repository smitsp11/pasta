# Iris stream contract (what the front end consumes)

The front end folds a stream of items into `RunState` (`web/src/state/reducer.ts`). Today the stream comes from the
authored demo script; Dev B's API produces the same items over `WS /runs/{id}/events`. Shapes below are copied from
`web/src/types.ts`; backend items are unchanged from `crucible/schemas.py`.

## Endpoints (from docs/plan.md §2)

- `POST /runs {url, hint?, cached_site_model?}` → `{run_id}`
- `GET /runs/{id}` → `{stage, site_model?, scorecard?, findings?}`
- `WS /runs/{id}/events` → stream of the items below
- `GET /fixtures/demo` → `fixtures/demo_run.json`

## Backend items (unchanged from `crucible/schemas.py`)

```ts
interface StageMarker   { type: "stage"; name: "explore" | "run" | "score" | "fix" | "done"; timestamp: string }
interface SessionStarted { type: "session_started"; run_id: string; session_id: string; journey_id: string; config: Config;
  viewer_url: string; replay_url: string; hls_url: string; timestamp: string }
interface RunEvent      { type: "run_event"; run_id: string; session_id: string; journey_id: string; config: Config;
  step_index: number; timestamp: string; action: string; observation: string; screenshot_ref: string | null; outcome: Outcome }
interface RunResult     { type: "run_result"; run_id: string; journey_id: string; config: Config; session_id: string | null;
  outcome: TerminalOutcome; attempt: number; events: RunEvent[]; replay_url: string | null; hls_url: string | null;
  final_screenshot_ref: string | null; failure_step_index: number | null; replay_offset_s: number | null;
  harness_reason: string | null; stall_hint: string | null }
```

## Iris additions (frontend contract; the API must emit these too)

```ts
interface Source     { id: string; name: string; kind: "reviews" | "forum" | "appstore" | "help" | "competitor" | "social" | "support";
  pastel: 1 | 2 | 3 | 4; thumbnail: string | null }
interface Quote      { source_id: string; text: string; date: string; url: string | null }
interface Persona    { id: string; segment: string; config: Config; journey_id: string; goal: string; evidence: Quote;
  pastel: 1 | 2 | 3 | 4; run_id: string; pair_id: string | null }
interface StressTest { probe: string; why: string; source: string }
interface SiteNode   { path: string; parent: string | null; journey: number | null }

type SourceRead    = { type: "source_read"; source_id: string; quotes: Quote[]; timestamp: string };
type SiteModelItem = { type: "site_model"; site_model: SiteModel; nodes: SiteNode[] };   // re-sent as nodes grow
type BriefItem     = { type: "brief"; personas: Persona[]; stress_tests: StressTest[] };
type ResultItem    = { type: "result"; scorecard: ScoreCard; findings: Finding[];
  affected: Record<string, { persona_ids: string[]; share: number }> };                 // keyed by finding id

type StreamItem = StageMarker | SourceRead | SiteModelItem | BriefItem | SessionStarted | RunEvent | RunResult | ResultItem;
```

## Ordering the UI expects

1. `stage: explore`, then interleaved `source_read` and `site_model` items (research and site map run in parallel).
2. `brief` (eight personas; exactly two share a `pair_id` and differ in one config field).
3. `stage: run`, then per session `session_started` → `run_event`* → `run_result`. A `session_started` with an existing
   `run_id` replaces that feed (retry). `harness_error` results are shown grey and excluded from the score.
4. `stage: score`, then `result`, then `stage: done`.

The initial `Source[]` list (the research wall) and the target `url` are known before the stream starts; the API should
return them from `GET /runs/{id}` or emit them first.
