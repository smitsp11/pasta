import { render, screen, act, fireEvent } from "@testing-library/react";
import App from "../src/App";
import { TARGETS } from "../src/data/targets";
it("plays the whole show at high speed and reaches the report", async () => {
  vi.useFakeTimers();
  window.history.replaceState({}, "", "/?speed=50");
  render(<App />);
  fireEvent.change(screen.getByRole("textbox"), { target: { value: "https://www.ikea.com/ca/en/" } });
  fireEvent.click(screen.getByText("RUN IRIS →"));
  for (let i = 0; i < 40; i++) await act(async () => { vi.advanceTimersByTime(250); });
  expect(screen.getByText("What broke, for whom, and why.")).toBeInTheDocument();
  const shown = TARGETS.find(t => t.id === "ikea")!;
  expect(screen.getAllByRole("option").length).toBe(shown.demo.findings.length);
  // a second run on another url restarts the show from the top and lands on that target's report
  fireEvent.change(screen.getByRole("textbox"), { target: { value: "https://www.zara.com/us/" } });
  fireEvent.click(screen.getByText("RUN AGAIN →"));
  await act(async () => { vi.advanceTimersByTime(500); });
  expect(screen.queryAllByRole("option")).toHaveLength(0);
  for (let i = 0; i < 40; i++) await act(async () => { vi.advanceTimersByTime(250); });
  expect(screen.getAllByRole("option").length).toBe(TARGETS.find(t => t.id === "zara")!.demo.findings.length);
  vi.useRealTimers();
});
