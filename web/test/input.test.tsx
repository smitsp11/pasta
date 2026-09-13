import { fireEvent, render, screen } from "@testing-library/react";
import { Input } from "../src/screens/Input";
it("submits the url and calls onRun once", () => {
  const onRun = vi.fn();
  render(<Input onRun={onRun} />);
  fireEvent.change(screen.getByRole("textbox"), { target: { value: "https://x.test" } });
  fireEvent.click(screen.getByText("RUN IRIS →"));
  expect(onRun).toHaveBeenCalledWith("https://x.test");
  expect(onRun).toHaveBeenCalledTimes(1);
  expect(screen.getByText("Send your customers in first.")).toBeInTheDocument();
});
it("stays usable after a run has started so a second url can be run", () => {
  const onRun = vi.fn();
  render(<Input onRun={onRun} collapsed />);
  fireEvent.change(screen.getByRole("textbox"), { target: { value: "https://www.zara.com/us/" } });
  fireEvent.click(screen.getByText("RUN AGAIN →"));
  expect(onRun).toHaveBeenCalledWith("https://www.zara.com/us/");
});
