import { motion } from "motion/react";
import { AsciiImage } from "../../texture/AsciiImage";
import { PixelDissolve } from "../../primitives/PixelDissolve";
import { Reticle } from "../../primitives/Reticle";
import type { Feed, Persona } from "../../types";
const GRAD: Record<number, string> = { 1: "linear-gradient(150deg, #FFD9CF, #F3E9D2)", 2: "linear-gradient(150deg, #F3E9D2, #FFD9CF)", 3: "linear-gradient(150deg, #E5DDF5, #D8ECE3)", 4: "linear-gradient(150deg, #D8ECE3, #E5DDF5)" };
const SHELL: Record<Feed["status"], React.CSSProperties> = {
  running: { border: "1px solid rgba(20,20,20,0.14)", background: "#FAF7F2" }, completed: { border: "1px solid rgba(31,157,85,0.5)", background: "#FAF7F2" },
  stalled: { border: "1px solid rgba(217,48,37,0.5)", background: "#FAF7F2" }, harness_error: { border: "1px solid rgba(20,20,20,0.12)", background: "rgba(20,20,20,0.02)" } };
const MARK: Record<Feed["status"], string> = { running: "var(--scan-ink)", completed: "var(--ok-ink)", stalled: "var(--stall-ink)", harness_error: "var(--muted)" };
const pill = (status: Feed["status"]): React.CSSProperties => ({ display: "flex", alignItems: "center", gap: status === "completed" ? 4 : 5, fontFamily: "var(--font-mono)", fontSize: 8, letterSpacing: "0.1em", padding: "3px 5px", whiteSpace: "nowrap", flexShrink: 0,
  color: MARK[status], border: `1px solid ${status === "harness_error" ? "rgba(20,20,20,0.2)" : MARK[status]}` });
const LABEL: Record<Feed["status"], string> = { running: "RUNNING", completed: "✓ DONE", stalled: "STALLED", harness_error: "ERROR" };
export function FeedCard({ feed, persona, focused, index, scanSeconds }: { feed: Feed; persona: Persona | undefined; focused: boolean; index: number; scanSeconds: number }) {
  const err = feed.status === "harness_error"; const muted = err ? "var(--muted)" : "#141414";
  const url = (feed.last_observation || "").replace(/^https?:\/\//, "") || "connecting…";
  const chips = persona ? [persona.config.device, persona.config.country, persona.config.identity === "fresh" ? "new" : "returning"] : [];
  return (
    <motion.div layout initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.08, duration: 0.3 }}
      style={{ position: "relative", display: "flex", flexDirection: "column", gap: 9, padding: 12, minWidth: 0, ...SHELL[feed.status] }}>
      {focused && <Reticle layoutId="swarm-reticle" size={13} thickness={2} inset={-5} />}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8 }}>
        <span style={{ fontSize: 14, lineHeight: 1.25, letterSpacing: "-0.005em", color: muted }}>{persona?.segment ?? feed.run_id}</span>
        <span style={pill(feed.status)}>{feed.status === "running" && <span style={{ width: 4, height: 4, background: "var(--scan)", borderRadius: "50%", display: "block", animation: "irisPulse 1.4s ease-in-out infinite" }} />}{LABEL[feed.status]}</span>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>{chips.map(c => <span key={c} style={{ fontFamily: "var(--font-mono)", fontSize: 8, letterSpacing: "0.1em", textTransform: "uppercase", color: muted, border: `1px solid rgba(20,20,20,${err ? 0.14 : 0.18})`, padding: "2px 5px" }}>{c}</span>)}</div>
      <div style={{ flex: "none", aspectRatio: "16 / 10", border: `1px solid ${feed.status === "stalled" ? "rgba(217,48,37,0.3)" : feed.status === "completed" ? "rgba(31,157,85,0.3)" : err ? "rgba(20,20,20,0.1)" : "rgba(20,20,20,0.12)"}`, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 5, padding: "5px 7px", borderBottom: `1px solid rgba(20,20,20,${err ? 0.08 : 0.1})` }}>
          {[0, 1].map(i => <span key={i} style={{ width: 4, height: 4, background: `rgba(20,20,20,${err ? 0.16 : 0.22})`, display: "block" }} />)}
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 8, color: "var(--muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{url}</span>
        </div>
        {err ? (
          <div style={{ flex: 1, background: "rgba(20,20,20,0.06)", display: "flex", alignItems: "center", justifyContent: "center", padding: 8 }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.12em", color: "var(--muted)", textAlign: "center" }}>TOOLING ERROR · EXCLUDED</span></div>
        ) : (
          <PixelDissolve trigger={feed.status} style={{ flex: 1, position: "relative", background: GRAD[persona?.pastel ?? 1], overflow: "hidden" }}>
            <AsciiImage seed={feed.run_id + feed.step} cols={60} rows={28} fontSize={7} style={{ background: "transparent", padding: 6, lineHeight: "8px", color: "rgba(20,20,20,0.44)" }} />
            {feed.status === "running" && <span aria-hidden style={{ position: "absolute", left: 0, right: 0, height: 1, background: "var(--scan)", boxShadow: "0 0 8px rgba(255,90,31,0.5)", animation: `irisScan ${scanSeconds}s linear infinite` }} />}
            {feed.status === "stalled" && <span style={{ position: "absolute", inset: 0, background: "rgba(217,48,37,0.22)", display: "flex", alignItems: "center", justifyContent: "center" }}><span style={{ fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 500, letterSpacing: "0.16em", color: "#FFFFFF", background: "var(--stall-ink)", padding: "5px 9px" }}>STALLED</span></span>}
            {feed.status === "completed" && <span style={{ position: "absolute", inset: 0, background: "rgba(31,157,85,0.22)", display: "flex", alignItems: "center", justifyContent: "center" }}><span style={{ width: 44, height: 44, borderRadius: "50%", background: "var(--ok-ink)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 26, lineHeight: 1, color: "#FFFFFF" }}>✓</span></span>}
          </PixelDissolve>)}
      </div>
      <div style={{ display: "flex", gap: 5 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: MARK[feed.status], flexShrink: 0 }}>&gt;</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, lineHeight: 1.45, color: muted }}>{feed.last_action}</span>
      </div>
    </motion.div>);
}
