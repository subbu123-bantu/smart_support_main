import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
import Dashboard from "../pages/Dashboard";
import { getTicketStats, getTickets } from "../services/api";

jest.mock("../services/api", () => ({
  getTicketStats: jest.fn(),
  getTickets: jest.fn(),
}));

jest.mock("../components/dashboard/StatsCards", () => {
  const PropTypes = require("prop-types");

  const MockStatsCards = ({ stats, loadingStats }) => (
    <div data-testid="stats-cards">
      stats:{stats.total}|loading:{String(loadingStats)}
    </div>
  );

  MockStatsCards.propTypes = {
    stats: PropTypes.shape({
      total: PropTypes.number,
    }).isRequired,
    loadingStats: PropTypes.bool.isRequired,
  };

  return MockStatsCards;
});

jest.mock("../components/dashboard/ChartsSection", () => {
  const PropTypes = require("prop-types");

  const MockChartsSection = ({ pieData, lineData, categoryData, priorityData }) => (
    <div data-testid="charts-section">
      pie:{pieData.length}|line:{lineData.length}|category:{categoryData.length}|priority:{priorityData.length}
      |category-names:{categoryData.map((item) => item.name).join(",")}
      |priority-names:{priorityData.map((item) => item.name).join(",")}
      |line-dates:{lineData.map((item) => item.date).join(",")}
    </div>
  );

  MockChartsSection.propTypes = {
    pieData: PropTypes.array.isRequired,
    lineData: PropTypes.array.isRequired,
    categoryData: PropTypes.array.isRequired,
    priorityData: PropTypes.array.isRequired,
  };

  return MockChartsSection;
});

jest.mock("../components/dashboard/AgentWorkloadTable", () => {
  const PropTypes = require("prop-types");

  const MockAgentWorkloadTable = ({ agentWorkload }) => (
    <div data-testid="agent-workload">agents:{agentWorkload.length}</div>
  );

  MockAgentWorkloadTable.propTypes = {
    agentWorkload: PropTypes.array.isRequired,
  };

  return MockAgentWorkloadTable;
});

jest.mock("../components/dashboard/RecentTicketsSection", () => {
  const PropTypes = require("prop-types");

  const MockRecentTicketsSection = ({ loadingTickets, recentTickets }) => (
    <div data-testid="recent-tickets">
      loading:{String(loadingTickets)}|count:{recentTickets.length}
    </div>
  );

  MockRecentTicketsSection.propTypes = {
    loadingTickets: PropTypes.bool.isRequired,
    recentTickets: PropTypes.array.isRequired,
  };

  return MockRecentTicketsSection;
});

describe("Dashboard", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    localStorage.setItem("access", "token-123");
  });

  test("renders admin dashboard data from stats and tickets APIs", async () => {
    localStorage.setItem("role", "admin");
    getTicketStats.mockResolvedValue({
      data: {
        total: 12,
        open: 4,
        in_progress: 5,
        closed: 3,
        by_category: [{ category__name: "Billing", count: 2 }],
        by_priority: [{ priority: "high", count: 3 }],
        by_date: [{ date: "2026-04-20", count: 4 }],
        agent_workload: [{ username: "agent1", assigned_count: 2 }],
      },
    });
    getTickets.mockResolvedValue({
      data: {
        results: [{ id: 1, title: "Issue 1" }, { id: 2, title: "Issue 2" }],
      },
    });

    render(<Dashboard />);

    await waitFor(() => {
      expect(getTicketStats).toHaveBeenCalled();
      expect(getTickets).toHaveBeenCalledWith(1);
      expect(screen.getByTestId("stats-cards")).toHaveTextContent("stats:12|loading:false");
      expect(screen.getByTestId("charts-section")).toHaveTextContent("pie:3|line:1|category:1|priority:1");
      expect(screen.getByTestId("agent-workload")).toHaveTextContent("agents:1");
      expect(screen.getByTestId("recent-tickets")).toHaveTextContent("loading:false|count:2");
    });
  });

  test("renders customer dashboard without admin-only sections", async () => {
    localStorage.setItem("role", "customer");
    getTicketStats.mockRejectedValue(new Error("stats failed"));

    render(<Dashboard />);

    await waitFor(() => {
      expect(getTicketStats).toHaveBeenCalled();
      expect(getTickets).not.toHaveBeenCalled();
      expect(screen.getByTestId("stats-cards")).toHaveTextContent("stats:0|loading:false");
      expect(screen.queryByTestId("charts-section")).not.toBeInTheDocument();
      expect(screen.queryByTestId("agent-workload")).not.toBeInTheDocument();
      expect(screen.queryByTestId("recent-tickets")).not.toBeInTheDocument();
    });
  });

  test("renders agent recent tickets and handles ticket fetch failures", async () => {
    localStorage.setItem("role", "agent");
    getTicketStats.mockResolvedValue({ data: {} });
    getTickets.mockRejectedValue(new Error("tickets failed"));

    render(<Dashboard />);

    await waitFor(() => {
      expect(getTickets).toHaveBeenCalledWith(1);
      expect(screen.getByTestId("recent-tickets")).toHaveTextContent("loading:false|count:0");
      expect(screen.queryByTestId("charts-section")).not.toBeInTheDocument();
    });
  });

  test("skips stats fetch without an auth token and falls back missing admin data", async () => {
    localStorage.setItem("role", "admin");
    localStorage.removeItem("access");

    getTickets.mockResolvedValue({ data: {} });

    render(<Dashboard />);

    await waitFor(() => {
      expect(getTicketStats).not.toHaveBeenCalled();
      expect(getTickets).toHaveBeenCalledWith(1);
      expect(screen.getByTestId("stats-cards")).toHaveTextContent("stats:0|loading:true");
      expect(screen.getByTestId("charts-section")).toHaveTextContent("pie:3|line:0|category:0|priority:0");
      expect(screen.getByTestId("agent-workload")).toHaveTextContent("agents:0");
      expect(screen.getByTestId("recent-tickets")).toHaveTextContent("loading:false|count:0");
    });
  });

  test("uses fallback chart values when stats payload fields are missing", async () => {
    localStorage.setItem("role", "admin");
    getTicketStats.mockResolvedValue({
      data: {
        total: 3,
        open: null,
        in_progress: undefined,
        closed: 2,
        by_category: [{ category__name: "", count: null }],
        by_priority: [{ priority: "", count: null }],
        by_date: [{ date: null, count: null }],
        agent_workload: null,
      },
    });
    getTickets.mockResolvedValue({ data: { results: [] } });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByTestId("stats-cards")).toHaveTextContent("stats:3|loading:false");
      expect(screen.getByTestId("charts-section")).toHaveTextContent("category-names:Unknown");
      expect(screen.getByTestId("charts-section")).toHaveTextContent("priority-names:unknown");
      expect(screen.getByTestId("charts-section")).toHaveTextContent("line-dates:");
      expect(screen.getByTestId("agent-workload")).toHaveTextContent("agents:0");
    });
  });
});
