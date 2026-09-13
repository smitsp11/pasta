import { motion } from "motion/react";
import type { Persona } from "../../types";
const PIN: Record<string, { left: string; top: string; above?: boolean }[]> = {
  US: [{ left: "16%", top: "27.6%" }, { left: "22.9%", top: "33.1%" }, { left: "25.7%", top: "24.5%" }, { left: "29.4%", top: "25.4%" }],
  CA: [{ left: "15.8%", top: "19%", above: true }, { left: "27.9%", top: "23.2%", above: true }],
  GB: [{ left: "50%", top: "17.4%", above: true }], DE: [{ left: "53.7%", top: "16.7%" }],
};
export function WorldDots({ personas }: { personas: Persona[] }) {
  const used: Record<string, number> = {};
  const pins = personas.map(p => { const i = used[p.config.country] ?? 0; used[p.config.country] = i + 1; const slots = PIN[p.config.country] ?? PIN.US; return { id: p.id, country: p.config.country, ...slots[i % slots.length] }; });
  return (
    <div style={{ position: "relative", width: "fit-content", maxWidth: "100%", margin: "0 auto" }}>
      <img src="/assets/world-dots.png" alt="" style={{ display: "block", height: "33vh", width: "auto", maxWidth: "100%", opacity: 0.9 }} />
      {pins.map((p, i) => (
        <motion.span key={p.id} initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.3, duration: 0.3 }}
          style={{ position: "absolute", left: p.left, top: p.top, transform: "translate(-50%, -50%)", display: "flex", flexDirection: p.above ? "column-reverse" : "column", alignItems: "center", gap: 3 }}>
          <span style={{ width: 9, height: 9, background: "var(--scan)", borderRadius: "50%", display: "block", animation: `irisBlip 2s ease-in-out ${i * 0.15}s infinite` }} />
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", color: "var(--scan-ink)" }}>{p.country}</span>
        </motion.span>))}
    </div>);
}
