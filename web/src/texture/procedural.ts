// Seeded texture for cards with no source image (the exports use hand-made ramps; this makes them deterministic per id).
import { RAMP } from "./ascii";
export function proceduralAscii(seed: string, cols: number, rows: number): string[] {
  let h = 2166136261; for (const ch of seed) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619); }
  const rnd = () => { h ^= h << 13; h ^= h >>> 17; h ^= h << 5; return ((h >>> 0) % 1000) / 1000; };
  const cx = cols * (0.35 + rnd() * 0.3), cy = rows * (0.35 + rnd() * 0.3), r = Math.min(cols, rows) * (0.25 + rnd() * 0.2);
  const lines: string[] = [];
  for (let y = 0; y < rows; y++) { let line = ""; for (let x = 0; x < cols; x++) {
    const d = Math.hypot((x - cx) / 1.0, (y - cy) * 2) / r; const l = Math.min(1, Math.max(0, 1 - Math.exp(-d * 1.2) + rnd() * 0.08));
    line += RAMP[Math.round((1 - l) * (RAMP.length - 1))]; } lines.push(line); }
  return lines;
}
