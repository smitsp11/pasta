import { render, screen } from "@testing-library/react";
import { Learning } from "../src/screens/Learning";
import { initialState, reduce } from "../src/state/reducer";
import demo from "../src/data/iris_demo.json";
it("shows read quotes, the focused source, and counts", () => {
  let s = initialState(demo as any);
  s = reduce(s, { type: "stage", name: "explore", timestamp: "" });
  s = reduce(s, { type: "source_read", source_id: "trustpilot", quotes: demo.reads[0].quotes as any, timestamp: "" });
  s = reduce(s, { type: "site_model", site_model: demo.site_model as any, nodes: demo.nodes.slice(0, 3) as any });
  render(<Learning state={s} />);
  expect(screen.getByText("checkout resets on my phone every time")).toBeInTheDocument();
  expect(screen.getByText("2 PIECES OF EVIDENCE · 1 SOURCE")).toBeInTheDocument();
  expect(screen.getByText("3 PAGES · 1 JOURNEY")).toBeInTheDocument();
  expect(screen.getByText("Trustpilot")).toHaveStyle({ color: "var(--scan-ink)" });
});
