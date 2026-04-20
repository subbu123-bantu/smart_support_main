import "@testing-library/jest-dom";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import EvaluationBadge from "../components/EvaluationBadge";
import FeedbackCard from "../components/FeedBackCard";
import Layout from "../components/Layout";
import PriorityBadge from "../components/PriorityBadge";
import StatusBadge from "../components/StatusBadge";
import TicketFilters from "../components/TicketFilters";
import Topbar from "../components/Topbar";

jest.mock("../components/Sidebar", () => () => <div data-testid="sidebar">Sidebar</div>);
jest.mock("lucide-react", () => ({
  Search: () => <span data-testid="search-icon" />,
  X: () => <span data-testid="clear-icon" />,
  Filter: () => <span data-testid="filter-icon" />,
}));

describe("shared UI components", () => {
  test("renders evaluation badge labels for each state", () => {
    const { rerender } = render(<EvaluationBadge value={null} />);
    expect(screen.getByText("Pending")).toBeInTheDocument();

    rerender(<EvaluationBadge value />);
    expect(screen.getByText("Correct")).toBeInTheDocument();

    rerender(<EvaluationBadge value={false} />);
    expect(screen.getByText("Incorrect")).toBeInTheDocument();
  });

  test("renders feedback card content", () => {
    render(<FeedbackCard title="Category">Body content</FeedbackCard>);
    expect(screen.getByText("Category")).toBeInTheDocument();
    expect(screen.getByText("Body content")).toBeInTheDocument();
  });

  test("renders layout with sidebar, topbar, and children", () => {
    render(<Layout><div>Main content</div></Layout>);
    expect(screen.getByTestId("sidebar")).toBeInTheDocument();
    expect(screen.getByText("Main content")).toBeInTheDocument();
  });

  test("renders priority and status badges with mapped and fallback labels", () => {
    const { rerender } = render(<PriorityBadge priority="high" />);
    expect(screen.getByText("High")).toBeInTheDocument();

    rerender(<PriorityBadge priority="unknown" />);
    expect(screen.getByText("Low")).toBeInTheDocument();

    rerender(<StatusBadge status="closed" />);
    expect(screen.getByText("Closed")).toBeInTheDocument();

    rerender(<StatusBadge status="unknown" />);
    expect(screen.getByText("Open")).toBeInTheDocument();
  });

  test("renders ticket filters and triggers handlers", () => {
    const onSearchInputChange = jest.fn();
    const onSearch = jest.fn();
    const onClear = jest.fn();
    const onPriorityChange = jest.fn();
    const onCategoryChange = jest.fn();
    const onAssignedChange = jest.fn();

    render(
      <TicketFilters
        searchInput="printer"
        onSearchInputChange={onSearchInputChange}
        onSearch={onSearch}
        onClear={onClear}
        isSearchMode
        priority="all"
        onPriorityChange={onPriorityChange}
        selectedCategory=""
        onCategoryChange={onCategoryChange}
        categories={[{ id: 1, name: "Billing" }]}
        assignedFilter=""
        onAssignedChange={onAssignedChange}
        role="admin"
        ticketCount={3}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("Search tickets..."), {
      target: { value: "router" },
    });
    fireEvent.keyDown(screen.getByPlaceholderText("Search tickets..."), {
      key: "Enter",
      code: "Enter",
    });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    fireEvent.click(screen.getByRole("button", { name: /clear/i }));

    const selects = screen.getAllByRole("combobox");
    fireEvent.change(selects[0], { target: { value: "high" } });
    fireEvent.change(selects[1], { target: { value: "1" } });
    fireEvent.change(selects[2], { target: { value: "true" } });

    expect(onSearchInputChange).toHaveBeenCalledWith("router");
    expect(onSearch).toHaveBeenCalledTimes(2);
    expect(onClear).toHaveBeenCalled();
    expect(onPriorityChange).toHaveBeenCalled();
    expect(onCategoryChange).toHaveBeenCalled();
    expect(onAssignedChange).toHaveBeenCalled();
  });

  test("renders topbar date", () => {
    const localeSpy = jest
      .spyOn(Date.prototype, "toLocaleDateString")
      .mockReturnValue("20 Apr 2026");

    render(<Topbar />);
    expect(screen.getByText("20 Apr 2026")).toBeInTheDocument();

    localeSpy.mockRestore();
  });
});
