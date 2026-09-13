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
