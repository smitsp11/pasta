import { Serif } from "../primitives/Serif";
import { TextScramble } from "../primitives/TextScramble";
import type { Persona, Source, StressTest } from "../types";
import { PersonaCard } from "./brief/PersonaCard";
import { StressTable } from "./brief/StressTable";
import { WorldDots } from "./brief/WorldDots";
function pairAxis(a: Persona, b: Persona): "device" | "identity" | "country" | null {
  return a.config.device !== b.config.device ? "device" : a.config.identity !== b.config.identity ? "identity" : a.config.country !== b.config.country ? "country" : null;
}
export function Brief({ personas, stressTests, sources }: { personas: Persona[]; stressTests: StressTest[]; sources: Source[] }) {
  const byId = Object.fromEntries(personas.map(p => [p.id, p]));
  const rendered = new Set<string>();
  const items: React.ReactNode[] = [];
  personas.forEach((p, i) => {
    if (rendered.has(p.id)) return;
    const mate = p.pair_id ? byId[p.pair_id] : null;
    if (mate) {
      const axis = pairAxis(p, mate); rendered.add(p.id); rendered.add(mate.id);
      items.push(
        <div key={p.id + mate.id} className="span-2" style={{ position: "relative", gridColumn: "span 2", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, minWidth: 0 }}>
          <PersonaCard p={p} pairAxis={axis} index={i} sources={sources} /><PersonaCard p={mate} pairAxis={axis} index={i + 1} sources={sources} />
          <span style={{ position: "absolute", left: "50%", top: 58, transform: "translateX(-50%)", width: 40, height: 1, background: "var(--scan)", pointerEvents: "none" }} />
          <span style={{ position: "absolute", left: "50%", top: 66, transform: "translateX(-50%)", fontFamily: "var(--font-mono)", fontSize: 8, letterSpacing: "0.12em", color: "var(--scan-ink)", background: "#FAF7F2", border: "1px solid #FF5A1F", padding: "3px 6px", whiteSpace: "nowrap", pointerEvents: "none" }}>MATCHED PAIR · {axis?.toUpperCase()}</span>
        </div>);
    } else { rendered.add(p.id); items.push(<PersonaCard key={p.id} p={p} pairAxis={null} index={i} sources={sources} />); }
  });
  return (
    <section className="pad-x" style={{ display: "flex", flexDirection: "column", gap: 44, padding: "44px 32px 72px", maxWidth: 1400, width: "100%", boxSizing: "border-box", margin: "0 auto" }}>
      <Serif size="clamp(38px, 4.6vw, 68px)" style={{ maxWidth: 900, lineHeight: 0.98 }}><TextScramble duration={0.9}>Here's who we'll send.</TextScramble></Serif>
      <WorldDots personas={personas} />
      <div className="card-grid">{items}</div>
      <StressTable rows={stressTests} />
    </section>);
}
