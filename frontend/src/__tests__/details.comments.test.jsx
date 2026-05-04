import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { toast } from "react-toastify";
import TicketDetails from "../pages/TicketDetails";
import TicketComments from "../pages/TicketComments";
import {
  addTicketComment,
  deleteTicketComment,
  getTicketById,
  getTicketComments,
  getTicketPredictionFeedback,
} from "../services/api";

const mockNavigate = jest.fn();

jest.mock("react-toastify", () => ({ toast: { error: jest.fn(), success: jest.fn() } }));
jest.mock("../utils/logger", () => ({ error: jest.fn() }));
jest.mock("../services/api", () => ({
  getTicketById: jest.fn(),
  getTicketPredictionFeedback: jest.fn(),
  getTicketComments: jest.fn(),
  addTicketComment: jest.fn(),
  deleteTicketComment: jest.fn(),
}));
jest.mock("react-router-dom", () => ({ ...jest.requireActual("react-router-dom"), useNavigate: () => mockNavigate, useParams: () => ({ id: "42" }) }));

const ticketResponse = {
  id: 42,
  title: "Printer down",
  description: "Office printer is jammed",
  status: "open",
  priority: "high",
  category_name: "Hardware",
  assigned_to_name: "Alex",
};

const feedbackResponse = {
  has_feedback: true,
  predicted_category: "hardware",
  actual_category: "hardware",
  category_correct: true,
  predicted_priority: "high",
  actual_priority: "high",
  priority_correct: true,
  source: "ml_model",
  confidence: 0.93,
};

describe("ticket details and comments", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    localStorage.setItem("role", "admin");
    localStorage.setItem("username", "sam");
  });

  test("renders ticket details, feedback, and embedded comments", async () => {
    getTicketById.mockResolvedValue({ data: ticketResponse });
    getTicketPredictionFeedback.mockResolvedValue({ data: feedbackResponse });
    getTicketComments.mockResolvedValue({ data: [{ id: 1, username: "sam", user_role: "admin", message: "Investigating", created_at: "2026-04-28T00:00:00Z" }] });

    render(<TicketDetails />);

    expect(await screen.findByText(ticketResponse.title)).toBeInTheDocument();
    expect(screen.getByText(/office printer is jammed/i)).toBeInTheDocument();
    expect(screen.getAllByText("Correct")).toHaveLength(2);
    expect(screen.getByText("93%")).toBeInTheDocument();
    expect(await screen.findByText("Investigating")).toBeInTheDocument();
  });

  test("shows fallback when the ticket is missing", async () => {
    getTicketById.mockRejectedValueOnce(new Error("missing"));
    getTicketPredictionFeedback.mockRejectedValueOnce(new Error("none"));

    render(<TicketDetails />);

    expect(await screen.findByText(/ticket not found/i)).toBeInTheDocument();
    expect(screen.getByText(/this ticket may have been removed/i)).toBeInTheDocument();
  });

  test("posts internal notes and hides the checkbox for customers", async () => {
    getTicketComments
      .mockResolvedValue({ data: [] })
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce({ data: [{ id: 2, username: "sam", user_role: "admin", is_internal: true, message: "Secret", created_at: "2026-04-28T00:00:00Z" }] });
    addTicketComment.mockResolvedValue({});

    const { rerender } = render(<TicketComments ticketId={5} role="admin" />);

    expect(await screen.findByText(/no comments yet/i)).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText(/write a comment/i), { target: { value: "Secret" } });
    fireEvent.click(screen.getByLabelText(/mark as internal note/i));
    fireEvent.click(screen.getByRole("button", { name: /add comment/i }));

    await waitFor(() => expect(addTicketComment).toHaveBeenCalledWith(5, { message: "Secret", is_internal: true }));
    expect(toast.success).toHaveBeenCalledWith("Comment added");

    rerender(<TicketComments ticketId={5} role="customer" />);
    await waitFor(() => expect(screen.queryByLabelText(/mark as internal note/i)).not.toBeInTheDocument());
  });

  test("shows delete for allowed comments and refreshes after deletion", async () => {
    getTicketComments
      .mockResolvedValueOnce({
        data: [
          { id: 1, username: "sam", user_role: "admin", message: "Investigating", created_at: "2026-04-28T00:00:00Z" },
          { id: 2, username: "alex", user_role: "agent", message: "Agent note", created_at: "2026-04-28T01:00:00Z" },
        ],
      })
      .mockResolvedValueOnce({
        data: [
          { id: 2, username: "alex", user_role: "agent", message: "Agent note", created_at: "2026-04-28T01:00:00Z" },
        ],
      });
    deleteTicketComment.mockResolvedValue({});

    render(<TicketComments ticketId={5} role="admin" />);

    expect(await screen.findByText("Investigating")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: /delete/i })[0]);

    await waitFor(() => expect(deleteTicketComment).toHaveBeenCalledWith(5, 1));
    expect(toast.success).toHaveBeenCalledWith("Comment deleted");
    expect(await screen.findByText("Agent note")).toBeInTheDocument();
  });

  test("only shows delete for the current user's own comment when not admin", async () => {
    localStorage.setItem("username", "customer1");
    getTicketComments.mockResolvedValue({
      data: [
        { id: 1, username: "customer1", user_role: "customer", message: "Mine", created_at: "2026-04-28T00:00:00Z" },
        { id: 2, username: "someone-else", user_role: "customer", message: "Not mine", created_at: "2026-04-28T01:00:00Z" },
      ],
    });

    render(<TicketComments ticketId={5} role="customer" />);

    expect(await screen.findByText("Mine")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /delete/i })).toHaveLength(1);
  });

  test("shows ticket fallback values and no prediction feedback when data is partial", async () => {
    getTicketById.mockResolvedValue({ data: { id: 8, title: "Laptop", description: "Battery issue", status: "unknown", priority: "low", category: "", assigned_to_name: "" } });
    getTicketPredictionFeedback.mockResolvedValue({ data: { has_feedback: false } });

    render(<TicketDetails />);

    expect(await screen.findByText("Open")).toBeInTheDocument();
    expect(screen.getByText("Unassigned")).toBeInTheDocument();
    expect(screen.getByText(/no prediction feedback available/i)).toBeInTheDocument();
  });

  test("shows loading feedback first, then fallback markers and allows navigation", async () => {
    let resolveFeedback;
    getTicketById.mockResolvedValue({ data: { id: 10, title: "VPN", description: "Down", status: "closed", priority: "medium", category: "", assigned_to_name: "" } });
    getTicketPredictionFeedback.mockReturnValueOnce(new Promise((resolve) => {
      resolveFeedback = resolve;
    }));
    getTicketComments.mockResolvedValue({ data: [] });

    render(<TicketDetails />);

    expect(await screen.findByText("VPN")).toBeInTheDocument();
    expect(screen.getByText(/loading feedback/i)).toBeInTheDocument();

    await act(async () => {
      resolveFeedback({ data: { has_feedback: true, predicted_category: "", actual_category: "", category_correct: null, predicted_priority: "", actual_priority: "", priority_correct: null, source: "", confidence: 0 } });
    });

    await screen.findAllByText("Pending");
    expect(screen.getByText("0%")).toBeInTheDocument();
    fireEvent.click(screen.getByText(/back to tickets/i));
    expect(mockNavigate).toHaveBeenCalledWith("/tickets");
  });
});
