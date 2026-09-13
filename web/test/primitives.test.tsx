import { render, screen, act } from "@testing-library/react";
import { Chip } from "../src/primitives/Chip";
import { Pill } from "../src/primitives/Pill";
import { TextScramble } from "../src/primitives/TextScramble";
import { NumberTick } from "../src/primitives/NumberTick";
it("chip uppercases mono text and pill maps status to colour", () => {
  render(<Chip>mobile</Chip>); expect(screen.getByText("mobile")).toHaveStyle({ textTransform: "uppercase" });
  render(<Pill status="stalled">STALLED</Pill>); expect(screen.getByText("STALLED")).toHaveStyle({ color: "var(--stall-ink)" });
});
it("text scramble settles on the final text", async () => {
  vi.useFakeTimers(); render(<TextScramble duration={0.2} speed={0.02}>Watch them try.</TextScramble>);
  await act(async () => { vi.advanceTimersByTime(600); });
  expect(screen.getByText("Watch them try.")).toBeInTheDocument(); vi.useRealTimers();
});
it("number tick renders the target value when reduced motion", () => {
  render(<NumberTick value={58} instant />); expect(screen.getByText("58")).toBeInTheDocument();
});
