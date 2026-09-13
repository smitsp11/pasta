import { asciiFromLuma, RAMP } from "../src/texture/ascii";
it("maps luminance to the ramp, dark = dense", () => {
  const cols = 4, rows = 2;
  const luma = (_x: number, y: number) => (y === 0 ? 0 : 1);   // top row black, bottom row white
  const out = asciiFromLuma(luma, cols, rows);
  expect(out).toHaveLength(2);
  expect(out[0]).toBe(RAMP[RAMP.length - 1].repeat(4));       // '@@@@'
  expect(out[1]).toBe(RAMP[0].repeat(4));                       // '    '
});
