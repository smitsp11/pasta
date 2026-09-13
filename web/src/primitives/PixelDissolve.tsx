import { useMemo } from "react";
/** Overlay of 16px blocks in `color` that fade out with random delays over `duration`s, revealing children. Re-keys when `trigger` changes. */
export function PixelDissolve({ children, trigger, color = "#FAF7F2", duration = 0.6, style }:
  { children: React.ReactNode; trigger: string | number; color?: string; duration?: number; style?: React.CSSProperties }) {
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const cells = useMemo(() => Array.from({ length: 12 * 8 }, (_, i) => ({ i, d: Math.random() * duration })), [trigger, duration]);
  return (
    <span style={{ position: "relative", display: "block", ...style }}>
      {children}
      <span key={String(trigger)} aria-hidden style={{ position: "absolute", inset: 0, display: "grid", gridTemplateColumns: "repeat(12, 1fr)", gridTemplateRows: "repeat(8, 1fr)", pointerEvents: "none" }}>
        {cells.map(c => <span key={c.i} style={{ background: color, opacity: 1, animation: `irisFade 0.12s linear ${c.d}s forwards` }} />)}
      </span>
    </span>);
}
