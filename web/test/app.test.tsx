import { render, screen, act, fireEvent } from "@testing-library/react";
import App from "../src/App";
import { TARGETS } from "../src/data/targets";
it("plays the whole show at high speed and reaches the report", async () => {
  vi.useFakeTimers();
  window.history.replaceState({}, "", "/?speed=50");
  render(<App />);
  fireEvent.click(screen.getByText("RUN IRIS →"));
  for (let i = 0; i < 40; i++) await act(async () => { vi.advanceTimersByTime(250); });
  expect(screen.getByText("What broke, for whom, and why.")).toBeInTheDocument();
  const shown = TARGETS.find(t => t.id !== "northwind") ?? TARGETS[0];   // the input placeholder target
  expect(screen.getAllByText(/OF SHOPPERS/).length).toBe(shown.demo.findings.length);
  vi.useRealTimers();
});
