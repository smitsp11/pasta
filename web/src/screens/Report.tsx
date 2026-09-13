import { useMemo, useState } from "react";
import { NumberTick } from "../primitives/NumberTick";
import { Serif } from "../primitives/Serif";
import { TextScramble } from "../primitives/TextScramble";
import type { Feed, Finding, Persona, ResultItem, ScoreCard, Source } from "../types";
import { FlagDetail } from "./report/FlagDetail";
import { FlagRow } from "./report/FlagRow";
export function Report({ scorecard, findings, affected, personas, feeds = {}, sources = [], instant = false }: { scorecard: ScoreCard; findings: Finding[]; affected: ResultItem["affected"]; personas: Persona[]; feeds?: Record<string, Feed>; sources?: Source[]; instant?: boolean }) {
  const ranked = useMemo(() => [...findings].sort((a, b) => (affected[b.id]?.share ?? 0) - (affected[a.id]?.share ?? 0)), [findings, affected]);
  const [sel, setSel] = useState<string | undefined>(undefined);
  const f = ranked.find(x => x.id === sel) ?? ranked[0];
  const byId = Object.fromEntries(personas.map(p => [p.id, p]));
  const bySession: Record<string, Persona> = {};
  for (const f of Object.values(feeds)) { const p = byId[f.persona_id]; if (p) bySession[f.session_id] = p; }
  for (const p of personas) bySession[`sess-${p.run_id}`] ??= p;   // fixture convention when no feeds were streamed
  const excluded = scorecard.per_journey.reduce((a, j) => a + j.harness_errors, 0);
  const agents = personas.length; const journeys = scorecard.per_journey.length;
  const num: React.CSSProperties = { fontFamily: "var(--font-mono)", fontSize: "clamp(72px, 10vw, 132px)", lineHeight: 0.86, letterSpacing: "-0.04em" };
  const cap: React.CSSProperties = { fontFamily: "var(--font-mono)", fontSize: 11, lineHeight: 1.6, letterSpacing: "0.12em" };
  return (
    <section style={{ display: "flex", flexDirection: "column", gap: 44, padding: "48px 32px 72px", maxWidth: 1400, width: "100%", boxSizing: "border-box", margin: "0 auto" }}>
      <Serif size="clamp(38px, 4.6vw, 68px)" style={{ maxWidth: 900, lineHeight: 0.98 }}><TextScramble duration={0.9}>What broke, for whom, and why.</TextScramble></Serif>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 28, borderTop: "1px solid rgba(20,20,20,0.16)", borderBottom: "1px solid rgba(20,20,20,0.16)", padding: "26px 0" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, minWidth: 0 }}>
            <span style={{ ...num, color: "#8A8580" }}>{scorecard.static_score == null ? "—" : <NumberTick value={scorecard.static_score} instant={instant} duration={1.0} />}</span>
            <span style={{ ...cap, color: "#8A8580" }}>{scorecard.static_score == null ? "CLOUDFLARE STATIC SCORE · scanner blocked by the site" : "CLOUDFLARE STATIC SCORE · robots.txt, llms.txt, headers"}</span></div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, minWidth: 0 }}>
            <span style={{ ...num, color: "#FF5A1F" }}><NumberTick value={scorecard.overall} instant={instant} duration={1.2} /></span>
            <span style={{ ...cap, color: "#141414" }}>{`IRIS MEASURED · ${agents} real agents, ${journeys} journeys`}</span></div>
        </div>
        {excluded > 0 && <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.14em", color: "#8A8580" }}>{`${excluded} RUN${excluded === 1 ? "" : "S"} EXCLUDED · TOOLING ERROR`}</span>}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 1fr) minmax(0, 2fr)", gap: 40, alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", minWidth: 0, borderTop: "1px solid rgba(20,20,20,0.14)" }}>
          {ranked.map(x => <FlagRow key={x.id} f={x} selected={x.id === f?.id} share={affected[x.id]?.share ?? 0} people={(affected[x.id]?.persona_ids ?? []).map(id => byId[id]).filter(Boolean)} onSelect={() => setSel(x.id)} />)}
        </div>
        {f && <FlagDetail f={f} persona={f.session_id ? bySession[f.session_id] : undefined} sources={sources} feed={Object.values(feeds).find(x => x.session_id === f.session_id)} />}
      </div>
    </section>);
}
