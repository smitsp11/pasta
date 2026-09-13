import { render, screen } from "@testing-library/react";
import App from "../src/App";
it("renders the wordmark", () => { render(<App />); expect(screen.getByText("Iris")).toBeInTheDocument(); });
