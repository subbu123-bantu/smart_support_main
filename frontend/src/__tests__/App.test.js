import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import App from "../App";

test("renders login page", () => {
  render(<App />);
  const text = screen.getByText(/welcome back/i);
  expect(text).toBeInTheDocument();
});
