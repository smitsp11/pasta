import { LogoReticle } from "../primitives/Reticle";
import type { StageName } from "../types";
type StepState = "done" | "cur" | "up";
const STEPS: { key: StageName | "brief"; label: string }[] = [{ key: "explore", label: "LEARN" }, { key: "brief", label: "BRIEF" }, { key: "run", label: "SWARM" }, { key: "score", label: "FINDINGS" }, { key: "done", label: "REPORT" }];
const ORDER = ["explore", "brief", "run", "score", "done"];
const DOT: React.CSSProperties = { width: 9, height: 9, borderRadius: "50%", boxSizing: "border-box", display: "block", flex: "0 0 auto" };
function Node({ state, live }: { state: StepState; live: boolean }) {
  if (state === "done") return <span style={{ ...DOT, background: "var(--ok-ink)" }} />;
  if (state !== "cur") return <span style={{ ...DOT, border: "1px solid var(--line)" }} />;
  return (
    <span style={{ ...DOT, position: "relative", border: "1.5px solid var(--scan)" }}>
      {live && <span className="pipe-halo" style={{ position: "absolute", inset: -1.5, borderRadius: "50%", background: "var(--scan)" }} />}
      <span className={live ? "pipe-core pipe-core--live" : "pipe-core"} style={{ position: "absolute", inset: 1.5, borderRadius: "50%", background: "var(--scan)" }} />
    </span>);
}
/** `brief` is a UI-only stage between explore and run: it is "current" once personas exist and the run stage has not started. */
export function TopBar({ stage, sessions, cached = false, hasBrief = false }: { stage: StageName | "idle"; sessions: number; cached?: boolean; hasBrief?: boolean }) {
  const current = stage === "explore" && hasBrief ? "brief" : stage;
  const idx = ORDER.indexOf(current as string);
  const running = idx >= 0 && stage !== "done";
  return (
    <div style={{ position: "sticky", top: 0, zIndex: 5, backdropFilter: "blur(2px)", borderBottom: "1px solid var(--line-soft)", background: "rgba(250,247,242,0.82)" }}>
      <div className="topbar-grid" style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", alignItems: "center", gap: 20, padding: "0 28px", minHeight: 64 }}>
        <div className="topbar-logo" style={{ display: "flex", alignItems: "center", gap: 10 }}><LogoReticle /><span className="serif" style={{ fontSize: 30, lineHeight: 1 }}>Iris</span></div>
        <nav aria-label="Pipeline" className="mono pipe topbar-pipe" style={{ fontSize: 11, fontWeight: 500 }}>
          {STEPS.map((s, i) => {
            const state: StepState = idx < 0 ? "up" : i < idx ? "done" : i === idx ? "cur" : "up";
            const settled = state === "done" || (state === "cur" && stage === "done");
            return (<span key={s.key} style={{ display: "contents" }}>
              {i > 0 && <span className="pipe-link" data-state={idx < 0 ? "up" : i <= idx ? "done" : i === idx + 1 && running ? "next" : "up"} />}
              <span className="pipe-step" data-cur={state === "cur" ? 1 : 0} aria-current={state === "cur" ? "step" : undefined}
                style={{ color: settled ? "var(--ink)" : state === "cur" ? "var(--scan-ink)" : "var(--muted)" }}>
                <Node state={settled ? "done" : state} live={state === "cur" && running} />
                <span className="pipe-label">{s.label}</span></span></span>);
          })}
        </nav>
        <div className="topbar-meta" style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 10 }}>
          {cached && <span className="mono" style={{ fontSize: 12, fontWeight: 500, letterSpacing: "0.12em", color: "var(--muted)", background: "rgba(20,20,20,0.06)", padding: "6px 10px", borderRadius: 999, whiteSpace: "nowrap" }}>[ CACHED ]</span>}
          <span className="mono" style={{ fontSize: 12, fontWeight: 500, letterSpacing: "0.12em", color: "var(--ink)", border: "1px solid var(--line)", padding: "6px 10px", whiteSpace: "nowrap" }}>{`[ ${sessions} SESSION${sessions === 1 ? "" : "S"} ]`}</span>
        </div>
      </div>
    </div>);
}
