import type { DemoData } from "../types";

/** Invariants every authored demo must satisfy so the screens and the attribution story hold. Returns a list of problems (empty = ok). */
export function validateDemo(d: DemoData): string[] {
  const errs: string[] = [];
  const personaIds = new Set(d.personas.map(p => p.id));
  const runIds = new Set(d.runs.map(r => r.run_id));
  const sourceIds = new Set(d.sources.map(s => s.id));
  const paths = new Set(d.nodes.map(n => n.path));
  if (d.personas.length !== 8) errs.push(`expected 8 personas, got ${d.personas.length}`);
  if (d.runs.length !== 8) errs.push(`expected 8 runs, got ${d.runs.length}`);
  for (const p of d.personas) {
    if (!runIds.has(p.run_id)) errs.push(`persona ${p.id} run ${p.run_id} missing`);
    if (!sourceIds.has(p.evidence.source_id)) errs.push(`persona ${p.id} evidence source ${p.evidence.source_id} unknown`);
    if (!d.site_model.journeys.some(j => j.id === p.journey_id)) errs.push(`persona ${p.id} journey ${p.journey_id} unknown`);
  }
  for (const r of d.runs) {
    if (!personaIds.has(r.persona_id)) errs.push(`run ${r.run_id} persona ${r.persona_id} missing`);
    if (r.outcome === "stalled" && (r.failure_step_index == null || r.failure_step_index > r.steps.length)) errs.push(`run ${r.run_id} stalled without a valid failure_step_index`);
    if (r.steps.length === 0) errs.push(`run ${r.run_id} has no steps`);
  }
  const pair = d.personas.filter(p => p.pair_id);
  if (pair.length !== 2) errs.push(`expected exactly 2 paired personas, got ${pair.length}`);
  if (pair.length === 2) {
    const [a, b] = pair;
    if (a.pair_id !== b.id || b.pair_id !== a.id) errs.push("pair ids do not point at each other");
    const diff = (["device", "identity", "country", "engine"] as const).filter(k => a.config[k] !== b.config[k]);
    if (diff.length !== 1) errs.push(`matched pair must differ in exactly one config field, differs in ${diff.join(",") || "none"}`);
    const ra = d.runs.find(r => r.run_id === a.run_id), rb = d.runs.find(r => r.run_id === b.run_id);
    const outcomes = [ra?.outcome, rb?.outcome].sort().join("+");
    if (outcomes !== "completed+stalled") errs.push(`matched pair must be one completed and one stalled, got ${outcomes}`);
  }
  const outcomes = d.runs.map(r => r.outcome);
  if (outcomes.filter(o => o === "harness_error").length !== 1) errs.push("expected exactly one harness_error run");
  if (!outcomes.includes("stalled")) errs.push("expected at least one stalled run");
  for (const f of d.findings) {
    if (!d.affected[f.id]) errs.push(`finding ${f.id} has no affected entry`);
    for (const id of d.affected[f.id]?.persona_ids ?? []) if (!personaIds.has(id)) errs.push(`finding ${f.id} affects unknown persona ${id}`);
    if (f.session_id && !d.runs.some(r => r.session_id === f.session_id)) errs.push(`finding ${f.id} session ${f.session_id} matches no run`);
  }
  if (!d.findings.some(f => f.attributed_to === "site" && f.engine_consensus)) errs.push("expected one site-attributed engine_consensus finding");
  if (d.sources.map(s => s.id).join() !== d.reads.map(r => r.source_id).join()) errs.push("reads must be in the same order as sources");
  for (const j of d.site_model.journeys) if (!j.entry_url.startsWith(d.url.replace(/\/$/, "").replace(/^https?:\/\/(www\.)?/, "https://")) && !j.entry_url.includes(new URL(d.url).hostname.replace(/^www\./, ""))) errs.push(`journey ${j.id} entry_url is off-site`);
  if (![1, 2, 3].every(n => d.nodes.some(x => x.journey === n))) errs.push("nodes must mark journeys 1, 2 and 3");
  for (const n of d.nodes) if (n.parent && !paths.has(n.parent)) errs.push(`node ${n.path} parent ${n.parent} missing`);
  const sc = d.scorecard.per_journey;
  const total = sc.reduce((a, j) => a + j.completed + j.stalled + j.harness_errors, 0);
  if (total !== d.runs.length) errs.push(`scorecard per_journey counts sum to ${total}, expected ${d.runs.length}`);
  return errs;
}
