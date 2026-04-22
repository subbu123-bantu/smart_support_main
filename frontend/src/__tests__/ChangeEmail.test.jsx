import "@testing-library/jest-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { toast } from "react-toastify";
import ChangeEmail from "../pages/ChangeEmail";
import { changeEmail } from "../services/api";

jest.mock("../services/api", () => ({
  changeEmail: jest.fn(),
}));

jest.mock("react-toastify", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

describe("ChangeEmail page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    localStorage.setItem("email", "stored@example.com");
  });

  test("prefills the stored email address", () => {
    render(<ChangeEmail />);

    expect(screen.getByLabelText(/new email/i)).toHaveValue("stored@example.com");
  });

  test("shows validation error when fields are missing", async () => {
    render(<ChangeEmail />);

    fireEvent.change(screen.getByLabelText(/new email/i), { target: { value: "   " } });
    fireEvent.click(screen.getByRole("button", { name: /update email/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Please fill all fields");
      expect(changeEmail).not.toHaveBeenCalled();
    });
  });

  test("updates the email and clears the password on success", async () => {
    changeEmail.mockResolvedValue({
      data: {
        email: "new@example.com",
        message: "Email changed successfully",
      },
    });

    render(<ChangeEmail />);

    fireEvent.change(screen.getByLabelText(/new email/i), {
      target: { value: "  new@example.com  " },
    });
    fireEvent.change(screen.getByLabelText(/current password/i), {
      target: { value: "secret-pass" },
    });
    fireEvent.click(screen.getByRole("button", { name: /update email/i }));

    await waitFor(() => {
      expect(changeEmail).toHaveBeenCalledWith({
        email: "new@example.com",
        current_password: "secret-pass",
      });
      expect(localStorage.getItem("email")).toBe("new@example.com");
      expect(toast.success).toHaveBeenCalledWith("Email changed successfully");
      expect(screen.getByLabelText(/current password/i)).toHaveValue("");
    });
  });

  test("shows fallback success message when backend message is missing", async () => {
    changeEmail.mockResolvedValue({
      data: {
        email: "fallback@example.com",
      },
    });

    render(<ChangeEmail />);

    fireEvent.change(screen.getByLabelText(/current password/i), {
      target: { value: "secret-pass" },
    });
    fireEvent.click(screen.getByRole("button", { name: /update email/i }));

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith("Email updated");
    });
  });

  test("shows backend email validation errors", async () => {
    changeEmail.mockRejectedValue({
      response: {
        data: {
          email: ["Enter a valid email address"],
        },
      },
    });

    render(<ChangeEmail />);

    fireEvent.change(screen.getByLabelText(/new email/i), {
      target: { value: "bad-email" },
    });
    fireEvent.change(screen.getByLabelText(/current password/i), {
      target: { value: "secret-pass" },
    });
    fireEvent.click(screen.getByRole("button", { name: /update email/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Enter a valid email address");
    });
  });

  test("shows fallback error message when backend error details are missing", async () => {
    changeEmail.mockRejectedValue(new Error("network"));

    render(<ChangeEmail />);

    fireEvent.change(screen.getByLabelText(/current password/i), {
      target: { value: "secret-pass" },
    });
    fireEvent.click(screen.getByRole("button", { name: /update email/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Unable to update email");
    });
  });
});
