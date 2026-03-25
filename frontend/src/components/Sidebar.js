import { NavLink, useNavigate } from "react-router-dom";
import { useState } from "react";
import {
  LayoutDashboard,
  Ticket,
  PlusCircle,
  LogOut,
  Menu
} from "lucide-react";

function Sidebar() {
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const role = localStorage.getItem("role"); // admin / agent / customer

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    navigate("/login");
  };

  const linkClass = ({ isActive }) =>
    `flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium transition
     ${
       isActive
         ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow"
         : "text-gray-300 hover:bg-gray-800 hover:text-white"
     }`;

  return (
    <div
      className={`h-screen bg-gray-900 text-white flex flex-col transition-all duration-300
      ${collapsed ? "w-20" : "w-64"}`}
    >
      {/* 🔹 Top Section */}
      <div className="flex items-center justify-between p-4">
        {!collapsed && <h2 className="text-lg font-bold">Smart Support</h2>}

        <button onClick={() => setCollapsed(!collapsed)}>
          <Menu size={20} />
        </button>
      </div>

      {/* 🔹 Links */}
      <div className="flex flex-col gap-2 px-2">

        <NavLink to="/dashboard" className={linkClass}>
          <LayoutDashboard size={18} />
          {!collapsed && "Dashboard"}
        </NavLink>

        <NavLink to="/tickets" className={linkClass}>
          <Ticket size={18} />
          {!collapsed && "Tickets"}
        </NavLink>

        {/* 👇 Only Customer */}
        {role === "customer" && (
          <NavLink to="/create-ticket" className={linkClass}>
            <PlusCircle size={18} />
            {!collapsed && "Create Ticket"}
          </NavLink>
        )}

      </div>

      {/* 🔹 Logout (Bottom) */}
      <button
        onClick={handleLogout}
        className="mt-auto m-4 flex items-center justify-center gap-2 
                   bg-red-500 hover:bg-red-600 px-4 py-2 rounded-lg transition"
      >
        <LogOut size={18} />
        {!collapsed && "Logout"}
      </button>
    </div>
  );
}

export default Sidebar;