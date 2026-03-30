import {
  LayoutDashboard,
  Ticket,
  PlusCircle,
} from "lucide-react";

export const sidebarLinks = [
  {
    label: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
    roles: ["admin", "agent", "customer"],
  },
  {
    label: "Tickets",
    path: "/tickets",
    icon: Ticket,
    roles: ["admin", "agent"],
  },
  {
    label: "My Tickets",
    path: "/tickets",
    icon: Ticket,
    roles: ["customer"],
  },
  {
    label: "Create Ticket",
    path: "/create-ticket",
    icon: PlusCircle,
    roles: ["customer"],
  },
];