export const RAMP = " .:;i1tfLCG08@";          // light → dark
export type Luma = (x: number, y: number) => number;   // 0 = black … 1 = white, sampled at cell centres
export function asciiFromLuma(luma: Luma, cols: number, rows: number): string[] {
  const lines: string[] = [];
  for (let y = 0; y < rows; y++) {
    let line = "";
    for (let x = 0; x < cols; x++) { const l = Math.min(1, Math.max(0, luma(x, y))); line += RAMP[Math.round((1 - l) * (RAMP.length - 1))]; }
    lines.push(line);
  }
  return lines;
}
export async function asciiFromImage(src: string, cols: number, rows: number): Promise<string[]> {
  const img = await load(src);
  const c = document.createElement("canvas"); c.width = cols; c.height = rows;
  const ctx = c.getContext("2d")!; ctx.drawImage(img, 0, 0, cols, rows);
  const { data } = ctx.getImageData(0, 0, cols, rows);
  return asciiFromLuma((x, y) => { const i = (y * cols + x) * 4; return (0.2126 * data[i] + 0.7152 * data[i + 1] + 0.0722 * data[i + 2]) / 255; }, cols, rows);
}
export const load = (src: string) => new Promise<HTMLImageElement>((res, rej) => { const im = new Image(); im.crossOrigin = "anonymous"; im.onload = () => res(im); im.onerror = rej; im.src = src; });
