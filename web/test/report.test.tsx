import { fireEvent, render, screen } from "@testing-library/react";
import { Report } from "../src/screens/Report";
import demo from "../src/data/iris_demo.json";
it("shows both scores, ranked flags, and switches detail on click", () => {
  render(<Report scorecard={demo.scorecard as any} findings={demo.findings as any} affected={demo.affected as any} personas={demo.personas as any} sources={demo.sources as any} instant />);
  expect(screen.getByText("85")).toBeInTheDocument(); expect(screen.getByText("58")).toBeInTheDocument();
  expect(screen.getByText("1 RUN EXCLUDED · TOOLING ERROR")).toBeInTheDocument();
  const rows = screen.getAllByText(/OF SHOPPERS/); expect(rows[0]).toHaveTextContent("~63%");   // ranked by share desc
  fireEvent.click(screen.getByText("Cookie wall"));
  expect(screen.getByText(/OK button is 16px on mobile/)).toBeInTheDocument();
  expect(screen.getByText("STEP 4 · 00:41")).toBeInTheDocument();
});
