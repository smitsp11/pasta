export const Chip = ({ children, active = false }: { children: React.ReactNode; active?: boolean }) =>
  <span className="mono" style={{ fontSize: 11, fontWeight: 500, padding: "3px 6px", border: `1px solid ${active ? "var(--scan)" : "var(--line)"}`, color: active ? "var(--scan)" : "var(--ink)", background: "#FFFFFF", textTransform: "uppercase" }}>{children}</span>;
