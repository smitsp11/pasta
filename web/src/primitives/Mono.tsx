export const Mono = ({ children, size = 11, color = "var(--muted)", style, ...rest }: React.HTMLAttributes<HTMLSpanElement> & { size?: number; color?: string }) =>
  <span className="mono" style={{ fontSize: size, fontWeight: 500, color, ...style }} {...rest}>{children}</span>;
