import { NavLink, useNavigate } from "react-router-dom";
import { useState } from "react";
import { LogOut, Menu } from "lucide-react";
import { sidebarLinks } from "../services/sidebarConfig";

function Sidebar() {
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const role = (localStorage.getItem("role") || "Customer").toLowerCase();

  const handleLogout = async () => {
  try {
    await LogOut();
  } catch (err) {
    // ignore
  } finally {
    localStorage.removeItem("access");
    localStorage.removeItem("role");
    window.location.href = "/login";  // hard redirect, clears React state too
  }
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
      {/* 🔹 Top */}
      <div className="flex items-center justify-between p-4">
        {!collapsed && <h2 className="text-lg font-bold">Smart Support</h2>}
        <button onClick={() => setCollapsed(!collapsed)}>
          <Menu size={20} />
        </button>
      </div>

      {/* 🔹 Dynamic Links */}
      <div className="flex flex-col gap-2 px-2">
        {sidebarLinks
          .filter((link) => link.roles.includes(role))
          .map((link, index) => {
            const Icon = link.icon;

            return (
              <NavLink key={index} to={link.path} className={linkClass}>
                <Icon size={18} />
                {!collapsed && link.label}
              </NavLink>
            );
          })}
      </div>

      {/* 🔹 Logout */}
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