import type { FeedStatus } from "../types";
const C: Record<FeedStatus, { color: string; bg: string; border: string }> = {
  running: { color: "#FF5A1F", bg: "rgba(255,90,31,0.08)", border: "#FF5A1F" }, completed: { color: "#1F9D55", bg: "rgba(31,157,85,0.08)", border: "#1F9D55" },
  stalled: { color: "#D93025", bg: "rgba(217,48,37,0.08)", border: "#D93025" }, harness_error: { color: "#8A8580", bg: "rgba(138,133,128,0.10)", border: "rgba(20,20,20,0.18)" } };
export const Pill = ({ status, children }: { status: FeedStatus; children: React.ReactNode }) =>
  <span className="mono" style={{ fontSize: 10, fontWeight: 500, padding: "3px 7px", color: C[status].color, background: C[status].bg, border: `1px solid ${C[status].border}`, display: "inline-flex", alignItems: "center", gap: 5, whiteSpace: "nowrap" }}>
    {status === "running" && <span style={{ width: 5, height: 5, borderRadius: "50%", background: "#FF5A1F", animation: "irisPulse 1.4s ease-in-out infinite" }} />}{children}</span>;
