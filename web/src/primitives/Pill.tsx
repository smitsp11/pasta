import type { FeedStatus } from "../types";
const C: Record<FeedStatus, { color: string; bg: string; border: string }> = {
  running: { color: "var(--scan-ink)", bg: "rgba(255,90,31,0.08)", border: "var(--scan)" }, completed: { color: "var(--ok-ink)", bg: "rgba(31,157,85,0.08)", border: "var(--ok-ink)" },
  stalled: { color: "var(--stall-ink)", bg: "rgba(217,48,37,0.08)", border: "var(--stall-ink)" }, harness_error: { color: "var(--muted)", bg: "rgba(138,133,128,0.10)", border: "rgba(20,20,20,0.18)" } };
export const Pill = ({ status, children }: { status: FeedStatus; children: React.ReactNode }) =>
  <span className="mono" style={{ fontSize: 10, fontWeight: 500, padding: "3px 7px", color: C[status].color, background: C[status].bg, border: `1px solid ${C[status].border}`, display: "inline-flex", alignItems: "center", gap: 5, whiteSpace: "nowrap" }}>
    {status === "running" && <span style={{ width: 5, height: 5, borderRadius: "50%", background: "var(--scan)", animation: "irisPulse 1.4s ease-in-out infinite" }} />}{children}</span>;
