import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { toast } from "react-toastify";
import CreateTicket from "../pages/CreateTicket";
import Tickets from "../pages/Tickets";
import { assignTicket, createTicket, getAgents, getCategories, getTickets, predictTicket, updateTicket } from "../services/api";

const mockNavigate = jest.fn();
let mockSearch = "";
let consoleErrorSpy;

jest.mock("react-toastify", () => ({ toast: { error: jest.fn(), success: jest.fn() } }));
jest.mock("../utils/logger", () => ({ error: jest.fn() }));
jest.mock("../services/api", () => ({
  createTicket: jest.fn(),
  predictTicket: jest.fn(),
  getTickets: jest.fn(),
  updateTicket: jest.fn(),
  getAgents: jest.fn(),
  assignTicket: jest.fn(),
  getCategories: jest.fn(),
}));
jest.mock("../components/TicketCard", () => {
  const PropTypes = require("prop-types");
  const MockTicketCard = (props) => (
    <div>
      <span>{props.ticket.title}</span>
      <button onClick={() => props.onStatusUpdate(props.ticket.id, "closed")}>status</button>
      <button onClick={() => props.onFieldUpdate(props.ticket.id, { priority: "high" })}>field</button>
      <button onClick={() => props.onAssign(props.ticket.id, "7")}>assign</button>
    </div>
  );
  MockTicketCard.propTypes = {
    ticket: PropTypes.shape({
      id: PropTypes.number.isRequired,
      title: PropTypes.string.isRequired,
    }).isRequired,
    onFieldUpdate: PropTypes.func.isRequired,
    onStatusUpdate: PropTypes.func.isRequired,
    onAssign: PropTypes.func.isRequired,
  };
  return MockTicketCard;
});
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

beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
  consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
  localStorage.clear();
  localStorage.setItem("role", "admin");
  mockSearch = "";
});

afterEach(() => {
  jest.useRealTimers();
  consoleErrorSpy.mockRestore();
});

test("create ticket auto-predicts and submits trimmed values", async () => {
  predictTicket.mockResolvedValue({ data: { predicted_category: "billing", predicted_priority: "urgent", category_confidence: 0.81 } });
  createTicket.mockResolvedValue({});
  render(<CreateTicket />);
  fireEvent.change(screen.getByPlaceholderText(/brief summary/i), { target: { value: " Broken login " } });
  fireEvent.change(screen.getByPlaceholderText(/describe the issue/i), { target: { value: "the login form keeps failing badly" } });
  act(() => {
    jest.runAllTimers();
  });
  await waitFor(() => expect(predictTicket).toHaveBeenCalledWith({ text: "the login form keeps failing badly" }));
  fireEvent.click(screen.getByRole("button", { name: /submit ticket/i }));
  await waitFor(() => expect(createTicket).toHaveBeenCalledWith({ title: "Broken login", description: "the login form keeps failing badly" }));
  expect(mockNavigate).toHaveBeenCalledWith("/tickets");
});

test("create ticket skips short predictions and handles prediction and submit failures", async () => {
  predictTicket
    .mockRejectedValueOnce(new Error("prediction failed"))
    .mockResolvedValueOnce({ data: { predicted_category: "other", predicted_priority: "low", category_confidence: 0.45, needs_manual_review: true } });
  createTicket.mockRejectedValueOnce({ response: { data: { category: ["Pick a valid category"] } } });
  render(<CreateTicket />);

  fireEvent.click(screen.getByRole("button", { name: /submit ticket/i }));
  expect(toast.error).toHaveBeenCalledWith("Please fill in both fields");

  fireEvent.change(screen.getByPlaceholderText(/brief summary/i), { target: { value: " Mail issue " } });
  fireEvent.change(screen.getByPlaceholderText(/describe the issue/i), { target: { value: "short" } });
  act(() => {
    jest.runAllTimers();
  });
  expect(predictTicket).not.toHaveBeenCalled();
  expect(screen.getByText(/5 more characters for ai analysis/i)).toBeInTheDocument();

  fireEvent.change(screen.getByPlaceholderText(/describe the issue/i), { target: { value: "mail routing keeps dropping replies" } });
  act(() => {
    jest.runAllTimers();
  });
  await waitFor(() => expect(predictTicket).toHaveBeenCalledWith({ text: "mail routing keeps dropping replies" }));

  fireEvent.change(screen.getByPlaceholderText(/describe the issue/i), { target: { value: "mail routing keeps dropping replies every morning" } });
  await act(async () => {
    jest.runAllTimers();
  });
  await waitFor(() => expect(predictTicket).toHaveBeenLastCalledWith({ text: "mail routing keeps dropping replies every morning" }));
  expect(await screen.findByText("45%")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /submit ticket/i }));
  await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Pick a valid category"));
});

