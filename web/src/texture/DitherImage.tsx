import { useEffect, useRef } from "react";
import { ditherImage } from "./dither";
export function DitherImage({ src, width, height, palette = ["#FAF7F2", "#D9D4CC", "#8A8580", "#141414"], style }:
  { src: string; width: number; height: number; palette?: string[]; style?: React.CSSProperties }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => { let on = true; ditherImage(src, width, height, palette).then(c => { if (!on || !ref.current) return; const ctx = ref.current.getContext("2d")!; ctx.imageSmoothingEnabled = false; ctx.drawImage(c, 0, 0); }).catch(() => {}); return () => { on = false; }; }, [src, width, height]);
  return <canvas ref={ref} width={width} height={height} style={{ imageRendering: "pixelated", ...style }} />;
}
