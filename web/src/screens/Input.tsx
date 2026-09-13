import { useState } from "react";
import { motion } from "motion/react";
import { Serif } from "../primitives/Serif";
export function Input({ onRun, collapsed = false }: { onRun: (url: string) => void; collapsed?: boolean }) {
  const [url, setUrl] = useState("");
  const placeholder = "https://";
  const canRun = url.trim().length > 0;
  return (
    <motion.section layout initial={false} animate={{ minHeight: collapsed ? 0 : "calc(100vh - 64px)", paddingTop: collapsed ? 24 : 32, paddingBottom: collapsed ? 24 : 48 }}
      transition={{ duration: 0.6, ease: "easeInOut" }}
      style={{ position: "relative", display: "flex", alignItems: "center", justifyContent: "center", padding: "32px 32px 48px", overflow: "hidden" }}>
      <div style={{ position: "relative", zIndex: 2, width: "100%", maxWidth: 660, display: "flex", flexDirection: "column", alignItems: "center", gap: collapsed ? 16 : 34 }}>
        {!collapsed && <img src="/assets/computer-globe-monitor.png" alt="" style={{ position: "absolute", left: "50%", bottom: "calc(100% + 14px)", transform: "translateX(-50%)", height: "min(150px, 26vh)", width: "auto", maxWidth: "100%", opacity: 0.2, imageRendering: "pixelated", pointerEvents: "none", userSelect: "none" }} />}
        <Serif size={collapsed ? 28 : "clamp(40px, 6vw, 76px)"} style={{ position: "relative", zIndex: 1, textAlign: "center", lineHeight: 0.96 }}>Send your customers in first.</Serif>
        <form style={{ position: "relative", zIndex: 1, width: "100%", maxWidth: 580, display: "flex", flexWrap: "wrap", gap: 10 }} onSubmit={e => { e.preventDefault(); if (canRun) onRun(url); }}>
          <input value={url} onChange={e => setUrl(e.target.value)} placeholder={placeholder} aria-label="Site to scan" className="url-input"
            style={{ flex: "1 1 300px", minWidth: 0, boxSizing: "border-box", fontFamily: "var(--font-mono)", fontSize: 16, color: "#141414", background: "#FFFFFF", border: "1px solid rgba(20,20,20,0.22)", padding: "15px 18px", outline: "none" }}
            onFocus={e => { e.currentTarget.style.borderColor = "var(--scan)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(255,90,31,0.12)"; }}
            onBlur={e => { e.currentTarget.style.borderColor = "rgba(20,20,20,0.22)"; e.currentTarget.style.boxShadow = "none"; }} />
          <button type="submit" disabled={!canRun} className="btn-primary" style={{ flex: "0 0 auto", fontFamily: "var(--font-mono)", fontSize: 13, fontWeight: 500, letterSpacing: "0.14em", color: "#FFFFFF", background: canRun ? "var(--scan-deep)" : "var(--muted)", border: "none", padding: "15px 28px", cursor: canRun ? "pointer" : "not-allowed", whiteSpace: "nowrap" }}>{collapsed ? "RUN AGAIN →" : "RUN IRIS →"}</button>
        </form>
      </div>
    </motion.section>);
}