test("tickets page loads admin filters and refreshes after actions", async () => {
  getTickets.mockResolvedValue({ data: { results: [{ id: 1, title: "Printer", status: "open", priority: "low", category: 1 }], next: "/2", previous: null } });
  getAgents.mockResolvedValue({ data: [{ id: 7, username: "Alex" }] });
  getCategories.mockResolvedValue({ data: [{ id: 2, name: "Billing" }] });
  updateTicket.mockResolvedValue({});
  assignTicket.mockResolvedValue({});
  render(<Tickets />);
  await waitFor(() => expect(getTickets).toHaveBeenCalledWith(1, null, null, null, "", ""));
  fireEvent.change(screen.getByPlaceholderText(/search tickets/i), { target: { value: "printer" } });
  fireEvent.click(screen.getByRole("button", { name: /^search$/i }));
  await waitFor(() => expect(getTickets).toHaveBeenLastCalledWith(1, null, null, "printer", "", ""));
  fireEvent.change(screen.getByDisplayValue("All Priority"), { target: { value: "high" } });
  fireEvent.change(screen.getByDisplayValue("All Categories"), { target: { value: "2" } });
  fireEvent.change(screen.getByDisplayValue("All"), { target: { value: "true" } });
  await waitFor(() => expect(getTickets).toHaveBeenLastCalledWith(1, null, "high", "printer", "true", "2"));
  fireEvent.click(await screen.findByText("status"));
  fireEvent.click(screen.getByText("field"));
  fireEvent.click(screen.getByText("assign"));
  await waitFor(() => expect(updateTicket).toHaveBeenCalled());
  expect(assignTicket).toHaveBeenCalledWith(1, "7");
  expect(toast.success).toHaveBeenCalled();
});

test("tickets page handles loading, pagination, empty states, errors, and non-admin users", async () => {
  let resolveTickets;
  getTickets.mockReturnValueOnce(new Promise((resolve) => {
    resolveTickets = resolve;
  }));
  getAgents.mockRejectedValueOnce(new Error("agents failed"));
  getCategories.mockRejectedValueOnce(new Error("categories failed"));
  const view = render(<Tickets />);
  expect(await screen.findByText(/loading/i)).toBeInTheDocument();

  resolveTickets({ data: { results: [], next: "/2", previous: null } });
  expect(await screen.findByText(/no tickets found/i)).toBeInTheDocument();

  getTickets.mockResolvedValueOnce({ data: { results: [{ id: 2, title: "Router", status: "open", priority: "medium", category: 1 }], next: "/3", previous: "/1" } });
  fireEvent.click(screen.getByText(/next/i));
  await waitFor(() => expect(getTickets).toHaveBeenLastCalledWith(2, null, null, null, "", ""));
  expect(await screen.findByText("Page 2")).toBeInTheDocument();

  getTickets.mockRejectedValueOnce(new Error("fetch failed"));
  fireEvent.click(screen.getByText(/next/i));
  expect(await screen.findByText(/no tickets found/i)).toBeInTheDocument();

  mockNavigate.mockClear();
  view.unmount();
  localStorage.setItem("role", "customer");
  getTickets.mockResolvedValueOnce({ data: { results: [{ id: 9, title: "Customer Ticket", status: "open", priority: "low", category: 1 }], next: null, previous: null } });
  render(<Tickets />);
  await waitFor(() => expect(getTickets).toHaveBeenLastCalledWith(1, null, null, null, "", null));
  fireEvent.click(screen.getByText(/back to dashboard/i));
  expect(mockNavigate).toHaveBeenCalledWith("/dashboard");
  expect(screen.queryByDisplayValue("All Categories")).not.toBeInTheDocument();
});

test("tickets page clears searches and surfaces update and assignment failures", async () => {
  getTickets.mockResolvedValue({ data: { results: [{ id: 5, title: "Switch", status: "open", priority: "low", category: 1 }], next: "/2", previous: null } });
  getAgents.mockResolvedValue({ data: [{ id: 7, username: "Alex" }] });
  getCategories.mockResolvedValue({ data: { results: [{ id: 1, name: "Network" }] } });
  updateTicket.mockRejectedValueOnce(new Error("update failed")).mockRejectedValueOnce(new Error("field failed"));
  assignTicket.mockRejectedValueOnce(new Error("assign failed"));

  render(<Tickets />);

  await waitFor(() => expect(getTickets).toHaveBeenCalledWith(1, null, null, null, "", ""));
  fireEvent.change(screen.getByPlaceholderText(/search tickets/i), { target: { value: "switch" } });
  fireEvent.click(screen.getByRole("button", { name: /^search$/i }));
  await waitFor(() => expect(getTickets).toHaveBeenLastCalledWith(1, null, null, "switch", "", ""));
  expect(screen.queryByText(/next/i)).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /clear/i }));
  await waitFor(() => expect(getTickets).toHaveBeenLastCalledWith(1, null, null, null, "", ""));
  expect(screen.getByText(/next/i)).toBeInTheDocument();

  fireEvent.click(await screen.findByText("status"));
  fireEvent.click(screen.getByText("field"));
  fireEvent.click(screen.getByText("assign"));

  await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Failed to update"));
  expect(toast.error).toHaveBeenCalledWith("Update failed");
  expect(toast.error).toHaveBeenCalledWith("Failed");
});
