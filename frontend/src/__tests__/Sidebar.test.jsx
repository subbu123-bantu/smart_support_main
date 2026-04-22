import "@testing-library/jest-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import API from "../services/api";
import logger from "../utils/logger";

jest.mock("../services/api", () => ({
  __esModule: true,
  default: {
    post: jest.fn(),
  },
}));

jest.mock("../utils/logger", () => ({
  __esModule: true,
  default: {
    error: jest.fn(),
  },
}));

describe("Sidebar", () => {
  let originalLocation;

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    localStorage.setItem("username", "Subbu");

    originalLocation = globalThis.location;
    delete globalThis.location;
    globalThis.location = { href: "http://localhost/" };
  });

  afterEach(() => {
    globalThis.location = originalLocation;
  });

  test("shows customer links and toggles collapsed navigation", () => {
    localStorage.setItem("role", "customer");

    const { container } = render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );

    expect(screen.getByText("My Tickets")).toBeInTheDocument();
    expect(screen.getByText("Create Ticket")).toBeInTheDocument();
    expect(screen.queryByText(/^Tickets$/)).not.toBeInTheDocument();
    expect(container.firstChild).toHaveClass("w-60");

    fireEvent.click(screen.getByRole("button", { name: "" }));

    expect(screen.queryByText("My Tickets")).not.toBeInTheDocument();
    expect(screen.queryByText("Sign out")).not.toBeInTheDocument();
    expect(container.firstChild).toHaveClass("w-[68px]");
  });

  test("shows admin navigation and logs out successfully", async () => {
    localStorage.setItem("role", "admin");
    localStorage.setItem("access", "token-123");
    API.post.mockResolvedValue({ data: { message: "ok" } });

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Tickets")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /sign out/i }));

    await waitFor(() => {
      expect(API.post).toHaveBeenCalledWith("logout/");
      expect(localStorage.getItem("access")).toBeNull();
      expect(localStorage.getItem("role")).toBeNull();
      expect(localStorage.getItem("username")).toBeNull();
      expect(globalThis.location.href).toBe("/login");
    });
  });

  test("still clears auth state when logout request fails", async () => {
    localStorage.setItem("role", "agent");
    localStorage.setItem("access", "token-123");
    API.post.mockRejectedValue(new Error("logout failed"));

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: /sign out/i }));

    await waitFor(() => {
      expect(logger.error).toHaveBeenCalled();
      expect(globalThis.location.href).toBe("/login");
    });
  });

  test("falls back to default user metadata when storage is empty", () => {
    localStorage.clear();

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );

    expect(screen.getByText("User")).toBeInTheDocument();
    expect(screen.getByText("customer")).toBeInTheDocument();
  });

  test("uses active nav styling for the current route", () => {
    localStorage.setItem("role", "customer");

    render(
      <MemoryRouter initialEntries={["/create-ticket"]}>
        <Sidebar />
      </MemoryRouter>,
    );

    const activeLink = screen.getByRole("link", { name: /create ticket/i });
    expect(activeLink).toHaveClass("bg-indigo-600");
  });

  test("uses fallback role colors for unknown roles", () => {
    localStorage.setItem("role", "manager");
    localStorage.setItem("username", "Morgan");

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );

    expect(screen.getByText("manager")).toHaveClass("bg-emerald-500/20");
  });
});
