import { fireEvent, render, screen } from "@testing-library/react";
import { Report } from "../src/screens/Report";
import demo from "../src/data/iris_demo.json";
it("shows both scores, ranked flags, and switches detail on click", () => {
  render(<Report scorecard={demo.scorecard as any} findings={demo.findings as any} affected={demo.affected as any} personas={demo.personas as any} sources={demo.sources as any} instant />);
  expect(screen.getByText("85")).toBeInTheDocument(); expect(screen.getByText("58")).toBeInTheDocument();
  expect(screen.getByText("1 RUN EXCLUDED · TOOLING ERROR")).toBeInTheDocument();
  const rows = screen.getAllByRole("option");
  expect(rows).toHaveLength(4);
  expect(rows[0]).toHaveTextContent("~63%");                    // site-wide first, then share desc
  expect(screen.getByText("4 ISSUES")).toBeInTheDocument();
  expect(screen.getByText(/^1 \/ 4/)).toBeInTheDocument();
  fireEvent.click(screen.getByText("Cookie wall"));
  expect(screen.getByText(/OK button is 16px on mobile/)).toBeInTheDocument();
  expect(screen.getByText("STEP 4 · 00:41")).toBeInTheDocument();
  expect(screen.getByText("ISSUE 2 / 4")).toBeInTheDocument();
});
it("moves between issues with the arrow keys and j/k", () => {
  render(<Report scorecard={demo.scorecard as any} findings={demo.findings as any} affected={demo.affected as any} personas={demo.personas as any} sources={demo.sources as any} instant />);
  const list = screen.getByRole("listbox");
  expect(screen.getByText("ISSUE 1 / 4")).toBeInTheDocument();
  fireEvent.keyDown(list, { key: "ArrowDown" });
  expect(screen.getByText("ISSUE 2 / 4")).toBeInTheDocument();
  fireEvent.keyDown(list, { key: "j" });
  expect(screen.getByText("ISSUE 3 / 4")).toBeInTheDocument();
  fireEvent.keyDown(list, { key: "k" });
  expect(screen.getByText("ISSUE 2 / 4")).toBeInTheDocument();
  fireEvent.keyDown(list, { key: "ArrowDown" });
  fireEvent.keyDown(list, { key: "ArrowDown" });                 // two presses before a render still move two
  expect(screen.getByText("ISSUE 4 / 4")).toBeInTheDocument();
  fireEvent.keyDown(list, { key: "Home" });
  expect(screen.getByText("ISSUE 1 / 4")).toBeInTheDocument();
  fireEvent.keyDown(list, { key: "End" });
  expect(screen.getByText("ISSUE 4 / 4")).toBeInTheDocument();
  expect(screen.getAllByRole("option")[3]).toHaveAttribute("aria-selected", "true");
});
