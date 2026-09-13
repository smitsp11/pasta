import type { Finding, Persona } from "../../types";
const TITLE: Record<string, string> = { cookie_wall: "Cookie wall", icon_only_control: "Icon-only cart button", geo_block: "Geo-blocked pricing", hidden_nav: "Hidden mobile nav", captcha: "CAPTCHA wall", ambiguous_cta: "Ambiguous call to action", infinite_scroll: "Infinite scroll", login_wall: "Login wall", layout_shift: "Layout shift", timeout: "Timed out", other: "Other" };
export const flagTitle = (f: Finding) => TITLE[f.category] ?? f.category;
export const severity = (f: Finding) => f.attributed_to === "site" ? { text: "FAILS FOR EVERYONE", color: "#D93025", bg: "rgba(217,48,37,0.1)" } : { text: `FAILS ONLY ON ${f.attributed_to === "device" ? f.config.device : f.attributed_to === "country" ? f.config.country : f.attributed_to === "identity" ? "RETURNING" : "VISION AGENTS"}`.toUpperCase(), color: "#FF5A1F", bg: "rgba(255,90,31,0.12)" };
const GRAD: Record<number, string> = { 1: "linear-gradient(150deg, #FFD9CF, #F3E9D2)", 2: "linear-gradient(150deg, #F3E9D2, #FFD9CF)", 3: "linear-gradient(150deg, #E5DDF5, #D8ECE3)", 4: "linear-gradient(150deg, #D8ECE3, #E5DDF5)" };
export const Avatar = ({ pastel }: { pastel: number }) => (
  <span style={{ width: 22, height: 22, background: GRAD[pastel] ?? GRAD[1], overflow: "hidden", display: "block" }}>
    <pre style={{ margin: 0, fontFamily: "var(--font-mono)", fontSize: 5, lineHeight: "5px", color: "rgba(20,20,20,0.5)", whiteSpace: "pre" }}>{" ;tt; \n;fCCf;\n1LGGL1\nfCG0GC"}</pre></span>);
export function FlagRow({ f, selected, share, people, onSelect }: { f: Finding; selected: boolean; share: number; people: Persona[]; onSelect: () => void }) {
  const sev = severity(f);
  return (
    <div role="button" tabIndex={0} onClick={onSelect} onKeyDown={e => { if (e.key === "Enter" || e.key === " ") onSelect(); }} style={{ display: "flex", flexDirection: "column", gap: 9, padding: "16px 0", borderBottom: "1px solid rgba(20,20,20,0.1)", background: selected ? "rgba(255,90,31,0.05)" : "transparent", cursor: "pointer" }}>
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10, padding: "0 12px" }}>
        <span style={{ fontSize: 17, letterSpacing: "-0.01em" }}>{flagTitle(f)}</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", color: sev.color, background: sev.bg, padding: "3px 6px", whiteSpace: "nowrap" }}>{sev.text}</span>
        {f.engine_consensus && <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", color: "#FFFFFF", background: "#141414", padding: "3px 6px" }}>EVERY ENGINE</span>}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8, padding: "0 12px" }}>
        <span style={{ display: "flex", gap: 4 }}>{people.map(p => <Avatar key={p.id} pastel={p.pastel} />)}</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em", color: "#8A8580" }}>{`~${Math.round(share * 100)}% OF SHOPPERS`}</span>
      </div>
    </div>);
}
