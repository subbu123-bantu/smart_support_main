import "@testing-library/jest-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { toast } from "react-toastify";
import TicketComments from "../pages/TicketComments";
import TicketDetails from "../pages/TicketDetails";
import {
  addTicketComment,
  getTicketById,
  getTicketComments,
  getTicketPredictionFeedback,
} from "../services/api";
import logger from "../utils/logger";

const mockNavigate = jest.fn();

jest.mock("../services/api", () => ({
  getTicketComments: jest.fn(),
  addTicketComment: jest.fn(),
  getTicketById: jest.fn(),
  getTicketPredictionFeedback: jest.fn(),
}));

jest.mock("../utils/logger", () => ({
  __esModule: true,
  default: {
    error: jest.fn(),
  },
}));

jest.mock("react-toastify", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

jest.mock("../components/FeedBackCard", () => ({ title, children }) => (
  <div data-testid="feedback-card">
    <h4>{title}</h4>
    {children}
  </div>
));

jest.mock("../components/EvaluationBadge", () => ({ value }) => (
  <span data-testid="evaluation-badge">{String(value)}</span>
));

jest.mock("lucide-react", () => ({
  ArrowLeft: () => <span data-testid="arrow-left" />,
  Tag: () => <span data-testid="tag-icon" />,
  AlertCircle: () => <span data-testid="alert-icon" />,
  Clock: () => <span data-testid="clock-icon" />,
}));

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
  useParams: () => ({ id: "12" }),
}));

describe("ticket comments and details pages", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test("loads comments, supports internal notes, and refreshes after posting", async () => {
    getTicketComments
      .mockResolvedValueOnce({
        data: {
          results: [
            {
              id: 1,
              username: "Agent One",
              user_role: "agent",
              is_internal: true,
              created_at: "2026-04-20T08:00:00Z",
              message: "Investigating issue",
            },
          ],
        },
      })
      .mockResolvedValueOnce({
        data: [
          {
            id: 2,
            username: "Agent One",
            user_role: "agent",
            is_internal: false,
            created_at: "2026-04-20T09:00:00Z",
            message: "Resolved",
          },
        ],
      });
    addTicketComment.mockResolvedValue({});

    render(<TicketComments ticketId={12} role="agent" />);

    expect(screen.getByText("Loading comments...")).toBeInTheDocument();
    expect(await screen.findByText("Investigating issue")).toBeInTheDocument();
    expect(screen.getByText("Internal")).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText("Write a comment..."), {
      target: { value: "Resolved" },
    });
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "Add Comment" }));

    await waitFor(() =>
      expect(addTicketComment).toHaveBeenCalledWith(12, {
        message: "Resolved",
        is_internal: true,
      }),
    );
    expect(await screen.findByText("Resolved")).toBeInTheDocument();
    expect(toast.success).toHaveBeenCalledWith("Comment added");
  });

  test("handles comments validation and failure states", async () => {
    getTicketComments.mockRejectedValueOnce(new Error("load failed"));
    addTicketComment.mockRejectedValueOnce(new Error("save failed"));

    render(<TicketComments ticketId={99} role="customer" />);

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Failed to load comments"));
    expect(logger.error).toHaveBeenCalled();
    expect(screen.getByText("No comments yet")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Add Comment" }));
    expect(toast.error).toHaveBeenCalledWith("Comment cannot be empty");

    fireEvent.change(screen.getByPlaceholderText("Write a comment..."), {
      target: { value: "Need update" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add Comment" }));

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Failed to add comment"));
  });

  test("renders ticket details, prediction feedback, and back navigation", async () => {
    localStorage.setItem("role", "admin");
    getTicketById.mockResolvedValueOnce({
      data: {
        id: 12,
        title: "VPN issue",
        description: "Cannot connect",
        status: "closed",
        priority: "high",
        category_name: "Technical",
        assigned_to_name: "Asha",
      },
    });
    getTicketPredictionFeedback.mockResolvedValueOnce({
      data: {
        has_feedback: true,
        predicted_category: "technical",
        actual_category: "technical",
        category_correct: true,
        predicted_priority: "high",
        actual_priority: "high",
        priority_correct: true,
        source: "ai_prediction",
        confidence: 0.81,
      },
    });
    getTicketComments.mockResolvedValue({ data: [] });

    render(
      <MemoryRouter>
        <TicketDetails />
      </MemoryRouter>,
    );

    expect(screen.getByText("Loading ticket...")).toBeInTheDocument();
    expect(await screen.findByText("VPN issue")).toBeInTheDocument();
    expect(screen.getByText("Cannot connect")).toBeInTheDocument();
    expect(screen.getByText("Asha")).toBeInTheDocument();
    expect(await screen.findByText("AI Prediction Feedback")).toBeInTheDocument();
    expect(screen.getByText("81%")).toBeInTheDocument();
    expect(screen.getByText("ai prediction")).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole("button", { name: /back to tickets/i })[0]);
    expect(mockNavigate).toHaveBeenCalledWith("/tickets");
  });

  test("renders missing ticket and no-feedback fallback states", async () => {
    getTicketById.mockRejectedValueOnce(new Error("missing"));
    getTicketPredictionFeedback.mockRejectedValueOnce(new Error("no feedback"));

    render(
      <MemoryRouter>
        <TicketDetails />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Ticket not found")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /back to tickets/i }));
    expect(mockNavigate).toHaveBeenCalledWith("/tickets");
  });
});
