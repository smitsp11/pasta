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
