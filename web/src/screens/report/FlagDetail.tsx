import { AsciiImage } from "../../texture/AsciiImage";
import { Reticle } from "../../primitives/Reticle";
import { sourceName } from "../brief/PersonaCard";
import { flagTitle, severity } from "./FlagRow";
import type { Finding, Persona, Source } from "../../types";
const mmss = (s: number | null) => { const n = Math.max(0, Math.round(s ?? 0)); return `${String(Math.floor(n / 60)).padStart(2, "0")}:${String(n % 60).padStart(2, "0")}`; };
const step: React.CSSProperties = { fontFamily: "var(--font-mono)", fontSize: 12, lineHeight: 1, color: "var(--ink)", background: "transparent", border: "1px solid var(--line)", padding: "6px 10px", cursor: "pointer" };
export function FlagDetail({ f, persona, sources, position, total, where, onPrev, onNext, ref }: { f: Finding; persona: Persona | undefined; sources: Source[]; position: number; total: number; where: string; onPrev?: () => void; onNext?: () => void; ref?: React.Ref<HTMLDivElement> }) {
  const url = (f.replay_url ?? "").replace(/^https?:\/\//, "");
  const q = persona?.evidence;
  const sev = severity(f);
  return (
    <div ref={ref} tabIndex={-1} aria-label={`Issue ${position} of ${total}: ${flagTitle(f)}`} style={{ display: "flex", flexDirection: "column", gap: 20, minWidth: 0, outline: "none", scrollMarginTop: 80 }}>
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10, paddingBottom: 14, borderBottom: "1px solid var(--line-soft)" }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.12em", color: sev.color, background: sev.bg, padding: "4px 7px", whiteSpace: "nowrap" }}>{sev.text}</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em", color: "var(--muted)", minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{where}</span>
        <span style={{ flex: 1, minWidth: 12 }} />
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.12em", color: "var(--muted)", whiteSpace: "nowrap" }}>{`ISSUE ${position} / ${total}`}</span>
        <span style={{ display: "flex", gap: 6 }}>
          <button type="button" className="btn-secondary" onClick={onPrev} disabled={position <= 1} aria-label="Previous issue" style={{ ...step, opacity: position <= 1 ? 0.4 : 1, cursor: position <= 1 ? "default" : "pointer" }}>↑</button>
          <button type="button" className="btn-secondary" onClick={onNext} disabled={position >= total} aria-label="Next issue" style={{ ...step, opacity: position >= total ? 0.4 : 1, cursor: position >= total ? "default" : "pointer" }}>↓</button>
        </span>
      </div>
      <span style={{ fontSize: 24, lineHeight: 1.35, letterSpacing: "-0.01em", maxWidth: 640, textWrap: "pretty" }}>{f.description}</span>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 20, alignItems: "stretch" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 12, border: "1px solid rgba(20,20,20,0.14)", background: "#FAF7F2", padding: 14, minWidth: 0 }}>
          <div style={{ background: "linear-gradient(150deg, #FFD9CF, #F3E9D2)", border: "1px solid rgba(20,20,20,0.08)", height: 84, overflow: "hidden" }}>
            <AsciiImage seed={q?.source_id ?? "evidence"} cols={110} rows={13} fontSize={7} style={{ background: "transparent", padding: 6, lineHeight: "8px", color: "rgba(20,20,20,0.42)" }} /></div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em", color: "var(--muted)", textTransform: "uppercase" }}>{q ? `${sourceName(sources, q.source_id)} · ${q.date}` : "NO CUSTOMER QUOTE · AGENT-READINESS FLAG"}</span>
          {q && <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, lineHeight: 1.6, color: "#141414" }}>"{q.text}"</span>}
          {q?.url && <a href={q.url} target="_blank" rel="noreferrer" style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em", color: "var(--scan-ink)" }}>READ THE REVIEW ↗</a>}
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12, border: "1px solid rgba(20,20,20,0.14)", background: "#FAF7F2", padding: 14, minWidth: 0 }}>
          <div style={{ border: "1px solid rgba(20,20,20,0.12)", display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "6px 8px", borderBottom: "1px solid rgba(20,20,20,0.1)" }}>
              {[0, 1].map(i => <span key={i} style={{ width: 5, height: 5, background: "rgba(20,20,20,0.22)", display: "block" }} />)}
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{url}</span></div>
            <div style={{ position: "relative", height: 150, background: "linear-gradient(150deg, #F3E9D2, #FFD9CF)", overflow: "hidden" }}>
              <AsciiImage seed={f.session_id ?? f.id} cols={110} rows={22} fontSize={7} style={{ background: "transparent", padding: 6, lineHeight: "8px", color: "rgba(20,20,20,0.42)" }} />
              <span style={{ position: "absolute", left: "46%", top: "58%", width: 34, height: 20, border: "1px solid rgba(20,20,20,0.45)", background: "rgba(250,247,242,0.9)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-mono)", fontSize: 8, color: "#141414" }}>OK
                <Reticle layoutId={`replay-${f.id}`} size={9} thickness={2} inset={-7} /></span>
            </div>
          </div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.12em", color: "var(--scan-ink)" }}>{`STEP ${f.step_index ?? "–"} · ${mmss(f.replay_offset_s)}`}</span>
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 14, border: "1px solid rgba(18,122,62,0.4)", background: "rgba(31,157,85,0.07)", padding: 18 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 500, letterSpacing: "0.16em", color: "var(--ok-ink)" }}>PROPOSED FIX</span>
        <span style={{ fontSize: 15, lineHeight: 1.6, color: "#141414", maxWidth: 640, textWrap: "pretty" }}>{f.proposed_fix}</span>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          <a href={f.replay_url ?? "#"} target="_blank" rel="noreferrer" className="btn-primary" style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 500, letterSpacing: "0.12em", color: "#FFFFFF", background: "var(--scan-deep)", border: "none", padding: "13px 22px", whiteSpace: "nowrap" }}>OPEN REPLAY ↗</a>
          <button onClick={() => navigator.clipboard?.writeText(f.proposed_fix)} className="btn-secondary" style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 500, letterSpacing: "0.12em", color: "#141414", background: "transparent", border: "1px solid rgba(20,20,20,0.3)", padding: "13px 22px", cursor: "pointer", whiteSpace: "nowrap" }}>COPY FIX</button>
        </div>
      </div>
    </div>);
}
