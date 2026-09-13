import { motion } from "motion/react";
import { AsciiImage } from "../../texture/AsciiImage";
import { Reticle } from "../../primitives/Reticle";
import type { Quote, Source } from "../../types";
const GRAD: Record<number, string> = { 1: "linear-gradient(140deg, #FFD9CF, #F3E9D2)", 2: "linear-gradient(140deg, #E5DDF5, #D8ECE3)", 3: "linear-gradient(140deg, #D8ECE3, #FFD9CF)", 4: "linear-gradient(140deg, #F3E9D2, #E5DDF5)" };
export function SourceCard({ source, quotes, focused, index }: { source: Source; quotes: Quote[] | undefined; focused: boolean; index: number }) {
  return (
    <motion.div layout initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.15, duration: 0.35 }} style={{ position: "relative", display: "flex", flexDirection: "column", gap: 7, minWidth: 0 }}>
      <div style={{ position: "relative", aspectRatio: "4 / 3", background: GRAD[((index % 4) + 1)], border: "1px solid rgba(20,20,20,0.12)", overflow: "hidden" }}>
        <AsciiImage src={source.thumbnail} seed={source.id} cols={28} rows={8} fontSize={7} style={{ background: "transparent", padding: 5, color: quotes ? "rgba(20,20,20,0.45)" : "rgba(20,20,20,0.4)", lineHeight: "7px" }} />
        {focused && <Reticle layoutId="research-reticle" size={11} thickness={2} inset={5} />}
      </div>
      <span className="mono" style={{ fontSize: 10, letterSpacing: "0.08em", lineHeight: 1.4, color: focused ? "#FF5A1F" : "#141414", textTransform: "uppercase" }}>{source.name}</span>
      {quotes?.slice(0, 1).map(q => (
        <motion.div key={q.text} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} style={{ display: "flex", gap: 6, background: "rgba(255,90,31,0.1)", padding: "6px 7px" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "#FF5A1F", flexShrink: 0 }}>&gt;</span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, lineHeight: 1.45, color: "#141414" }}>{q.text}</span>
        </motion.div>))}
    </motion.div>);
}
