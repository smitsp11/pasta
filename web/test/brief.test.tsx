import { render, screen } from "@testing-library/react";
import { Brief } from "../src/screens/Brief";
import demo from "../src/data/iris_demo.json";
it("renders eight personas, the matched pair label, and the stress table", () => {
  render(<Brief personas={demo.personas as any} stressTests={demo.stress_tests} sources={demo.sources as any} />);
  expect(screen.getAllByText(/Coupon hunter, United States/)).toHaveLength(2);
  expect(screen.getByText("MATCHED PAIR · DEVICE")).toBeInTheDocument();
  expect(screen.getByText("checkout on mobile")).toBeInTheDocument();
  expect(screen.getAllByText("CA").length).toBeGreaterThanOrEqual(2);
});
