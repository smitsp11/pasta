import { useEffect } from "react";
import { AsciiImage } from "../../texture/AsciiImage";
import { Reticle } from "../../primitives/Reticle";
import type { Feed, Finding, Persona } from "../../types";

const mmss = (s: number | null) => { const n = Math.max(0, Math.round(s ?? 0)); return `${String(Math.floor(n / 60)).padStart(2, "0")}:${String(n % 60).padStart(2, "0")}`; };

/** In-page session replay frozen at the stall step: the frame, the reticle on the offending element, and the step log. */
export function ReplayModal({ f, feed, persona, onClose }: { f: Finding; feed: Feed | undefined; persona: Persona | undefined; onClose: () => void }) {
  useEffect(() => { const k = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); }; window.addEventListener("keydown", k); return () => window.removeEventListener("keydown", k); }, [onClose]);
  const events = feed?.events ?? [];
  const stallStep = f.step_index ?? events[events.length - 1]?.step ?? 0;
  const url = (events.find(e => e.step === stallStep)?.observation ?? feed?.last_observation ?? f.replay_url ?? "").replace(/^https?:\/\//, "");
  const chips = persona ? [persona.config.device, persona.config.country, persona.config.identity === "fresh" ? "new" : "returning"] : [];
  return (
    <div role="dialog" aria-modal="true" aria-label="Session replay" onClick={onClose}
      style={{ position: "fixed", inset: 0, zIndex: 20, background: "rgba(20,20,20,0.55)", display: "flex", alignItems: "center", justifyContent: "center", padding: 32 }}>
      <div onClick={e => e.stopPropagation()} style={{ width: "min(1100px, 100%)", maxHeight: "100%", overflow: "auto", background: "#FAF7F2", border: "1px solid rgba(20,20,20,0.2)", display: "grid", gridTemplateColumns: "minmax(0, 2fr) minmax(260px, 1fr)", gap: 0 }}>
        <div style={{ display: "flex", flexDirection: "column", borderRight: "1px solid rgba(20,20,20,0.12)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 14px", borderBottom: "1px solid rgba(20,20,20,0.1)" }}>
            {[0, 1, 2].map(i => <span key={i} style={{ width: 6, height: 6, background: "rgba(20,20,20,0.22)", display: "block" }} />)}
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "#8A8580", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{url}</span>
            <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.12em", color: "#D93025", border: "1px solid #D93025", padding: "2px 6px" }}>STALLED</span>
          </div>
          <div style={{ position: "relative", aspectRatio: "16 / 10", background: "linear-gradient(150deg, #F3E9D2, #FFD9CF)", overflow: "hidden" }}>
            <AsciiImage seed={f.session_id ?? f.id} cols={140} rows={44} fontSize={9} style={{ background: "transparent", padding: 10, lineHeight: "11px", color: "rgba(20,20,20,0.42)" }} />
            <span style={{ position: "absolute", left: "46%", top: "58%", width: 62, height: 34, border: "1px solid rgba(20,20,20,0.45)", background: "rgba(250,247,242,0.9)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-mono)", fontSize: 11, color: "#141414" }}>OK
              <Reticle layoutId={`replay-modal-${f.id}`} size={12} thickness={2} inset={-9} /></span>
            <span style={{ position: "absolute", left: 12, bottom: 10, fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.12em", color: "#FF5A1F", background: "rgba(250,247,242,0.9)", padding: "4px 8px" }}>{`STEP ${stallStep || "–"} · ${mmss(f.replay_offset_s)}${f.session_id ? ` · ${f.session_id}` : ""}`}</span>
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 14, padding: 18, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 10 }}>
            <span style={{ fontSize: 16, lineHeight: 1.25 }}>{persona?.segment ?? f.journey_id}</span>
            <button onClick={onClose} aria-label="Close replay" style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.1em", color: "#141414", background: "transparent", border: "1px solid rgba(20,20,20,0.3)", padding: "4px 8px", cursor: "pointer" }}>CLOSE</button>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>{chips.map(c => <span key={c} style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", textTransform: "uppercase", border: "1px solid rgba(20,20,20,0.18)", padding: "2px 5px" }}>{c}</span>)}</div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.14em", color: "#8A8580" }}>AGENT TRACE</span>
          <ol style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
            {events.map(e => { const stall = e.step === stallStep; return (
              <li key={e.step} style={{ display: "grid", gridTemplateColumns: "28px 1fr", gap: 8, padding: "6px 8px", background: stall ? "rgba(217,48,37,0.08)" : "transparent", borderLeft: `2px solid ${stall ? "#D93025" : "rgba(20,20,20,0.12)"}` }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: stall ? "#D93025" : "#8A8580" }}>{String(e.step).padStart(2, "0")}</span>
                <span style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, lineHeight: 1.45, color: "#141414" }}>{e.action}</span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "#8A8580", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{e.observation.replace(/^https?:\/\//, "")}</span>
                </span></li>); })}
            {events.length === 0 && <li style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "#8A8580" }}>No trace recorded for this session.</li>}
          </ol>
          <span style={{ fontSize: 13, lineHeight: 1.5, color: "#141414", marginTop: "auto" }}>{f.description}</span>
        </div>
      </div>
    </div>);
}
