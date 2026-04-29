import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { toast } from "react-toastify";
import TicketDetails from "../pages/TicketDetails";
import TicketComments from "../pages/TicketComments";
import { addTicketComment, getTicketById, getTicketComments, getTicketPredictionFeedback } from "../services/api";

const mockNavigate = jest.fn();

jest.mock("react-toastify", () => ({ toast: { error: jest.fn(), success: jest.fn() } }));
jest.mock("../utils/logger", () => ({ error: jest.fn() }));
jest.mock("../services/api", () => ({
  getTicketById: jest.fn(),
  getTicketPredictionFeedback: jest.fn(),
  getTicketComments: jest.fn(),
  addTicketComment: jest.fn(),
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
  });

  test("renders ticket details, feedback, and embedded comments", async () => {
    getTicketById.mockResolvedValue({ data: ticketResponse });
    getTicketPredictionFeedback.mockResolvedValue({ data: feedbackResponse });
    getTicketComments.mockResolvedValue({ data: [{ id: 1, username: "sam", user_role: "admin", message: "Investigating", created_at: "2026-04-28T00:00:00Z" }] });

    render(<TicketDetails />);

    await waitFor(() => expect(screen.getByText(ticketResponse.title)).toBeInTheDocument());
    expect(screen.getByText(/office printer is jammed/i)).toBeInTheDocument();
    expect(screen.getAllByText("Correct")).toHaveLength(2);
    expect(screen.getByText("93%")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Investigating")).toBeInTheDocument());
  });

  test("shows fallback when the ticket is missing", async () => {
    getTicketById.mockRejectedValueOnce(new Error("missing"));
    getTicketPredictionFeedback.mockRejectedValueOnce(new Error("none"));

    render(<TicketDetails />);

    await waitFor(() => expect(screen.getByText(/ticket not found/i)).toBeInTheDocument());
    expect(screen.getByText(/this ticket may have been removed/i)).toBeInTheDocument();
  });

  test("posts internal notes and hides the checkbox for customers", async () => {
    getTicketComments
      .mockResolvedValue({ data: [] })
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce({ data: [{ id: 2, username: "sam", user_role: "admin", is_internal: true, message: "Secret", created_at: "2026-04-28T00:00:00Z" }] });
    addTicketComment.mockResolvedValue({});

    const { rerender } = render(<TicketComments ticketId={5} role="admin" />);

    await waitFor(() => expect(screen.getByText(/no comments yet/i)).toBeInTheDocument());
    fireEvent.change(screen.getByPlaceholderText(/write a comment/i), { target: { value: "Secret" } });
    fireEvent.click(screen.getByLabelText(/mark as internal note/i));
    fireEvent.submit(screen.getByRole("button", { name: /add comment/i }).closest("form"));

    await waitFor(() => expect(addTicketComment).toHaveBeenCalledWith(5, { message: "Secret", is_internal: true }));
    expect(toast.success).toHaveBeenCalledWith("Comment added");

    rerender(<TicketComments ticketId={5} role="customer" />);
    await waitFor(() => expect(screen.queryByLabelText(/mark as internal note/i)).not.toBeInTheDocument());
  });

  test("shows ticket fallback values and no prediction feedback when data is partial", async () => {
    getTicketById.mockResolvedValue({ data: { id: 8, title: "Laptop", description: "Battery issue", status: "unknown", priority: "low", category: "", assigned_to_name: "" } });
    getTicketPredictionFeedback.mockResolvedValue({ data: { has_feedback: false } });

    render(<TicketDetails />);

    await waitFor(() => expect(screen.getByText("Open")).toBeInTheDocument());
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

    await waitFor(() => expect(screen.getByText("VPN")).toBeInTheDocument());
    expect(screen.getByText(/loading feedback/i)).toBeInTheDocument();

    await act(async () => {
      resolveFeedback({ data: { has_feedback: true, predicted_category: "", actual_category: "", category_correct: null, predicted_priority: "", actual_priority: "", priority_correct: null, source: "", confidence: 0 } });
    });

    await waitFor(() => expect(screen.getAllByText("Pending")).toHaveLength(2));
    expect(screen.getByText("0%")).toBeInTheDocument();
    fireEvent.click(screen.getByText(/back to tickets/i));
    expect(mockNavigate).toHaveBeenCalledWith("/tickets");
  });
});
