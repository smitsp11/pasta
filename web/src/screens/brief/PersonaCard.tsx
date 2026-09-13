import { motion } from "motion/react";
import { AsciiImage } from "../../texture/AsciiImage";
import type { Persona, Source } from "../../types";
const GRAD: Record<number, string> = { 1: "linear-gradient(150deg, #FFD9CF, #F3E9D2)", 2: "linear-gradient(150deg, #F3E9D2, #FFD9CF)", 3: "linear-gradient(150deg, #E5DDF5, #D8ECE3)", 4: "linear-gradient(150deg, #D8ECE3, #E5DDF5)" };
const chip = (accent: boolean): React.CSSProperties => ({ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", padding: "3px 6px", textTransform: "uppercase", color: accent ? "var(--scan-ink)" : "#141414", border: `1px solid ${accent ? "var(--scan)" : "rgba(20,20,20,0.18)"}` });
export const chipsFor = (p: Persona) => [p.config.device, p.config.country, p.config.identity === "fresh" ? "new" : "returning"];
export function PersonaCard({ p, pairAxis, index, sources }: { p: Persona; pairAxis: "device" | "identity" | "country" | null; index: number; sources: Source[] }) {
  const [device, country, identity] = chipsFor(p);
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.1, duration: 0.3 }}
      style={{ display: "flex", flexDirection: "column", gap: 10, border: `1px solid ${pairAxis ? "var(--scan)" : "rgba(20,20,20,0.14)"}`, background: "#FAF7F2", padding: 12, minWidth: 0 }}>
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
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.06em", color: "var(--muted)" }}>— {sourceName(sources, p.evidence.source_id)}, {p.evidence.date}</span>
      </div>
    </motion.div>);
}
export const sourceName = (sources: Source[], id: string) => sources.find(s => s.id === id)?.name ?? id;
