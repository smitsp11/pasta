export const Serif = ({ children, size, style, as: Tag = "h1" }: { children: React.ReactNode; size?: number | string; style?: React.CSSProperties; as?: "h1" | "h2" | "span" }) =>
  <Tag className="serif" style={{ margin: 0, fontSize: size ?? "clamp(40px, 6vw, 76px)", textWrap: "balance", ...style }}>{children}</Tag>;
