import { motion } from "motion/react";
import { AsciiImage } from "../../texture/AsciiImage";
import type { SiteNode } from "../../types";
import { edgePath, layoutNodes } from "./layout";
const short = (path: string) => { const segs = path.split("?")[0].replace(/\/$/, "").split("/").filter(Boolean); return segs.length === 0 ? "/" : segs.length === 1 ? `/${segs[0]}` : `…/${segs[segs.length - 1].slice(0, 28)}`; };
export function SiteMap({ url, nodes, scanning }: { url: string; nodes: SiteNode[]; scanning: boolean }) {
  const pos = layoutNodes(nodes);
  const host = url.replace(/^https?:\/\//, "").replace(/\/$/, "");
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16, alignItems: "stretch" }}>
      <div style={{ border: "1px solid rgba(20,20,20,0.14)", background: "#FAF7F2", display: "flex", flexDirection: "column", minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 10px", borderBottom: "1px solid rgba(20,20,20,0.12)" }}>
          <span style={{ display: "flex", gap: 4 }}>{[0, 1, 2].map(i => <span key={i} style={{ width: 6, height: 6, background: "rgba(20,20,20,0.22)", display: "block" }} />)}</span>
          <span className="mono" style={{ fontSize: 9, letterSpacing: "0.06em", color: "#8A8580", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", textTransform: "none" }}>{host}</span>
        </div>
        <div style={{ position: "relative", flex: 1, minHeight: 210, background: "linear-gradient(160deg, #F3E9D2, #FFD9CF)", overflow: "hidden" }}>
          <AsciiImage seed={host} cols={110} rows={30} fontSize={7} style={{ background: "transparent", padding: 8, lineHeight: "8.6px", letterSpacing: "0.02em", color: "rgba(20,20,20,0.42)" }} />
          <span aria-hidden style={{ position: "absolute", left: 0, right: 0, height: 2, background: "#FF5A1F", boxShadow: "0 0 10px rgba(255,90,31,0.55)", top: scanning ? undefined : "74%", animation: scanning ? "irisScanPanel 2.8s linear infinite" : "none" }} />
        </div>
      </div>
      <div style={{ position: "relative", minHeight: 250, minWidth: 0, padding: 8, boxSizing: "border-box", border: "1px solid rgba(20,20,20,0.1)" }}>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
          {nodes.filter(n => n.parent && pos[n.parent]).map(n => (
            <motion.path key={n.path} d={edgePath(pos[n.parent!], pos[n.path])} fill="none" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.3 }}
              stroke={n.journey ? "#FF5A1F" : "#141414"} strokeWidth={n.journey ? 0.45 : 0.35} opacity={n.journey ? 0.9 : 0.5} vectorEffect="non-scaling-stroke" />))}
        </svg>
        {nodes.map(n => (
          <motion.span key={n.path} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.2 }}
            style={{ position: "absolute", left: `${pos[n.path].x}%`, top: `${pos[n.path].y}%`, transform: "translate(-50%, -50%)", display: "flex", alignItems: "center", gap: 7, fontFamily: "var(--font-mono)", fontSize: 10,
              color: n.journey ? "#FF5A1F" : "#141414", background: "#FAF7F2", border: `1px solid ${n.journey ? "#FF5A1F" : "rgba(20,20,20,0.2)"}`, padding: "4px 7px", whiteSpace: "nowrap" }}>
            <span title={n.path}>{short(n.path)}</span>{n.journey && <span style={{ fontSize: 8, letterSpacing: "0.1em", color: "#FF5A1F", opacity: 0.85 }}>JOURNEY {n.journey}</span>}
          </motion.span>))}
      </div>
    </div>);
}
