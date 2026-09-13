import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { NumberTick } from "../primitives/NumberTick";
import { Serif } from "../primitives/Serif";
import { TextScramble } from "../primitives/TextScramble";
import type { Feed, Finding, Journey, Persona, ResultItem, ScoreCard, Source } from "../types";
import { FlagDetail } from "./report/FlagDetail";
import { FlagRow } from "./report/FlagRow";
const rank = (f: Finding) => f.attributed_to === "site" ? 0 : 1;
export function Report({ scorecard, findings, affected, personas, feeds = {}, sources = [], journeys: journeyList = [], instant = false }: { scorecard: ScoreCard; findings: Finding[]; affected: ResultItem["affected"]; personas: Persona[]; feeds?: Record<string, Feed>; sources?: Source[]; journeys?: Journey[]; instant?: boolean }) {
  const ranked = useMemo(() => [...findings].sort((a, b) => rank(a) - rank(b) || (affected[b.id]?.share ?? 0) - (affected[a.id]?.share ?? 0)), [findings, affected]);
  const [sel, setSel] = useState<string | undefined>(undefined);
  const at = Math.max(0, ranked.findIndex(x => x.id === sel));
  const f = ranked[at];
  const rows = useRef<Record<string, HTMLDivElement | null>>({});
  const detail = useRef<HTMLDivElement>(null);
  const journeyName = Object.fromEntries(journeyList.map(j => [j.id, j.name]));
  const where = (x: Finding) => `${(journeyName[x.journey_id] ?? x.journey_id.replace(/_/g, " ")).toUpperCase()}${x.step_index == null ? "" : ` · STEP ${x.step_index}`}`;
  const viaKey = useRef(false);
  // Resolve against the pending id, not `at`: two keydowns can land before a re-render.
  const go = useCallback((move: (i: number) => number) => {
    viaKey.current = true;
    setSel(prev => {
      const from = Math.max(0, ranked.findIndex(x => x.id === prev));
      return ranked[Math.min(ranked.length - 1, Math.max(0, move(from)))]?.id ?? prev;
    });
  }, [ranked]);
  useEffect(() => { if (viaKey.current) { viaKey.current = false; rows.current[f?.id ?? ""]?.focus({ preventScroll: true }); } }, [f?.id]);
  const onKeyDown = (e: React.KeyboardEvent) => {
    const k = e.key;
    if (k === "ArrowDown" || k === "j") go(i => i + 1);
    else if (k === "ArrowUp" || k === "k") go(i => i - 1);
    else if (k === "Home") go(() => 0);
    else if (k === "End") go(() => ranked.length - 1);
    else if (k === "Enter") { detail.current?.focus(); detail.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }); }
    else return;
    e.preventDefault();
  };
  const byId = Object.fromEntries(personas.map(p => [p.id, p]));
  const bySession: Record<string, Persona> = {};
  for (const f of Object.values(feeds)) { const p = byId[f.persona_id]; if (p) bySession[f.session_id] = p; }
  for (const p of personas) bySession[`sess-${p.run_id}`] ??= p;   // fixture convention when no feeds were streamed
  const excluded = scorecard.per_journey.reduce((a, j) => a + j.harness_errors, 0);
  const agents = personas.length; const journeys = scorecard.per_journey.length;
  const num: React.CSSProperties = { fontFamily: "var(--font-mono)", fontSize: "clamp(72px, 10vw, 132px)", lineHeight: 0.86, letterSpacing: "-0.04em" };
  const cap: React.CSSProperties = { fontFamily: "var(--font-mono)", fontSize: 11, lineHeight: 1.6, letterSpacing: "0.12em" };
  return (
    <section className="pad-x" style={{ display: "flex", flexDirection: "column", gap: 44, padding: "48px 32px 72px", maxWidth: 1400, width: "100%", boxSizing: "border-box", margin: "0 auto" }}>
      <Serif size="clamp(38px, 4.6vw, 68px)" style={{ maxWidth: 900, lineHeight: 0.98 }}><TextScramble duration={0.9}>What broke, for whom, and why.</TextScramble></Serif>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 28, borderTop: "1px solid rgba(20,20,20,0.16)", borderBottom: "1px solid rgba(20,20,20,0.16)", padding: "26px 0" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, minWidth: 0 }}>
            <span style={{ ...num, color: "var(--scan)" }}><NumberTick value={scorecard.overall} instant={instant} duration={1.2} /></span>
            <span style={{ ...cap, color: "#141414" }}>{`IRIS MEASURED · ${agents} real agents, ${journeys} journeys`}</span></div>
        </div>
        {excluded > 0 && <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.14em", color: "var(--muted)" }}>{`${excluded} RUN${excluded === 1 ? "" : "S"} EXCLUDED · TOOLING ERROR`}</span>}
      </div>
      <div className="report-grid">
        <div className="report-index" style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
          <div style={{ position: "sticky", top: 0, zIndex: 1, display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 10, padding: "0 0 9px", background: "var(--paper)", borderBottom: "1px solid rgba(20,20,20,0.14)" }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, fontWeight: 500, letterSpacing: "0.16em", color: "#141414" }}>{`${ranked.length} ISSUE${ranked.length === 1 ? "" : "S"}`}</span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.12em", color: "var(--muted)" }}>{`${at + 1} / ${ranked.length} · ↑↓ TO MOVE`}</span>
          </div>
          <div role="listbox" aria-label="Findings, most severe first" onKeyDown={onKeyDown} style={{ display: "flex", flexDirection: "column", outline: "none" }}>
            {ranked.map((x, i) => <FlagRow key={x.id} f={x} selected={x.id === f?.id} share={affected[x.id]?.share ?? 0} where={where(x)} position={i + 1} total={ranked.length}
              people={(affected[x.id]?.persona_ids ?? []).map(id => byId[id]).filter(Boolean)} onSelect={() => setSel(x.id)} rowRef={el => { rows.current[x.id] = el; }} />)}
          </div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em", color: "var(--muted)", padding: "10px 0 0" }}>SORTED BY SEVERITY · % = SHOPPERS AFFECTED</span>
        </div>
        {f && <FlagDetail ref={detail} f={f} position={at + 1} total={ranked.length} where={where(f)} persona={f.session_id ? bySession[f.session_id] : undefined} sources={sources}
          feed={Object.values(feeds).find(x => x.session_id === f.session_id)}
          onPrev={() => setSel(ranked[Math.max(0, at - 1)]?.id)} onNext={() => setSel(ranked[Math.min(ranked.length - 1, at + 1)]?.id)} />}
      </div>
    </section>);
}
