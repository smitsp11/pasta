import { render, screen } from "@testing-library/react";
import { TopBar } from "../src/components/TopBar";
it("marks stages and pluralises sessions", () => {
  render(<TopBar stage="run" sessions={8} cached />);
  expect(screen.getByText("SWARM")).toBeInTheDocument();
  expect(screen.getByText("[ 8 SESSIONS ]")).toBeInTheDocument();
  expect(screen.getByText("[ CACHED ]")).toBeInTheDocument();
  render(<TopBar stage="idle" sessions={1} />); expect(screen.getByText("[ 1 SESSION ]")).toBeInTheDocument();
});
