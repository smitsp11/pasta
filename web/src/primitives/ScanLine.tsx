export const ScanLine = ({ duration = 2.4 }: { duration?: number }) =>
  <span aria-hidden style={{ position: "absolute", left: 0, right: 0, top: "2%", height: 2, background: "var(--scan)", opacity: 0.9, boxShadow: "0 0 8px rgba(255,90,31,0.6)", animation: `irisScan ${duration}s linear infinite`, pointerEvents: "none" }} />;
