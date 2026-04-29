import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { toast } from "react-toastify";
import Login from "../pages/Login";
import Register from "../pages/Register";
import ForgotPassword from "../pages/ForgotPassword";
import ResetPassword from "../pages/ResetPassword";
import ChangeEmail from "../pages/ChangeEmail";
import { changeEmail, loginUser, registerUser, requestPasswordReset, resetPassword } from "../services/api";

const mockNavigate = jest.fn();
let mockSearch = "";

jest.mock("react-toastify", () => ({ toast: { error: jest.fn(), success: jest.fn() } }));
jest.mock("../utils/logger", () => ({ __esModule: true, default: { error: jest.fn() } }));
jest.mock("../services/api", () => ({
  loginUser: jest.fn(),
  registerUser: jest.fn(),
  requestPasswordReset: jest.fn(),
  resetPassword: jest.fn(),
  changeEmail: jest.fn(),
}));
jest.mock("react-router-dom", () => {
  const PropTypes = require("prop-types");
  const MockLink = (props) => <a href={props.to}>{props.children}</a>;
  MockLink.propTypes = { children: PropTypes.node, to: PropTypes.string };
  return {
    ...jest.requireActual("react-router-dom"),
    Link: MockLink,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [new URLSearchParams(mockSearch)],
  };
});

const resetSession = () => {
  jest.clearAllMocks();
  localStorage.clear();
  mockSearch = "";
};

describe("auth pages", () => {
  beforeEach(resetSession);

  test("login validates fields, navigates, and handles network errors", async () => {
    loginUser.mockResolvedValue({ data: { user: { access: "t", role: "admin", username: "sam", email: "a@b.com" } } });

    render(<Login />);

    const loginForm = screen.getByLabelText(/username/i).closest("form");
    fireEvent.click(screen.getByRole("button", { name: /forgot password/i }));
    fireEvent.click(screen.getByRole("button", { name: /create one/i }));
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));
    expect(toast.error).toHaveBeenCalledWith("Please fill all fields");

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: "sam" } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: "pw" } });
    fireEvent.submit(loginForm);

    await waitFor(() => expect(loginUser).toHaveBeenCalledWith({ username: "sam", password: "pw" }));
    expect(localStorage.getItem("access")).toBe("t");
    expect(mockNavigate).toHaveBeenCalledWith("/dashboard");

    loginUser.mockRejectedValueOnce({ request: {} });
    fireEvent.submit(loginForm);
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith(expect.stringContaining("Cannot reach the backend")));
  });

  test("register blocks mismatched passwords and surfaces api errors", async () => {
    registerUser.mockResolvedValue({});

    render(<Register />);

    const registerForm = screen.getByLabelText(/^username/i).closest("form");
    fireEvent.change(screen.getByLabelText(/^username/i), { target: { value: "sam" } });
    fireEvent.change(screen.getByLabelText(/^email/i), { target: { value: "a@b.com" } });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: "pw1" } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: "pw2" } });
    fireEvent.submit(registerForm);

    expect(toast.error).toHaveBeenCalledWith("Passwords do not match");

    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: "pw1" } });
    expect(screen.getByText(/passwords match/i)).toBeInTheDocument();
    fireEvent.submit(registerForm);

    await waitFor(() => expect(registerUser).toHaveBeenCalledWith({ username: "sam", email: "a@b.com", password: "pw1" }));
    expect(mockNavigate).toHaveBeenCalledWith("/");

    registerUser.mockRejectedValueOnce({ response: { data: { email: ["Taken"] } } });
    fireEvent.submit(registerForm);
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Taken"));
  });

  test("forgot password trims email, redirects, and handles api errors", async () => {
    requestPasswordReset.mockResolvedValue({ data: { message: "sent" } });

    render(<ForgotPassword />);

    const forgotForm = screen.getByLabelText(/email/i).closest("form");
    fireEvent.click(screen.getByRole("button", { name: /back to sign in/i }));
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: " a@b.com " } });
    fireEvent.submit(forgotForm);

    await waitFor(() => expect(requestPasswordReset).toHaveBeenCalledWith({ email: "a@b.com" }));
    expect(mockNavigate).toHaveBeenCalledWith("/login");

    requestPasswordReset.mockRejectedValueOnce({ response: { data: { email: ["Unknown email"] } } });
    fireEvent.submit(forgotForm);
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Unknown email"));
  });

  test("reset password validates the link and handles submit branches", async () => {
    const firstRender = render(<ResetPassword />);
    fireEvent.submit(screen.getByRole("button", { name: /reset password/i }).closest("form"));
    expect(toast.error).toHaveBeenCalledWith("Reset link is invalid");
    firstRender.unmount();

    mockSearch = "uid=u1&token=t1";
    resetPassword.mockResolvedValue({ data: { message: "ok" } });

    render(<ResetPassword />);

    const resetForm = screen.getByLabelText(/new password/i).closest("form");
    fireEvent.click(screen.getByRole("button", { name: /request another/i }));
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: "pw" } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: "nope" } });
    fireEvent.submit(resetForm);

    expect(toast.error).toHaveBeenCalledWith("Passwords do not match");

    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: "pw" } });
    fireEvent.submit(resetForm);

    await waitFor(() => expect(resetPassword).toHaveBeenCalledWith({ uid: "u1", token: "t1", password: "pw", confirm_password: "pw" }));
    expect(mockNavigate).toHaveBeenCalledWith("/login");

    resetPassword.mockRejectedValueOnce({ response: { data: { error: "Expired" } } });
    fireEvent.submit(resetForm);
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Expired"));
  });

  test("change email reads storage, submits, and handles errors", async () => {
    localStorage.setItem("email", "old@x.com");
    changeEmail.mockResolvedValue({ data: { email: "new@x.com", message: "done" } });

    render(<ChangeEmail />);

    const emailForm = screen.getByLabelText(/new email/i).closest("form");
    expect(screen.getByLabelText(/new email/i)).toHaveValue("old@x.com");
    fireEvent.submit(emailForm);
    expect(toast.error).toHaveBeenCalledWith("Please fill all fields");

    fireEvent.change(screen.getByLabelText(/current password/i), { target: { value: "pw" } });
    fireEvent.submit(emailForm);

    await waitFor(() => expect(changeEmail).toHaveBeenCalledWith({ email: "old@x.com", current_password: "pw" }));
    expect(localStorage.getItem("email")).toBe("new@x.com");

    changeEmail.mockRejectedValueOnce({ response: { data: { error: "Bad password" } } });
    fireEvent.change(screen.getByLabelText(/current password/i), { target: { value: "pw" } });
    fireEvent.submit(emailForm);
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Bad password"));
  });
});
