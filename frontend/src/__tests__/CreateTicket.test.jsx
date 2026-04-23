import "@testing-library/jest-dom";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { toast } from "react-toastify";
import CreateTicket from "../pages/CreateTicket";
import { createTicket, predictTicket } from "../services/api";

const mockNavigate = jest.fn();

jest.mock("../services/api", () => ({
  createTicket: jest.fn(),
  predictTicket: jest.fn(),
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

describe("CreateTicket page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  function renderPage() {
    render(
      <MemoryRouter>
        <CreateTicket />
      </MemoryRouter>,
    );
  }

  function getForm() {
    return {
      title: screen.getByPlaceholderText(/brief summary of the issue/i),
      description: screen.getByPlaceholderText(/describe the issue in detail/i),
      submit: screen.getByRole("button", { name: /submit ticket/i }),
    };
  }

  function fillForm({
    title = "Printer issue",
    description = "The office printer is showing error code 500 and not printing.",
  } = {}) {
    const form = getForm();
    fireEvent.change(form.title, { target: { value: title } });
    fireEvent.change(form.description, { target: { value: description } });
  }

  test("shows validation error when title or description is missing", async () => {
    renderPage();
    fireEvent.click(getForm().submit);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Please fill in both fields");
      expect(createTicket).not.toHaveBeenCalled();
    });
  });

  test("does not trigger AI prediction for short descriptions", async () => {
    renderPage();
    fireEvent.change(getForm().description, { target: { value: "short" } });

    await act(async () => {
      jest.advanceTimersByTime(700);
    });

    expect(predictTicket).not.toHaveBeenCalled();
    expect(screen.getByText(/more characters for AI analysis/i)).toBeInTheDocument();
  });

  test("applies AI prediction results after debounce", async () => {
    predictTicket.mockResolvedValue({
      data: {
        predicted_category: "technical",
        predicted_priority: "high",
        category_confidence: 0.82,
        needs_manual_review: false,
      },
    });

    renderPage();
    fillForm();

    await act(async () => {
      jest.advanceTimersByTime(700);
    });

    await waitFor(() => {
      expect(predictTicket).toHaveBeenCalledWith({
        text: "The office printer is showing error code 500 and not printing.",
      });
      expect(screen.getByText("Technical")).toBeInTheDocument();
      expect(screen.getByText("High")).toBeInTheDocument();
      expect(screen.getByText("82%")).toBeInTheDocument();
    });
  });

  test("falls back to manual review when AI prediction fails", async () => {
    predictTicket.mockRejectedValue(new Error("prediction failed"));

    renderPage();
    fillForm();

    await act(async () => {
      jest.advanceTimersByTime(700);
    });

    await waitFor(() => {
      expect(predictTicket).toHaveBeenCalled();
      expect(screen.getByText("Other")).toBeInTheDocument();
      expect(screen.getByText("0%")).toBeInTheDocument();
      expect(screen.queryByText(/low confidence/i)).not.toBeInTheDocument();
    });
  });

  test("shows low-confidence manual review UI and prediction fallback defaults", async () => {
    predictTicket.mockResolvedValue({
      data: {
        predicted_category: "",
        predicted_priority: "",
        category_confidence: 0.4,
        needs_manual_review: true,
      },
    });

    renderPage();
    fillForm({
      description: "Need urgent help with a failing VPN client today.",
    });

    await act(async () => {
      jest.advanceTimersByTime(700);
    });

    await waitFor(() => {
      expect(screen.getAllByText("Other").length).toBeGreaterThan(0);
      expect(screen.getByText("40%")).toBeInTheDocument();
      expect(screen.getByText(/low confidence/i)).toBeInTheDocument();
    });
  });

  test("shows medium-confidence styling and generic fallback create error", async () => {
    predictTicket.mockResolvedValue({
      data: {
        predicted_category: "billing",
        predicted_priority: "medium",
        category_confidence: 0.65,
        needs_manual_review: false,
      },
    });

    renderPage();
    fillForm({
      title: "Billing mismatch",
      description: "The invoice total is wrong after the latest subscription update.",
    });

    await act(async () => {
      jest.advanceTimersByTime(700);
    });

    await waitFor(() => {
      expect(screen.getByText("65%")).toBeInTheDocument();
      expect(screen.getAllByText("Billing").length).toBeGreaterThan(0);
    });

    const confidenceBar = screen.getByText("Confidence").closest("div").nextSibling.firstChild;
    expect(confidenceBar).toHaveStyle({ background: "#f59e0b", width: "65%" });

    createTicket.mockRejectedValueOnce({});
    fireEvent.click(getForm().submit);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Failed to create ticket");
    });
  });

  test("submits a ticket successfully and redirects", async () => {
    createTicket.mockResolvedValue({ data: {} });
    renderPage();
    fillForm({
      title: " Login issue ",
      description: " Users cannot login after the latest deployment. ",
    });

    fireEvent.click(getForm().submit);

    await waitFor(() => {
      expect(createTicket).toHaveBeenCalledWith({
        title: "Login issue",
        description: "Users cannot login after the latest deployment.",
      });
      expect(toast.success).toHaveBeenCalledWith("Ticket submitted!");
      expect(mockNavigate).toHaveBeenCalledWith("/tickets");
    });
  });

  test("shows backend create-ticket errors", async () => {
    createTicket.mockRejectedValue({
      response: { data: { detail: "Failed to create ticket" } },
    });
    renderPage();
    fillForm();

    fireEvent.click(getForm().submit);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Failed to create ticket");
    });
  });

  test("shows category error fallback and prevents duplicate submission while pending", async () => {
    let resolveRequest;
    createTicket.mockReturnValue(
      new Promise((resolve) => {
        resolveRequest = resolve;
      }),
    );
    renderPage();
    fillForm();
    const form = getForm();

    fireEvent.click(form.submit);
    fireEvent.submit(form.submit.closest("form"));

    expect(createTicket).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: /submitting/i })).toBeDisabled();

    resolveRequest({ data: {} });
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith("/tickets"));
    await waitFor(() => expect(screen.getByRole("button", { name: /submit ticket/i })).toBeInTheDocument());

    createTicket.mockRejectedValueOnce({
      response: { data: { category: ["Choose a valid category"] } },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ticket/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Choose a valid category");
    });
  });
});
