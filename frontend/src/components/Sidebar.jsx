import { NavLink } from "react-router-dom";
import { useState } from "react";
import { LogOut, Menu, X } from "lucide-react";
import { sidebarLinks } from "../services/sidebarConfig";
import API from "../services/api"; // use this if API is default export

function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const role = (localStorage.getItem("role") || "customer").toLowerCase();
  const username = localStorage.getItem("username") || "User";

  const handleLogout = async () => {
    try {
      await API.post("logout/");
    } catch {
    } finally {
      localStorage.removeItem("access");
      localStorage.removeItem("role");
      localStorage.removeItem("username");
      window.location.href = "/login";
    }
  };

  const linkClass = ({ isActive }) =>
    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150
     ${isActive
       ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20"
       : "text-slate-400 hover:text-white hover:bg-white/5"
     }`;

  const roleColors = {
    admin: "bg-rose-500/20 text-rose-400 border-rose-500/30",
    agent: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    customer: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  };

  return (
    <div
      style={{ fontFamily: "'DM Sans', sans-serif" }}
      className={`h-screen bg-[#0f1117] border-r border-white/5 flex flex-col transition-all duration-300 shrink-0
      ${collapsed ? "w-[68px]" : "w-60"}`}
    >
      <div className="flex items-center justify-between px-4 py-5 border-b border-white/5">
        {!collapsed && (
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center shrink-0">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M2 4h5v5H2zM9 7h5v5H9z" fill="white" opacity="0.9" />
                <path d="M2 10h3v4H2zM11 2h3v4h-3z" fill="white" opacity="0.5" />
              </svg>
            </div>
            <span className="text-white font-semibold text-sm tracking-tight">Smart Support</span>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-slate-500 hover:text-white transition-colors p-1 rounded-md hover:bg-white/5"
        >
          {collapsed ? <Menu size={16} /> : <X size={16} />}
        </button>
      </div>

      <nav className="flex flex-col gap-1 px-2 py-4 flex-1 overflow-y-auto">
        {!collapsed && (
          <p className="text-xs font-semibold text-slate-600 uppercase tracking-widest px-3 mb-2">
            Navigation
          </p>
        )}
        {sidebarLinks
          .filter((link) => link.roles.includes(role))
          .map((link, index) => {
            const Icon = link.icon;
            return (
              <NavLink key={index} to={link.path} className={linkClass} title={collapsed ? link.label : ""}>
                <Icon size={16} className="shrink-0" />
                {!collapsed && <span>{link.label}</span>}
              </NavLink>
            );
          })}
      </nav>

      <div className="border-t border-white/5 p-3 space-y-2">
        {!collapsed && (
          <div className="flex items-center gap-3 px-2 py-2">
            <div className="w-8 h-8 rounded-full bg-indigo-600/30 border border-indigo-500/30 flex items-center justify-center shrink-0">
              <span className="text-indigo-300 text-xs font-bold uppercase">
                {username?.[0] || "U"}
              </span>
            </div>
            <div className="min-w-0">
              <p className="text-white text-xs font-medium truncate">{username}</p>
              <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${roleColors[role] || roleColors.customer}`}>
                {role}
              </span>
            </div>
          </div>
        )}

        <button
          onClick={handleLogout}
          className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium
            text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all duration-150
            ${collapsed ? "justify-center" : ""}`}
          title="Logout"
        >
          <LogOut size={15} className="shrink-0" />
          {!collapsed && "Sign out"}
        </button>
      </div>
    </div>
  );
}

export default Sidebar;