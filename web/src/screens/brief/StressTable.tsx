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
