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
  const runCues: Cue[] = []; const tStart = t;
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
