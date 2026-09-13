import { useEffect, useState } from "react";
import { asciiFromImage } from "./ascii";
import { proceduralAscii } from "./procedural";
const PASTEL = { 1: "var(--pastel-1)", 2: "var(--pastel-2)", 3: "var(--pastel-3)", 4: "var(--pastel-4)" } as const;
export function AsciiImage({ src, seed, cols = 48, rows = 14, pastel = 2, fontSize = 9, className, style }:
  { src?: string | null; seed: string; cols?: number; rows?: number; pastel?: 1 | 2 | 3 | 4; fontSize?: number; className?: string; style?: React.CSSProperties }) {
  const [lines, setLines] = useState<string[]>(() => proceduralAscii(seed, cols, rows));
  useEffect(() => { setLines(proceduralAscii(seed, cols, rows)); }, [seed, cols, rows]);
  useEffect(() => { let on = true; if (src) asciiFromImage(src, cols, rows).then(l => on && setLines(l)).catch(() => {}); return () => { on = false; }; }, [src, cols, rows]);
  return (
    <pre className={className} style={{ margin: 0, fontFamily: "var(--font-mono)", fontSize, lineHeight: 1.15, color: "rgba(20,20,20,0.55)", whiteSpace: "pre", overflow: "hidden",
      background: `linear-gradient(160deg, ${PASTEL[pastel]} 0%, #FAF7F2 100%)`, padding: "10px 12px", ...style }}>{lines.join("\n")}</pre>
  );
}
