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
    <section className="pad-x" style={{ display: "flex", flexDirection: "column", gap: 24, padding: "32px 32px 40px", maxWidth: 1400, width: "100%", boxSizing: "border-box", margin: "0 auto" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <Serif size="clamp(38px, 4.6vw, 68px)" style={{ lineHeight: 0.98 }}><TextScramble duration={0.9}>Watch them try.</TextScramble></Serif>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, letterSpacing: "0.16em", color: "var(--muted)" }}>{`${c.running} RUNNING · ${c.done} DONE · ${c.stalled} STALLED · ${c.error} ERROR`}</span>
      </div>
      <div className="card-grid">
        {feeds.map((f, i) => <FeedCard key={f.run_id} feed={f} persona={byRun[f.run_id]} focused={state.focus === f.run_id} index={i} scanSeconds={SCAN[i % SCAN.length]} />)}
      </div>
    </section>);
}
