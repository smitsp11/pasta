import type { Finding, Persona } from "../../types";
const TITLE: Record<string, string> = { cookie_wall: "Cookie wall", icon_only_control: "Icon-only cart button", geo_block: "Geo-blocked pricing", hidden_nav: "Hidden mobile nav", captcha: "CAPTCHA wall", ambiguous_cta: "Ambiguous call to action", infinite_scroll: "Infinite scroll", login_wall: "Login wall", layout_shift: "Layout shift", timeout: "Timed out", other: "Other" };
export const flagTitle = (f: Finding) => TITLE[f.category] ?? f.category;
export const severity = (f: Finding) => f.attributed_to === "site" ? { text: "FAILS FOR EVERYONE", color: "var(--stall-ink)", bg: "rgba(190,35,24,0.09)" } : { text: `FAILS ONLY ON ${f.attributed_to === "device" ? f.config.device : f.attributed_to === "country" ? f.config.country : f.attributed_to === "identity" ? (f.config.identity === "returning" ? "RETURNING" : "NEW") : (f.config.engine === "browser_use" ? "DOM AGENTS" : "VISION AGENTS")}`.toUpperCase(), color: "var(--scan-ink)", bg: "rgba(201,63,6,0.10)" };
const GRAD: Record<number, string> = { 1: "linear-gradient(150deg, #FFD9CF, #F3E9D2)", 2: "linear-gradient(150deg, #F3E9D2, #FFD9CF)", 3: "linear-gradient(150deg, #E5DDF5, #D8ECE3)", 4: "linear-gradient(150deg, #D8ECE3, #E5DDF5)" };
export const Avatar = ({ pastel }: { pastel: number }) => (
  <span style={{ width: 22, height: 22, background: GRAD[pastel] ?? GRAD[1], overflow: "hidden", display: "block" }}>
    <pre style={{ margin: 0, fontFamily: "var(--font-mono)", fontSize: 5, lineHeight: "5px", color: "rgba(20,20,20,0.5)", whiteSpace: "pre" }}>{" ;tt; \n;fCCf;\n1LGGL1\nfCG0GC"}</pre></span>);
export function FlagRow({ f, selected, share, people, where, position, total, onSelect, rowRef }: { f: Finding; selected: boolean; share: number; people: Persona[]; where: string; position: number; total: number; onSelect: () => void; rowRef?: (el: HTMLDivElement | null) => void }) {
  const sev = severity(f);
  return (
    <div ref={rowRef} className="flag-row" role="option" aria-selected={selected} aria-label={`${position} of ${total}. ${flagTitle(f)}. ${sev.text}. ${where}.`}
      tabIndex={selected ? 0 : -1} onClick={onSelect}
      style={{ display: "grid", gridTemplateColumns: "3px minmax(0, 1fr)", gap: 11, padding: "11px 12px 11px 0", borderBottom: "1px solid var(--line-soft)", background: selected ? "rgba(255,90,31,0.06)" : "transparent", cursor: "pointer" }}>
      <span aria-hidden style={{ background: sev.color, opacity: selected ? 1 : 0.35 }} />
      <div style={{ display: "flex", flexDirection: "column", gap: 7, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
          <span style={{ flex: 1, minWidth: 0, fontSize: 16, letterSpacing: "-0.01em", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{flagTitle(f)}</span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.08em", color: selected ? "var(--ink)" : "var(--muted)", whiteSpace: "nowrap" }}>{`~${Math.round(share * 100)}%`}</span>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 6 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", color: sev.color, background: sev.bg, padding: "3px 6px", whiteSpace: "nowrap" }}>{sev.text}</span>
          {f.engine_consensus && <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", color: "#FFFFFF", background: "#141414", padding: "3px 6px" }}>EVERY ENGINE</span>}
          <span style={{ flex: 1 }} />
          <span style={{ display: "flex", gap: 3 }}>{people.map(p => <Avatar key={p.id} pastel={p.pastel} />)}</span>
        </div>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.08em", color: "var(--muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{where}</span>
      </div>
    </div>);
}
