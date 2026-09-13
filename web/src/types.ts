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

// Authored demo show (one per target) ------------------------------------------
export interface DemoRun { run_id: string; persona_id: string; session_id: string; start_url: string; outcome: TerminalOutcome;
  failure_step_index: number | null; steps: [string, string][] }
export interface DemoData {
  url: string; site_model: SiteModel; nodes: SiteNode[]; sources: Source[];
  reads: { source_id: string; quotes: Quote[] }[]; personas: Persona[]; stress_tests: StressTest[];
  runs: DemoRun[]; findings: Finding[]; affected: ResultItem["affected"]; scorecard: ScoreCard;
}
