import "@testing-library/jest-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { toast } from "react-toastify";
import Register from "../pages/Register";
import { registerUser } from "../services/api";

const mockNavigate = jest.fn();

jest.mock("../services/api", () => ({
  registerUser: jest.fn(),
}));

jest.mock("react-toastify", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

describe("Register page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  function renderPage() {
    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>,
    );
  }

  test("shows validation error when fields are missing", async () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Please fill all fields");
      expect(registerUser).not.toHaveBeenCalled();
    });
  });

  test("shows mismatch message when passwords do not match", async () => {
    renderPage();

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: "subbu" } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: "subbu@example.com" } });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: "pass123" } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: "pass456" } });

    expect(screen.getByText("Passwords do not match")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Passwords do not match");
    });
  });

  test("registers successfully and redirects to login", async () => {
    registerUser.mockResolvedValue({ data: {} });
    renderPage();

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: "subbu" } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: "subbu@example.com" } });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: "pass123" } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: "pass123" } });

    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(registerUser).toHaveBeenCalledWith({
        username: "subbu",
        email: "subbu@example.com",
        password: "pass123",
      });
      expect(toast.success).toHaveBeenCalledWith("Account created! Please sign in.");
      expect(mockNavigate).toHaveBeenCalledWith("/");
    });
  });

  test("shows backend validation errors", async () => {
    registerUser.mockRejectedValue({
      response: { data: { email: ["Email already exists"] } },
    });
    renderPage();

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: "subbu" } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: "subbu@example.com" } });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: "pass123" } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: "pass123" } });

    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Email already exists");
    });
  });
});
