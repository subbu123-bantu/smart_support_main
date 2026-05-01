import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../App";
import EvaluationBadge from "../components/EvaluationBadge";
import PrivateRoute from "../components/PrivateRoute";
import Sidebar from "../components/Sidebar";
import TicketCard from "../components/TicketCard";
import TicketFilters from "../components/TicketFilters";
import API, { clearAuthStorage } from "../services/api";

const mockDecode = jest.fn();

jest.mock("jwt-decode", () => ({ jwtDecode: (...args) => mockDecode(...args) }));
jest.mock("../pages/Login", () => () => <div>Login Page</div>);
jest.mock("../pages/ForgotPassword", () => () => <div>Forgot Page</div>);
jest.mock("../pages/ResetPassword", () => () => <div>Reset Page</div>);
jest.mock("../pages/Register", () => () => <div>Register Page</div>);
jest.mock("../pages/Dashboard", () => () => <div>Dashboard Page</div>);
jest.mock("../pages/CreateTicket", () => () => <div>Create Ticket Page</div>);
jest.mock("../pages/Tickets", () => () => <div>Tickets Page</div>);
jest.mock("../pages/TicketDetails", () => () => <div>Ticket Details Page</div>);
jest.mock("../pages/ChangeEmail", () => () => <div>Change Email Page</div>);

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  localStorage.setItem("access", "token");
  localStorage.setItem("role", "admin");
  localStorage.setItem("username", "sam");
});

test("app routes root to login and renders protected dashboard", () => {
  window.history.pushState({}, "", "/");
  render(<App />);
  expect(screen.getByText("Login Page")).toBeInTheDocument();
  mockDecode.mockReturnValue({ exp: Math.floor(Date.now() / 1000) + 60 });
  window.history.pushState({}, "", "/dashboard");
  render(<App />);
  expect(screen.getByText("Dashboard Page")).toBeInTheDocument();
});

test("private route clears auth for expired tokens and allows matching roles", () => {
  mockDecode.mockReturnValue({ exp: 1 });
  const view = render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><PrivateRoute allowedRoles={["admin"]}><div>secret</div></PrivateRoute></MemoryRouter>);
  expect(screen.queryByText("secret")).not.toBeInTheDocument();
  view.unmount();
  localStorage.setItem("access", "fresh");
  localStorage.setItem("role", "admin");
  mockDecode.mockReturnValue({ exp: Math.floor(Date.now() / 1000) + 60 });
  render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><PrivateRoute allowedRoles={["admin"]}><div>secret</div></PrivateRoute></MemoryRouter>);
  expect(screen.getByText("secret")).toBeInTheDocument();
  clearAuthStorage();
  expect(localStorage.getItem("access")).toBeNull();
});

test("private route rejects invalid tokens and disallowed roles", () => {
  mockDecode.mockImplementationOnce(() => {
    throw new Error("bad token");
  });
  const view = render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><PrivateRoute allowedRoles={["admin"]}><div>secret</div></PrivateRoute></MemoryRouter>);
  expect(screen.queryByText("secret")).not.toBeInTheDocument();
  view.unmount();

  localStorage.setItem("access", "fresh");
  localStorage.setItem("role", "customer");
  mockDecode.mockReturnValue({ exp: Math.floor(Date.now() / 1000) + 60 });
  render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><PrivateRoute allowedRoles={["admin"]}><div>secret</div></PrivateRoute></MemoryRouter>);
  expect(screen.queryByText("secret")).not.toBeInTheDocument();
});

test("sidebar shows role links and logs out", async () => {
  Object.defineProperty(window, "location", { value: { href: "" }, writable: true });
  API.post = jest.fn().mockResolvedValue({});
  render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><Sidebar /></MemoryRouter>);
  expect(screen.getByText("Dashboard")).toBeInTheDocument();
  expect(screen.getByText("Tickets")).toBeInTheDocument();
  expect(screen.getByText("Change Email")).toBeInTheDocument();
  expect(screen.queryByText("Create Ticket")).not.toBeInTheDocument();
  fireEvent.click(screen.getByTitle("Logout"));
  expect(API.post).toHaveBeenCalledWith("logout/");
  await screen.findByTitle("Logout");
  expect(window.location.href).toBe("/login");
});

test("sidebar collapses and still logs out after api failures", async () => {
  Object.defineProperty(window, "location", { value: { href: "" }, writable: true });
  localStorage.setItem("role", "agent");
  localStorage.setItem("username", "alex");
  API.post = jest.fn().mockRejectedValue(new Error("network"));
  render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><Sidebar /></MemoryRouter>);

  fireEvent.click(screen.getByRole("button", { name: "" }));
  expect(screen.queryByText("Navigation")).not.toBeInTheDocument();
  expect(screen.getByTitle("Dashboard")).toBeInTheDocument();

  fireEvent.click(screen.getByTitle("Logout"));
  await screen.findByTitle("Logout");
  expect(window.location.href).toBe("/login");
  expect(localStorage.getItem("access")).toBeNull();
});

