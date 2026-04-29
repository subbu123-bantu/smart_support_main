import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Dashboard from "../pages/Dashboard";
import { getTicketStats, getTickets } from "../services/api";

jest.mock("../services/api", () => ({ getTicketStats: jest.fn(), getTickets: jest.fn() }));
jest.mock("recharts", () => {
  const PropTypes = require("prop-types");
  const MockChart = (props) => <div>{props.children}</div>;
  const MockPrimitive = () => null;
  MockChart.propTypes = { children: PropTypes.node };
  return {
    ResponsiveContainer: MockChart,
    PieChart: MockChart,
    Pie: MockPrimitive,
    LineChart: MockChart,
    Line: MockPrimitive,
    BarChart: MockChart,
    Bar: MockPrimitive,
    XAxis: MockPrimitive,
    YAxis: MockPrimitive,
    Tooltip: MockPrimitive,
    CartesianGrid: MockPrimitive,
  };
});

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  localStorage.setItem("access", "token");
  localStorage.setItem("role", "admin");
});

test("dashboard maps stats data and shows admin sections", async () => {
  getTicketStats.mockResolvedValue({ data: { total: 8, open: 2, in_progress: 3, closed: 3, by_category: [{ category__name: "Billing", count: 3 }], by_priority: [{ priority: "high", count: 4 }], by_date: [{ date: "2026-04-28", count: 2 }], agent_workload: [{ agent: "A", assigned: 2, in_progress: 1, solved: 1, avg_resolution_hours: 4 }] } });
  getTickets.mockResolvedValue({ data: { results: [{ id: 1, title: "Printer", priority: "high" }, { id: 2, title: "VPN", priority: "low" }] } });
  render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><Dashboard /></MemoryRouter>);
  await waitFor(() => expect(screen.getByText("Total Tickets")).toBeInTheDocument());
  expect(screen.getByText("8")).toBeInTheDocument();
  expect(screen.getByText("Status Breakdown")).toBeInTheDocument();
  expect(screen.getByText("Tickets by Category")).toBeInTheDocument();
  expect(screen.getByText("Agent Workload")).toBeInTheDocument();
  expect(screen.getByText(/👤\s*A/)).toBeInTheDocument();
  expect(screen.getByText(/Printer/)).toBeInTheDocument();
});

test("dashboard skips recent ticket fetch for customers", async () => {
  localStorage.setItem("role", "customer");
  getTicketStats.mockResolvedValue({ data: {} });
  render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><Dashboard /></MemoryRouter>);
  await waitFor(() => expect(getTicketStats).toHaveBeenCalled());
  expect(getTickets).not.toHaveBeenCalled();
  expect(screen.queryByText("Status Breakdown")).not.toBeInTheDocument();
  expect(screen.getAllByText("0")).toHaveLength(4);
});

test("dashboard handles stats and recent ticket failures for agents", async () => {
  localStorage.setItem("role", "agent");
  getTicketStats.mockRejectedValueOnce(new Error("stats failed"));
  getTickets.mockRejectedValueOnce(new Error("tickets failed"));

  render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><Dashboard /></MemoryRouter>);

  await waitFor(() => expect(getTicketStats).toHaveBeenCalled());
  await waitFor(() => expect(getTickets).toHaveBeenCalledWith(1));
  expect(screen.queryByText("Agent Workload")).not.toBeInTheDocument();
  expect(screen.getAllByText("0")).toHaveLength(4);
});
