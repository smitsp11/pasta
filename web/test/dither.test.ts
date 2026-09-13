import { bayerIndex, ditherPixel } from "../src/texture/dither";
it("bayer threshold and palette snap are deterministic", () => {
  expect(bayerIndex(0, 0)).toBe(0); expect(bayerIndex(1, 1)).toBe(4); expect(bayerIndex(3, 3)).toBe(5);
  const palette = ["#FAF7F2", "#141414"];
  // cell (1,0) has threshold 8/16: bright pixels snap light, dark pixels snap dark
  expect(ditherPixel(0.95, 1, 0, palette)).toBe("#FAF7F2");
  expect(ditherPixel(0.05, 1, 0, palette)).toBe("#141414");
  // cell (0,0) has the lowest threshold, so it is the one cell that stays dark for a 95% pixel (ordered dither)
  expect(ditherPixel(0.95, 0, 0, palette)).toBe("#141414");
});