test("ticket card and filters trigger callbacks", () => {
  const onFieldUpdate = jest.fn(), onStatusUpdate = jest.fn(), onAssign = jest.fn(), onSearch = jest.fn(), onClear = jest.fn();
  render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><TicketCard ticket={{ id: 1, user_ticket_id: 11, title: "Printer", description: "Broken", status: "open", priority: "low", category: 2, category_name: "Hardware", assigned_to: "" }} role="admin" categories={[{ id: 2, name: "Hardware" }]} agents={[{ id: 7, username: "Alex", category_names: ["Hardware"] }]} onFieldUpdate={onFieldUpdate} onStatusUpdate={onStatusUpdate} onAssign={onAssign} /></MemoryRouter>);
  fireEvent.change(screen.getAllByRole("combobox")[0], { target: { value: "high" } });
  fireEvent.change(screen.getAllByRole("combobox")[1], { target: { value: "2" } });
  fireEvent.change(screen.getAllByRole("combobox")[2], { target: { value: "closed" } });
  fireEvent.change(screen.getAllByRole("combobox")[3], { target: { value: "7" } });
  expect(onFieldUpdate).toHaveBeenCalledTimes(2);
  expect(onStatusUpdate).toHaveBeenCalledWith(1, "closed");
  expect(onAssign).toHaveBeenCalledWith(1, "7");
  render(<TicketFilters searchInput="" onSearchInputChange={() => {}} onSearch={onSearch} onClear={onClear} isSearchMode priority="all" onPriorityChange={() => {}} selectedCategory="" onCategoryChange={() => {}} categories={[]} assignedFilter="" onAssignedChange={() => {}} role="admin" />);
  fireEvent.click(screen.getByRole("button", { name: /search/i }));
  fireEvent.click(screen.getByRole("button", { name: /clear/i }));
  expect(onSearch).toHaveBeenCalled();
  expect(onClear).toHaveBeenCalled();
});

test("ticket card formats admin assignment labels and tolerates missing callbacks", () => {
  render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <TicketCard
        ticket={{ id: 3, user_ticket_id: 44, title: "Mail", description: "Queue stuck", status: "open", priority: "low", category: 1, category_name: "", assigned_to: "" }}
        role="admin"
        categories={[{ id: 1, name: "Ops" }]}
        agents={[{ id: 9, username: "Jamie", category_names: [] }, { id: 10, username: "Rae", category_names: ["Ops", "Infra"] }]}
        onFieldUpdate={undefined}
        onStatusUpdate={undefined}
        onAssign={undefined}
      />
    </MemoryRouter>
  );

  expect(screen.getByRole("option", { name: "Jamie" })).toBeInTheDocument();
  expect(screen.getByRole("option", { name: "Rae - Ops, Infra" })).toBeInTheDocument();
  fireEvent.change(screen.getAllByRole("combobox")[0], { target: { value: "medium" } });
  fireEvent.change(screen.getAllByRole("combobox")[1], { target: { value: "1" } });
  fireEvent.change(screen.getAllByRole("combobox")[2], { target: { value: "closed" } });
  fireEvent.change(screen.getAllByRole("combobox")[3], { target: { value: "9" } });
});

test("ticket card navigation, role variants, and badge states render correctly", () => {
  render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><TicketCard ticket={{ id: 5, user_ticket_id: 42, title: "VPN", description: "No access", status: "in_progress", priority: "medium", category: "Billing", assigned_to: "", assigned_to_name: "" }} role="customer" categories={[]} agents={[]} /></MemoryRouter>);
  expect(screen.getByText("#42")).toBeInTheDocument();
  expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /vpn/i }));
  expect(screen.getByText("No access")).toBeInTheDocument();

  render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><TicketCard ticket={{ id: 6, user_ticket_id: 43, title: "Email", description: "Delayed", status: "open", priority: "high", category: 2, category_name: "", assigned_to: "" }} role="agent" categories={[]} agents={[]} /></MemoryRouter>);
  expect(screen.getAllByRole("combobox")).toHaveLength(1);

  render(
    <>
      <EvaluationBadge value />
      <EvaluationBadge value={false} />
      <EvaluationBadge value={null} />
      <TicketFilters searchInput="vpn" onSearchInputChange={() => {}} onSearch={jest.fn()} onClear={jest.fn()} isSearchMode={false} priority="all" onPriorityChange={() => {}} selectedCategory="" onCategoryChange={() => {}} categories={[]} assignedFilter="" onAssignedChange={() => {}} role="customer" />
    </>
  );
  expect(screen.getByText("Correct")).toBeInTheDocument();
  expect(screen.getByText("Incorrect")).toBeInTheDocument();
  expect(screen.getByText("Pending")).toBeInTheDocument();
  fireEvent.keyDown(screen.getByPlaceholderText(/search tickets/i), { key: "Enter" });
  expect(screen.queryByDisplayValue("All Categories")).not.toBeInTheDocument();
});
