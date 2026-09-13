import { render, screen, act, fireEvent } from "@testing-library/react";
import App from "../src/App";
it("plays the whole show at high speed and reaches the report", async () => {
  vi.useFakeTimers();
  window.history.replaceState({}, "", "/?speed=50");
  render(<App />);
  fireEvent.click(screen.getByText("RUN IRIS →"));
  for (let i = 0; i < 40; i++) await act(async () => { vi.advanceTimersByTime(250); });
  expect(screen.getByText("What broke, for whom, and why.")).toBeInTheDocument();
  expect(screen.getAllByText(/OF SHOPPERS/).length).toBe(4);
  vi.useRealTimers();
});
