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
});
