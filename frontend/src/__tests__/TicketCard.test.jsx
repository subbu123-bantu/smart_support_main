import "@testing-library/jest-dom";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import TicketCard from "../components/TicketCard";

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

const baseTicket = {
  id: 7,
  user_ticket_id: "CUS-007",
  title: "Printer issue",
  description: "Printer is not working",
  status: "open",
  priority: "high",
  category: 2,
  category_name: "Technical",
  assigned_to: "",
};

const categories = [
  { id: 1, name: "Billing" },
  { id: 2, name: "Technical" },
];

const agents = [
  { id: 3, username: "agent1", category_names: ["Technical", "Network"] },
  { id: 4, username: "agent2", category_names: [] },
];

describe("TicketCard", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("navigates to ticket details when clicked", () => {
    render(
      <MemoryRouter>
        <TicketCard
          ticket={baseTicket}
          role="customer"
          categories={categories}
          agents={agents}
        />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button"));

    expect(mockNavigate).toHaveBeenCalledWith("/tickets/7");
    expect(screen.getByText("#CUS-007")).toBeInTheDocument();
  });

  test("admin controls update priority, category, status, and assignment", () => {
    const onFieldUpdate = jest.fn();
    const onStatusUpdate = jest.fn();
    const onAssign = jest.fn();

    render(
      <MemoryRouter>
        <TicketCard
          ticket={baseTicket}
          role="admin"
          categories={categories}
          agents={agents}
          onFieldUpdate={onFieldUpdate}
          onStatusUpdate={onStatusUpdate}
          onAssign={onAssign}
        />
      </MemoryRouter>,
    );

    const selects = screen.getAllByRole("combobox");

    fireEvent.change(selects[0], { target: { value: "urgent" } });
    fireEvent.change(selects[1], { target: { value: "1" } });
    fireEvent.change(selects[2], { target: { value: "closed" } });
    fireEvent.change(selects[3], { target: { value: "3" } });

    expect(onFieldUpdate).toHaveBeenCalledWith(7, { priority: "urgent" });
    expect(onFieldUpdate).toHaveBeenCalledWith(7, { category: "1" });
    expect(onStatusUpdate).toHaveBeenCalledWith(7, "closed");
    expect(onAssign).toHaveBeenCalledWith(7, "3");
    expect(screen.getByRole("option", { name: "agent1 - Technical, Network" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "agent2" })).toBeInTheDocument();
  });

  test("agent can only update status", () => {
    const onStatusUpdate = jest.fn();

    render(
      <MemoryRouter>
        <TicketCard
          ticket={baseTicket}
          role="agent"
          categories={categories}
          agents={agents}
          onStatusUpdate={onStatusUpdate}
        />
      </MemoryRouter>,
    );

    const selects = screen.getAllByRole("combobox");
    expect(selects).toHaveLength(1);

    fireEvent.change(selects[0], { target: { value: "in_progress" } });

    expect(onStatusUpdate).toHaveBeenCalledWith(7, "in_progress");
  });
});
