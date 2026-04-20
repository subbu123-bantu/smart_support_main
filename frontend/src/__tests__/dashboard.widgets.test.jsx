import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import AgentWorkloadTable from "../components/dashboard/AgentWorkloadTable";
import ChartsSection from "../components/dashboard/ChartsSection";
import RecentTicketsSection from "../components/dashboard/RecentTicketsSection";
import StatsCards from "../components/dashboard/StatsCards";
import {
  AgentWorkloadTable as ExportedAgentWorkloadTable,
  ChartsSection as ExportedChartsSection,
  RecentTicketsSection as ExportedRecentTicketsSection,
  StatsCards as ExportedStatsCards,
} from "../components/dashboard";

jest.mock("recharts", () => ({
  ResponsiveContainer: ({ children }) => <div data-testid="responsive">{children}</div>,
  PieChart: ({ children }) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  LineChart: ({ children }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  CartesianGrid: () => <div data-testid="grid" />,
  BarChart: ({ children }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  Tooltip: () => <div data-testid="tooltip" />,
}));

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  Link: ({ to, children, ...props }) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

describe("dashboard widgets", () => {
  test("renders empty and populated agent workload states", () => {
    const { rerender } = render(<AgentWorkloadTable agentWorkload={[]} />);
    expect(screen.getByText("No agents found")).toBeInTheDocument();

    rerender(
      <AgentWorkloadTable
        agentWorkload={[
          {
            agent: "Asha",
            assigned: 4,
            in_progress: 1,
            solved: 3,
            avg_resolution_hours: 5,
          },
          {
            agent: "Ravi",
            assigned: 0,
            in_progress: 0,
            solved: 0,
            avg_resolution_hours: null,
          },
        ]}
      />,
    );

    expect(screen.getByText(/Asha/)).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("5h")).toBeInTheDocument();
  });

  test("renders chart widgets with transformed datasets", () => {
    render(
      <ChartsSection
        pieData={[{ name: "Open", value: 3 }]}
        lineData={[{ date: "Mon", count: 2 }]}
        categoryData={[{ name: "Billing", count: 5 }]}
        priorityData={[{ name: "high", count: 4 }]}
      />,
    );

    expect(screen.getByText("Status Breakdown")).toBeInTheDocument();
    expect(screen.getByText("Tickets Last 7 Days")).toBeInTheDocument();
    expect(screen.getByText("Tickets by Category")).toBeInTheDocument();
    expect(screen.getByText("Tickets by Priority")).toBeInTheDocument();
    expect(screen.getAllByTestId("responsive")).toHaveLength(4);
  });

  test("renders recent tickets loading, empty, and populated states", () => {
    const { rerender } = render(
      <MemoryRouter>
        <RecentTicketsSection loadingTickets recentTickets={[]} />
      </MemoryRouter>,
    );
    expect(screen.getByText("Loading...")).toBeInTheDocument();

    rerender(
      <MemoryRouter>
        <RecentTicketsSection loadingTickets={false} recentTickets={[]} />
      </MemoryRouter>,
    );
    expect(screen.getByText("No recent tickets")).toBeInTheDocument();

    rerender(
      <MemoryRouter>
        <RecentTicketsSection
          loadingTickets={false}
          recentTickets={[
            { id: 5, title: "VPN issue", priority: "urgent" },
            { id: 6, title: "Invoice", priority: "unknown" },
          ]}
        />
      </MemoryRouter>,
    );
    expect(screen.getByText("#5 VPN issue")).toBeInTheDocument();
    expect(screen.getByText("urgent")).toBeInTheDocument();
    expect(screen.getByText("unknown")).toBeInTheDocument();
  });

  test("renders stats cards and dashboard barrel exports", () => {
    render(
      <MemoryRouter>
        <StatsCards stats={{ total: 8, open: 2, in_progress: 3, closed: 3 }} loadingStats={false} />
      </MemoryRouter>,
    );

    expect(screen.getByText("Total Tickets")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
    expect(ExportedAgentWorkloadTable).toBe(AgentWorkloadTable);
    expect(ExportedChartsSection).toBe(ChartsSection);
    expect(ExportedRecentTicketsSection).toBe(RecentTicketsSection);
    expect(ExportedStatsCards).toBe(StatsCards);
  });
});
