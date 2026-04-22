import "@testing-library/jest-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { act } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { toast } from "react-toastify";
import ResetPassword from "../pages/ResetPassword";
import { resetPassword } from "../services/api";

const mockNavigate = jest.fn();
let mockSearchParams = new URLSearchParams("uid=user-1&token=token-123");

jest.mock("../services/api", () => ({
  resetPassword: jest.fn(),
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
  useSearchParams: () => [mockSearchParams],
}));

describe("ResetPassword page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams = new URLSearchParams("uid=user-1&token=token-123");
  });

  function renderPage() {
    render(
      <MemoryRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <ResetPassword />
      </MemoryRouter>,
    );
  }

  test("shows invalid link state when query params are missing", () => {
    mockSearchParams = new URLSearchParams("");
    renderPage();

    expect(
      screen.getByText("This reset link is missing required information."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reset password/i })).toBeDisabled();
  });

  test("shows invalid link toast when the form is submitted without link data", async () => {
    mockSearchParams = new URLSearchParams("");
    renderPage();

    fireEvent.submit(screen.getByRole("button", { name: /reset password/i }).closest("form"));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Reset link is invalid");
    });
  });

  test("shows validation error when fields are missing", async () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: /reset password/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Please fill all fields");
      expect(resetPassword).not.toHaveBeenCalled();
    });
  });

  test("shows mismatch error when passwords differ", async () => {
    renderPage();

    fireEvent.change(screen.getByLabelText(/new password/i), {
      target: { value: "pass123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: "pass456" },
    });
    fireEvent.click(screen.getByRole("button", { name: /reset password/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Passwords do not match");
      expect(resetPassword).not.toHaveBeenCalled();
    });
  });

  test("submits the reset request and redirects on success", async () => {
    resetPassword.mockResolvedValue({
      data: {
        message: "Password changed",
      },
    });
    renderPage();

    fireEvent.change(screen.getByLabelText(/new password/i), {
      target: { value: "pass123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: "pass123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /reset password/i }));

    await waitFor(() => {
      expect(resetPassword).toHaveBeenCalledWith({
        uid: "user-1",
        token: "token-123",
        password: "pass123",
        confirm_password: "pass123",
      });
      expect(toast.success).toHaveBeenCalledWith("Password changed");
      expect(mockNavigate).toHaveBeenCalledWith("/login");
    });
  });

  test("shows fallback success message when backend message is missing", async () => {
    resetPassword.mockResolvedValue({ data: {} });
    renderPage();

    fireEvent.change(screen.getByLabelText(/new password/i), {
      target: { value: "pass123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: "pass123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /reset password/i }));

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith("Password reset successful");
    });
  });

  test("shows backend confirm password error", async () => {
    resetPassword.mockRejectedValue({
      response: {
        data: {
          confirm_password: ["Passwords do not satisfy policy"],
        },
      },
    });
    renderPage();

    fireEvent.change(screen.getByLabelText(/new password/i), {
      target: { value: "pass123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: "pass123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /reset password/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Passwords do not satisfy policy");
    });
  });

  test("navigates to forgot password when requesting another link", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: /request another/i }));

    expect(mockNavigate).toHaveBeenCalledWith("/forgot-password");
  });

  test("shows loading state and password or generic backend fallbacks", async () => {
    let resolveRequest;
    resetPassword.mockReturnValue(
      new Promise((resolve) => {
        resolveRequest = resolve;
      }),
    );
    renderPage();

    fireEvent.change(screen.getByLabelText(/new password/i), {
      target: { value: "pass123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: "pass123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /reset password/i }));

    expect(screen.getByRole("button", { name: /resetting/i })).toBeDisabled();

    act(() => resolveRequest({ data: {} }));
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith("/login"));

    resetPassword.mockRejectedValueOnce({
      response: { data: { password: ["Password too weak"] } },
    });
    fireEvent.click(screen.getByRole("button", { name: /reset password/i }));
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Password too weak");
    });

    resetPassword.mockRejectedValueOnce(new Error("network"));
    fireEvent.click(screen.getByRole("button", { name: /reset password/i }));
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Unable to reset password");
    });
  });
});
