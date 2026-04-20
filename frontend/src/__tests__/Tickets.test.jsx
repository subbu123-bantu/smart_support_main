import "@testing-library/jest-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { toast } from "react-toastify";
import Tickets from "../pages/Tickets";
import {
  assignTicket,
  getAgents,
  getCategories,
  getTickets,
  updateTicket,
} from "../services/api";
import logger from "../utils/logger";

const mockNavigate = jest.fn();
let mockSearch = "";

jest.mock("../services/api", () => ({
  getTickets: jest.fn(),
  updateTicket: jest.fn(),
  getAgents: jest.fn(),
  assignTicket: jest.fn(),
  getCategories: jest.fn(),
}));

jest.mock("../utils/logger", () => ({
  __esModule: true,
  default: {
    error: jest.fn(),
  },
}));

jest.mock("react-toastify", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
  useSearchParams: () => [new URLSearchParams(mockSearch)],
}));

jest.mock("../components/TicketCard", () => {
  const MockTicketCard = ({ ticket, role, onFieldUpdate, onStatusUpdate, onAssign }) => (
    <div data-testid={`ticket-card-${ticket.id}`}>
      <span>{ticket.title}</span>
      <span>{role}</span>
      <button type="button" onClick={() => onFieldUpdate?.(ticket.id, { priority: "urgent" })}>
        field-update-{ticket.id}
      </button>
      <button type="button" onClick={() => onStatusUpdate?.(ticket.id, "closed")}>
        status-update-{ticket.id}
      </button>
      <button type="button" onClick={() => onAssign?.(ticket.id, "3")}>
        assign-{ticket.id}
      </button>
    </div>
  );

  MockTicketCard.propTypes = require("prop-types").shape;

  return MockTicketCard;
});

function renderPage() {
  return render(
    <MemoryRouter>
      <Tickets />
    </MemoryRouter>,
  );
}

const ticketResults = [
  { id: 1, title: "Printer issue" },
  { id: 2, title: "Login issue" },
];

describe("Tickets page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    mockSearch = "";
    getTickets.mockResolvedValue({
      data: {
        results: ticketResults,
        next: "next-page",
        previous: null,
      },
    });
    getAgents.mockResolvedValue({ data: [{ id: 3, username: "agent1" }] });
    getCategories.mockResolvedValue({ data: [{ id: 1, name: "Billing" }] });
  });

  test("loads admin ticket list with filters metadata", async () => {
    localStorage.setItem("role", "admin");

    renderPage();

    await waitFor(() => {
      expect(getTickets).toHaveBeenCalledWith(1, null, null, null, "", "");
      expect(getAgents).toHaveBeenCalled();
      expect(getCategories).toHaveBeenCalled();
      expect(screen.getByText("2 results")).toBeInTheDocument();
      expect(screen.getByText("Printer issue")).toBeInTheDocument();
      expect(screen.getByText("Login issue")).toBeInTheDocument();
    });
  });

  test("supports search and clear flow", async () => {
    localStorage.setItem("role", "admin");

    renderPage();

    await waitFor(() => expect(getTickets).toHaveBeenCalledTimes(1));

    fireEvent.change(screen.getByPlaceholderText(/search tickets/i), {
      target: { value: "router" },
    });
    fireEvent.click(screen.getByRole("button", { name: /search/i }));

    await waitFor(() => {
      expect(getTickets).toHaveBeenLastCalledWith(1, null, null, "router", "", "");
    });

    fireEvent.click(screen.getByRole("button", { name: /clear/i }));

    await waitFor(() => {
      expect(getTickets).toHaveBeenLastCalledWith(1, null, null, null, "", "");
    });
  });

  test("supports pagination and admin filters", async () => {
    localStorage.setItem("role", "admin");
    mockSearch = "status=open";

    renderPage();

    await waitFor(() => {
      expect(getTickets).toHaveBeenCalledWith(1, "open", null, null, "", "");
    });

    const selects = screen.getAllByRole("combobox");
    fireEvent.change(selects[0], { target: { value: "high" } });
    fireEvent.change(selects[1], { target: { value: "1" } });
    fireEvent.change(selects[2], { target: { value: "true" } });

    await waitFor(() => {
      expect(getTickets).toHaveBeenLastCalledWith(1, "open", "high", null, "true", "1");
    });

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    await waitFor(() => {
      expect(getTickets).toHaveBeenLastCalledWith(2, "open", "high", null, "true", "1");
    });
  });

  test("handles update and assign actions", async () => {
    localStorage.setItem("role", "admin");
    updateTicket.mockResolvedValue({ data: {} });
    assignTicket.mockResolvedValue({ data: {} });

    renderPage();

    await waitFor(() => expect(screen.getByText("Printer issue")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /field-update-1/i }));

    await waitFor(() => {
      expect(updateTicket).toHaveBeenCalledWith(1, { priority: "urgent" });
      expect(toast.success).toHaveBeenCalledWith("Updated");
    });

    fireEvent.click(screen.getByRole("button", { name: /status-update-1/i }));

    await waitFor(() => {
      expect(updateTicket).toHaveBeenCalledWith(1, { status: "closed" });
    });

    fireEvent.click(screen.getByRole("button", { name: /assign-1/i }));

    await waitFor(() => {
      expect(assignTicket).toHaveBeenCalledWith(1, "3");
      expect(toast.success).toHaveBeenCalledWith("Assigned");
    });
  });

  test("handles fetch and mutation failures", async () => {
    localStorage.setItem("role", "agent");
    getTickets.mockRejectedValueOnce(new Error("fetch failed"));
    updateTicket.mockRejectedValueOnce(new Error("update failed"));
    assignTicket.mockRejectedValueOnce(new Error("assign failed"));

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("No tickets found")).toBeInTheDocument();
      expect(logger.error).toHaveBeenCalled();
      expect(getAgents).not.toHaveBeenCalled();
      expect(getCategories).not.toHaveBeenCalled();
    });

    getTickets.mockResolvedValue({
      data: {
        results: [ticketResults[0]],
        next: null,
        previous: null,
      },
    });

    fireEvent.change(screen.getByPlaceholderText(/search tickets/i), {
      target: { value: "printer" },
    });
    fireEvent.click(screen.getByRole("button", { name: /search/i }));

    await waitFor(() => expect(screen.getByText("Printer issue")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /field-update-1/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Update failed");
    });

    fireEvent.click(screen.getByRole("button", { name: /assign-1/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Failed");
    });
  });

  test("navigates back to dashboard", async () => {
    localStorage.setItem("role", "customer");

    renderPage();

    await waitFor(() => expect(getTickets).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: /back to dashboard/i }));

    expect(mockNavigate).toHaveBeenCalledWith("/dashboard");
  });
});
