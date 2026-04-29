import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PriorityBadge from "../components/PriorityBadge";
import StatusBadge from "../components/StatusBadge";
import AgentWorkloadTable from "../components/dashboard/AgentWorkloadTable";
import ChartsSection from "../components/dashboard/ChartsSection";
import StatsCards from "../components/dashboard/StatsCards";
import { CATEGORY_META, PRIORITY_META, STATUS_META } from "../constants";
import {
  AgentWorkloadTable as AgentWorkloadTableExport,
  ChartsSection as ChartsSectionExport,
  RecentTicketsSection as RecentTicketsSectionExport,
  StatsCards as StatsCardsExport,
} from "../components/dashboard";

jest.mock("recharts", () => {
  const PropTypes = require("prop-types");

  const createChart = (testId) => {
    const Chart = ({ children, data }) => (
      <div data-testid={testId} data-chart={JSON.stringify(data || [])}>
        {children}
      </div>
    );
    Chart.propTypes = {
      children: PropTypes.node,
      data: PropTypes.array,
    };
    return Chart;
  };

  const Primitive = ({ data, label }) => (
    <div
      data-testid="chart-primitive"
      data-chart={JSON.stringify(data || [])}
      data-label={typeof label === "function" ? label({ name: "Open", percent: 0.5 }) : ""}
    />
  );
  Primitive.propTypes = {
    data: PropTypes.array,
    label: PropTypes.oneOfType([PropTypes.func, PropTypes.bool]),
  };

  return {
    ResponsiveContainer: createChart("responsive-container"),
    PieChart: createChart("pie-chart"),
    LineChart: createChart("line-chart"),
    BarChart: createChart("bar-chart"),
    Pie: Primitive,
    Line: Primitive,
    Bar: Primitive,
    XAxis: Primitive,
    YAxis: Primitive,
    Tooltip: Primitive,
    CartesianGrid: Primitive,
  };
});

const routerFuture = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
};

describe("dashboard helper components", () => {
  test("badge components fall back to default metadata for unknown values", () => {
    render(
      <>
        <PriorityBadge priority="not-real" />
        <StatusBadge status="not-real" />
      </>
    );

    expect(screen.getByText(PRIORITY_META.low.label)).toBeInTheDocument();
    expect(screen.getByText(STATUS_META.open.label)).toBeInTheDocument();
  });

  test("stats cards render loading state and exported barrel modules stay wired correctly", () => {
    expect(StatsCardsExport).toBe(StatsCards);
    expect(ChartsSectionExport).toBe(ChartsSection);
    expect(AgentWorkloadTableExport).toBe(AgentWorkloadTable);
    expect(RecentTicketsSectionExport).toBeDefined();
    expect(CATEGORY_META).toBeDefined();
    expect(PRIORITY_META.high.label).toBe("High");
    expect(STATUS_META.closed.label).toBe("Closed");

    render(
      <MemoryRouter future={routerFuture}>
        <StatsCards stats={{ total: 12, open: 3, in_progress: 4, closed: 5 }} loadingStats />
      </MemoryRouter>
    );

    expect(screen.getAllByText("...")).toHaveLength(4);
    expect(screen.getByRole("link", { name: /total tickets/i })).toHaveAttribute("href", "/tickets");
    expect(screen.getByRole("link", { name: /open/i })).toHaveAttribute("href", "/tickets?status=open");
  });

  test("agent workload table covers empty and populated states", () => {
    const emptyRender = render(<AgentWorkloadTable agentWorkload={[]} />);
    expect(screen.getByText("No agents found")).toBeInTheDocument();
    emptyRender.unmount();

    render(
      <AgentWorkloadTable
        agentWorkload={[
          {
            agent: "alex",
            assigned: 0,
            in_progress: 0,
            solved: 0,
            avg_resolution_hours: null,
          },
          {
            agent: "sam",
            assigned: 4,
            in_progress: 1,
            solved: 3,
            avg_resolution_hours: 2.5,
          },
        ]}
      />
    );

    expect(screen.getByText(/alex/i)).toBeInTheDocument();
    expect(screen.getByText("0%")).toBeInTheDocument();
    expect(screen.getByText("2.5h")).toBeInTheDocument();
  });

  test("charts section maps fallback colors and label formatting", () => {
    render(
      <ChartsSection
        pieData={[
          { name: "Open", value: 2 },
          { name: "Unknown", value: 1 },
        ]}
        lineData={[{ date: "2026-04-29", count: 3 }]}
        categoryData={Array.from({ length: 7 }, (_, index) => ({
          name: `Category ${index + 1}`,
          count: index + 1,
        }))}
        priorityData={[
          { name: "urgent", count: 4 },
          { name: "unknown", count: 1 },
        ]}
      />
    );

    expect(screen.getByText("Status Breakdown")).toBeInTheDocument();
    expect(screen.getByText("Tickets by Priority")).toBeInTheDocument();

    const piePrimitive = screen.getAllByTestId("chart-primitive")[0];
    expect(piePrimitive).toHaveAttribute(
      "data-chart",
      JSON.stringify([
        { name: "Open", value: 2, fill: "#ef4444" },
        { name: "Unknown", value: 1, fill: "#6366f1" },
      ])
    );
    expect(piePrimitive).toHaveAttribute("data-label", "Open 50%");

    const barCharts = screen.getAllByTestId("bar-chart");
    expect(barCharts[0]).toHaveAttribute(
      "data-chart",
      JSON.stringify([
        { name: "Category 1", count: 1, fill: "#6366f1" },
        { name: "Category 2", count: 2, fill: "#f59e0b" },
        { name: "Category 3", count: 3, fill: "#22c55e" },
        { name: "Category 4", count: 4, fill: "#ef4444" },
        { name: "Category 5", count: 5, fill: "#8b5cf6" },
        { name: "Category 6", count: 6, fill: "#06b6d4" },
        { name: "Category 7", count: 7, fill: "#6366f1" },
      ])
    );
    expect(barCharts[1]).toHaveAttribute(
      "data-chart",
      JSON.stringify([
        { name: "urgent", count: 4, fill: "#7c3aed" },
        { name: "unknown", count: 1, fill: "#6366f1" },
      ])
    );
  });
});
