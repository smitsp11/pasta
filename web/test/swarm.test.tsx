import { render, screen } from "@testing-library/react";
import { Swarm } from "../src/screens/Swarm";
import { initialState, reduce } from "../src/state/reducer";
import { buildScript } from "../src/data/script";
import demo from "../src/data/iris_demo.json";
it("renders eight feeds with derived tally and status overlays", () => {
  const s = buildScript(demo as any).reduce((st, c) => reduce(st, c.item), initialState(demo as any));
  render(<Swarm state={s} />);
  expect(screen.getByText("0 RUNNING · 5 DONE · 2 STALLED · 1 ERROR")).toBeInTheDocument();
  expect(screen.getAllByText("STALLED").length).toBeGreaterThanOrEqual(2);
  expect(screen.getByText("TOOLING ERROR · EXCLUDED")).toBeInTheDocument();
  expect(screen.getByText("overlay keeps intercepting clicks")).toBeInTheDocument();
});
