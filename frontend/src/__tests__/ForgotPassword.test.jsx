import "@testing-library/jest-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { toast } from "react-toastify";
import ForgotPassword from "../pages/ForgotPassword";
import { requestPasswordReset } from "../services/api";

const mockNavigate = jest.fn();

jest.mock("../services/api", () => ({
  requestPasswordReset: jest.fn(),
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

describe("ForgotPassword page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  function renderPage() {
    render(
      <MemoryRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <ForgotPassword />
      </MemoryRouter>,
    );
  }

  test("shows validation error when email is missing", async () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: /send reset link/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Please enter your email");
      expect(requestPasswordReset).not.toHaveBeenCalled();
    });
  });

  test("submits email and redirects to login on success", async () => {
    requestPasswordReset.mockResolvedValue({
      data: {
        message: "Check your inbox",
      },
    });
    renderPage();

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "  user@example.com  " },
    });
    fireEvent.click(screen.getByRole("button", { name: /send reset link/i }));

    await waitFor(() => {
      expect(requestPasswordReset).toHaveBeenCalledWith({ email: "user@example.com" });
      expect(toast.success).toHaveBeenCalledWith("Check your inbox");
      expect(mockNavigate).toHaveBeenCalledWith("/login");
    });
  });

  test("shows fallback success message when backend message is missing", async () => {
    requestPasswordReset.mockResolvedValue({ data: {} });
    renderPage();

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send reset link/i }));

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith("Reset instructions sent");
    });
  });

  test("shows backend validation error", async () => {
    requestPasswordReset.mockRejectedValue({
      response: {
        data: {
          email: ["Account not found"],
        },
      },
    });
    renderPage();

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send reset link/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Account not found");
    });
  });

  test("shows generic error fallback and loading state", async () => {
    let rejectRequest;
    requestPasswordReset.mockReturnValue(
      new Promise((_, reject) => {
        rejectRequest = reject;
      }),
    );
    renderPage();

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send reset link/i }));

    expect(screen.getByRole("button", { name: /sending/i })).toBeDisabled();

    rejectRequest(new Error("network"));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Unable to process request");
      expect(screen.getByRole("button", { name: /send reset link/i })).toBeInTheDocument();
    });
  });

  test("navigates back to sign in from the footer", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: /back to sign in/i }));

    expect(mockNavigate).toHaveBeenCalledWith("/login");
  });
});
