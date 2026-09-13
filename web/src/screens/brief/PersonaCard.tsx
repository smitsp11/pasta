import { motion } from "motion/react";
import { AsciiImage } from "../../texture/AsciiImage";
import type { Persona } from "../../types";
const GRAD: Record<number, string> = { 1: "linear-gradient(150deg, #FFD9CF, #F3E9D2)", 2: "linear-gradient(150deg, #F3E9D2, #FFD9CF)", 3: "linear-gradient(150deg, #E5DDF5, #D8ECE3)", 4: "linear-gradient(150deg, #D8ECE3, #E5DDF5)" };
const chip = (accent: boolean): React.CSSProperties => ({ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", padding: "3px 6px", textTransform: "uppercase", color: accent ? "#FF5A1F" : "#141414", border: `1px solid ${accent ? "#FF5A1F" : "rgba(20,20,20,0.18)"}` });
export const chipsFor = (p: Persona) => [p.config.device, p.config.country, p.config.identity === "fresh" ? "new" : "returning"];
export function PersonaCard({ p, pairAxis, index }: { p: Persona; pairAxis: "device" | "identity" | "country" | null; index: number }) {
  const [device, country, identity] = chipsFor(p);
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.1, duration: 0.3 }}
      style={{ display: "flex", flexDirection: "column", gap: 10, border: `1px solid ${pairAxis ? "#FF5A1F" : "rgba(20,20,20,0.14)"}`, background: "#FAF7F2", padding: 12, minWidth: 0 }}>
      <div style={{ background: GRAD[p.pastel], border: "1px solid rgba(20,20,20,0.08)", overflow: "hidden" }}>
        <AsciiImage seed={p.segment + p.config.device} cols={24} rows={10} fontSize={8} style={{ background: "transparent", padding: 8, lineHeight: "8px", color: "rgba(20,20,20,0.5)" }} />
      </div>
      <span style={{ fontSize: 20, lineHeight: 1.2, letterSpacing: "-0.01em" }}>{p.segment}</span>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
        <span style={chip(pairAxis === "device")}>{device}</span><span style={chip(pairAxis === "country")}>{country}</span><span style={chip(pairAxis === "identity")}>{identity}</span>
      </div>
      <span style={{ fontSize: 13, lineHeight: 1.5, color: "#141414" }}>{p.goal}</span>
      <div style={{ background: "rgba(20,20,20,0.04)", padding: 8, display: "flex", flexDirection: "column", gap: 4 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, lineHeight: 1.5, color: "#141414" }}>"{p.evidence.text}"</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.06em", color: "#8A8580" }}>— {sourceName(p.evidence.source_id)}, {p.evidence.date}</span>
      </div>
    </motion.div>);
}
const NAMES: Record<string, string> = { trustpilot: "Trustpilot", google: "Google Reviews", reddit: "Reddit r/Outdoors", appstore: "App Store", help: "Help centre", competitor: "Arc'teryx", youtube: "YouTube", support: "Support tickets", instagram: "Instagram" };
export const sourceName = (id: string) => NAMES[id] ?? id;
