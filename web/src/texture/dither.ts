const BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]];
export const bayerIndex = (x: number, y: number) => BAYER4[y & 3][x & 3];
export function ditherPixel(luma: number, x: number, y: number, palette: string[]): string {
  const thresh = (bayerIndex(x, y) + 0.5) / 16;                     // 0..1
  const levels = palette.length - 1;
  const v = Math.min(levels, Math.floor(luma * levels + thresh));   // ordered dither across palette levels
  return palette[levels - v];                                        // palette[0] = lightest
}
export async function ditherImage(src: string, w: number, h: number, palette: string[]): Promise<HTMLCanvasElement> {
  const { load } = await import("./ascii");
  const img = await load(src);
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const ctx = c.getContext("2d")!; ctx.drawImage(img, 0, 0, w, h);
  const id = ctx.getImageData(0, 0, w, h); const out = ctx.createImageData(w, h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = (y * w + x) * 4; const l = (0.2126 * id.data[i] + 0.7152 * id.data[i + 1] + 0.0722 * id.data[i + 2]) / 255;
    const hex = ditherPixel(l, x, y, palette); out.data[i] = parseInt(hex.slice(1, 3), 16); out.data[i + 1] = parseInt(hex.slice(3, 5), 16); out.data[i + 2] = parseInt(hex.slice(5, 7), 16); out.data[i + 3] = 255;
  }
  ctx.putImageData(out, 0, 0); return c;
}
