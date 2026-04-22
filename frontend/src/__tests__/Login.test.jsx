import "@testing-library/jest-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { toast } from "react-toastify";
import Login from "../pages/Login";
import { loginUser } from "../services/api";

const mockNavigate = jest.fn();

jest.mock("../services/api", () => ({
  loginUser: jest.fn(),
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

describe("Login page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  function renderPage() {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );
  }

  test("shows validation error when fields are missing", async () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Please fill all fields");
      expect(loginUser).not.toHaveBeenCalled();
    });
  });

  test("logs in successfully and stores auth data", async () => {
    loginUser.mockResolvedValue({
      data: {
        user: {
          access: "token-123",
          role: "admin",
          username: "subbu",
        },
      },
    });
    renderPage();

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: "subbu" } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: "pass123" } });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(loginUser).toHaveBeenCalledWith({ username: "subbu", password: "pass123" });
      expect(localStorage.getItem("access")).toBe("token-123");
      expect(localStorage.getItem("role")).toBe("admin");
      expect(localStorage.getItem("username")).toBe("subbu");
      expect(toast.success).toHaveBeenCalledWith("Login successful!", { autoClose: 800 });
      expect(mockNavigate).toHaveBeenCalledWith("/dashboard");
    });
  });

  test("shows backend login errors", async () => {
    loginUser.mockRejectedValue({
      response: { data: { error: "Invalid credentials" } },
    });
    renderPage();

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: "subbu" } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: "wrong-pass" } });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Invalid credentials");
    });
  });

  test("shows fallback login error and toggles loading state", async () => {
    let resolveRequest;
    loginUser.mockReturnValue(
      new Promise((resolve) => {
        resolveRequest = resolve;
      }),
    );
    renderPage();

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: "subbu" } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: "pass123" } });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByRole("button", { name: /signing in/i })).toBeDisabled();

    resolveRequest({ data: { user: { access: "token", role: "agent", username: "subbu" } } });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/dashboard");
    });

    loginUser.mockRejectedValueOnce(new Error("network down"));
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: "retry-pass" } });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Login failed");
    });
  });

  test("navigates from footer actions", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: /forgot password/i }));
    fireEvent.click(screen.getByRole("button", { name: /create one/i }));
    fireEvent.keyDown(screen.getByRole("button", { name: /create one/i }), { key: "Enter" });

    expect(mockNavigate).toHaveBeenCalledWith("/forgot-password");
    expect(mockNavigate).toHaveBeenCalledWith("/register");
  });
});
