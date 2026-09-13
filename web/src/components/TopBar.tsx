import { LogoReticle } from "../primitives/Reticle";
import type { StageName } from "../types";
const STEPS: { key: StageName | "brief"; label: string }[] = [{ key: "explore", label: "LEARN" }, { key: "brief", label: "BRIEF" }, { key: "run", label: "SWARM" }, { key: "score", label: "FINDINGS" }, { key: "done", label: "REPORT" }];
const ORDER = ["explore", "brief", "run", "score", "done"];
/** `brief` is a UI-only stage between explore and run: it is "current" once personas exist and the run stage has not started. */
export function TopBar({ stage, sessions, cached = false, hasBrief = false }: { stage: StageName | "idle"; sessions: number; cached?: boolean; hasBrief?: boolean }) {
  const current = stage === "explore" && hasBrief ? "brief" : stage;
  const idx = ORDER.indexOf(current as string);
  return (
    <div style={{ position: "sticky", top: 0, zIndex: 5, backdropFilter: "blur(2px)", borderBottom: "1px solid rgba(20,20,20,0.1)", background: "rgba(250,247,242,0.7)" }}>
      <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", alignItems: "center", gap: 20, padding: "0 28px", minHeight: 64 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}><LogoReticle /><span className="serif" style={{ fontSize: 30, lineHeight: 1 }}>Iris</span></div>
        <div className="mono" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 2, fontSize: 11, fontWeight: 500 }}>
          {STEPS.map((s, i) => {
            const state = idx < 0 ? "up" : i < idx ? "done" : i === idx ? "cur" : "up";
            const dot = state === "cur" && stage !== "done";
            return (<span key={s.key} style={{ display: "contents" }}>
              {i > 0 && <span style={{ color: "rgba(20,20,20,0.22)" }}>·</span>}
              <span style={{ display: "flex", alignItems: "center", gap: 6, padding: state === "cur" ? "6px 9px" : "6px 6px", whiteSpace: "nowrap",
                color: state === "done" ? "#141414" : state === "cur" ? "#FF5A1F" : "#8A8580", background: state === "cur" ? "rgba(255,90,31,0.08)" : "transparent" }}>
                {state === "done" && <span style={{ color: "#1F9D55" }}>✓</span>}
                {dot && <span style={{ width: 5, height: 5, background: "#FF5A1F", borderRadius: "50%", display: "block", animation: "irisPulse 1.4s ease-in-out infinite" }} />}
                {s.label}</span></span>);
          })}
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 10 }}>
          {cached && <span className="mono" style={{ fontSize: 12, fontWeight: 500, letterSpacing: "0.12em", color: "#8A8580", background: "rgba(20,20,20,0.06)", padding: "6px 10px", borderRadius: 999, whiteSpace: "nowrap" }}>[ CACHED ]</span>}
          <span className="mono" style={{ fontSize: 12, fontWeight: 500, letterSpacing: "0.12em", color: "#141414", border: "1px solid rgba(20,20,20,0.18)", padding: "6px 10px", whiteSpace: "nowrap" }}>{`[ ${sessions} SESSION${sessions === 1 ? "" : "S"} ]`}</span>
        </div>
      </div>
    </div>);
}
