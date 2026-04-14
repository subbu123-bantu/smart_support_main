import { useEffect, useState } from "react";
import { getTicketStats, getTickets } from "../services/api";
import { useNavigate } from "react-router-dom";
import {BarChart,Bar,XAxis,YAxis,Tooltip,ResponsiveContainer,Cell,PieChart,Pie,LineChart,Line,CartesianGrid,} from "recharts";

const CATEGORY_COLORS = ["#6366f1","#f59e0b","#22c55e","#ef4444","#8b5cf6","#06b6d4",];

const PRIORITY_COLORS = {
  urgent: "#7c3aed",
  high: "#ef4444",
  medium: "#f59e0b",
  low: "#22c55e",
};

const STATUS_COLORS = {
  Open: "#ef4444",
  "In Progress": "#f59e0b",
  Closed: "#22c55e",
};

const PRIORITY_META = {
  low: {
    color: "text-emerald-400",
    bg: "bg-emerald-500/10 border-emerald-500/20",
  },
  medium: {
    color: "text-amber-400",
    bg: "bg-amber-500/10 border-amber-500/20",
  },
  high: {
    color: "text-orange-400",
    bg: "bg-orange-500/10 border-orange-500/20",
  },
  urgent: {
    color: "text-red-400",
    bg: "bg-red-500/10 border-red-500/20",
  },
};

const chartAxisStyle = { fontSize: 12, fill: "#6b7280" };

const tooltipStyle = {
  backgroundColor: "#111827",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: "14px",
  color: "#fff",
};

function Dashboard() {
  const navigate = useNavigate();
  const role = localStorage.getItem("role");

  const [stats, setStats] = useState({
    total: 0,
    open: 0,
    in_progress: 0,
    closed: 0,
    by_category: [],
    by_priority: [],
    by_date: [],
    agent_workload: [],
  });

  const [recentTickets, setRecentTickets] = useState([]);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingTickets, setLoadingTickets] = useState(false);

  useEffect(() => {
  const token = localStorage.getItem("access");
    if (!token) return;

    setLoadingStats(true);
    getTicketStats()
      .then((res) => {
        setStats({
          total: res.data?.total ?? 0,
          open: res.data?.open ?? 0,
          in_progress: res.data?.in_progress ?? 0,
          closed: res.data?.closed ?? 0,
          by_category: res.data?.by_category ?? [],
          by_priority: res.data?.by_priority ?? [],
          by_date: res.data?.by_date ?? [],
          agent_workload: res.data?.agent_workload ?? [],
        });
      })
      .catch(() => {
      setStats({
        total: 0,
        open: 0,
        in_progress: 0,
        closed: 0,
        by_category: [],
        by_priority: [],
        by_date: [],
        agent_workload: [],
      });
    })
      .finally(() => setLoadingStats(false));
  }, []);

  useEffect(() => {
    if (role !== "admin" && role !== "agent") return;

    setLoadingTickets(true);
    getTickets(1)
      .then((res) => {
        setRecentTickets(res.data?.results?.slice(0, 5) || []);
      })
      .catch(() => {
        setRecentTickets([]);
      })
      .finally(() => setLoadingTickets(false));
  }, [role]);

  const pieData = [
    { name: "Open", value: stats.open || 0 },
    { name: "In Progress", value: stats.in_progress || 0 },
    { name: "Closed", value: stats.closed || 0 },
  ];

  const categoryData = (stats.by_category || []).map((c) => ({
    name: c.category__name || "Unknown",
    count: c.count || 0,
  }));

  const priorityData = (stats.by_priority || []).map((p) => ({
    name: p.priority || "unknown",
    count: p.count || 0,
  }));

  const lineData = (stats.by_date || []).map((d) => ({
    date: d.date ? d.date.slice(5) : "",
    count: d.count || 0,
  }));

  return (
    <div
      style={{ fontFamily: "'DM Sans', sans-serif" }}
      className="min-h-screen bg-[#0c0e14] p-6"
    >
      <div className="mb-8">
        <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-4 py-1.5 mb-4">
          <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
          <span className="text-indigo-400 text-xs font-medium tracking-wide">
            Ticket Operations Overview
          </span>
        </div>

        <h2
          className="text-3xl font-bold text-white mb-2"
          style={{ letterSpacing: "-0.03em" }}
        >
          Dashboard
        </h2>
        <p className="text-gray-500 text-sm">
          Monitor ticket flow, team workload, and recent activity in one place.
        </p>
      </div>

      {/* STAT CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
        <div
          onClick={() => navigate("/tickets")}
          className="bg-[#0f1117] border border-white/5 rounded-2xl p-5 cursor-pointer transition-all duration-200 hover:border-indigo-500/20 hover:bg-[#12151d]"
        >
          <p className="text-gray-500 text-sm mb-2">Total Tickets</p>
          <h2
            className="text-3xl font-bold text-white"
            style={{ letterSpacing: "-0.02em" }}
          >
            {loadingStats ? "..." : stats.total}
          </h2>
        </div>

        <div
          onClick={() => navigate("/tickets?status=open")}
          className="bg-[#0f1117] border border-white/5 rounded-2xl p-5 cursor-pointer transition-all duration-200 hover:border-red-500/20 hover:bg-[#12151d]"
        >
          <p className="text-gray-500 text-sm mb-2">Open</p>
          <h2
            className="text-3xl font-bold text-red-400"
            style={{ letterSpacing: "-0.02em" }}
          >
            {loadingStats ? "..." : stats.open}
          </h2>
        </div>

        <div
          onClick={() => navigate("/tickets?status=in_progress")}
          className="bg-[#0f1117] border border-white/5 rounded-2xl p-5 cursor-pointer transition-all duration-200 hover:border-amber-500/20 hover:bg-[#12151d]"
        >
          <p className="text-gray-500 text-sm mb-2">In Progress</p>
          <h2
            className="text-3xl font-bold text-amber-400"
            style={{ letterSpacing: "-0.02em" }}
          >
            {loadingStats ? "..." : stats.in_progress}
          </h2>
        </div>

        <div
          onClick={() => navigate("/tickets?status=closed")}
          className="bg-[#0f1117] border border-white/5 rounded-2xl p-5 cursor-pointer transition-all duration-200 hover:border-emerald-500/20 hover:bg-[#12151d]"
        >
          <p className="text-gray-500 text-sm mb-2">Closed</p>
          <h2
            className="text-3xl font-bold text-emerald-400"
            style={{ letterSpacing: "-0.02em" }}
          >
            {loadingStats ? "..." : stats.closed}
          </h2>
        </div>
      </div>

      {(role === "admin") && (
        <>
          {/* CHARTS */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
            <div className="bg-[#0f1117] border border-white/5 rounded-2xl p-5">
              <h3 className="text-base font-semibold text-white mb-1">
                Status Breakdown
              </h3>
              <p className="text-xs text-gray-600 mb-4">
                Distribution of open, active, and resolved tickets
              </p>

              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={62}
                    outerRadius={96}
                    paddingAngle={4}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                  >
                    {pieData.map((entry, i) => (
                      <Cell
                        key={i}
                        fill={STATUS_COLORS[entry.name] || "#6366f1"}
                      />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-[#0f1117] border border-white/5 rounded-2xl p-5">
              <h3 className="text-base font-semibold text-white mb-1">
                Tickets Last 7 Days
              </h3>
              <p className="text-xs text-gray-600 mb-4">
                Daily incoming ticket volume trend
              </p>

              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={lineData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" tick={chartAxisStyle} />
                  <YAxis allowDecimals={false} tick={chartAxisStyle} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#818cf8"
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: "#818cf8" }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* CATEGORY + PRIORITY */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
            <div className="bg-[#0f1117] border border-white/5 rounded-2xl p-5">
              <h3 className="text-base font-semibold text-white mb-1">
                Tickets by Category
              </h3>
              <p className="text-xs text-gray-600 mb-4">
                Category distribution across all tickets
              </p>

              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={categoryData} barSize={34}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" tick={chartAxisStyle} />
                  <YAxis allowDecimals={false} tick={chartAxisStyle} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                    {categoryData.map((_, i) => (
                      <Cell
                        key={i}
                        fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-[#0f1117] border border-white/5 rounded-2xl p-5">
              <h3 className="text-base font-semibold text-white mb-1">
                Tickets by Priority
              </h3>
              <p className="text-xs text-gray-600 mb-4">
                Priority mix currently handled by the system
              </p>

              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={priorityData} barSize={34}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" tick={chartAxisStyle} />
                  <YAxis allowDecimals={false} tick={chartAxisStyle} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                    {priorityData.map((entry, i) => (
                      <Cell
                        key={i}
                        fill={PRIORITY_COLORS[entry.name] || "#6366f1"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* AGENT WORKLOAD */}
          <div className="bg-[#0f1117] border border-white/5 rounded-2xl overflow-hidden mb-8">
            <div className="p-5 border-b border-white/5">
              <h3 className="text-base font-semibold text-white mb-1">
                Agent Workload
              </h3>
              <p className="text-xs text-gray-600">
                Performance overview of all active agents
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-white/[0.02] text-gray-500 text-xs uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4 text-left">Agent</th>
                    <th className="py-3 px-4 text-center">Assigned</th>
                    <th className="py-3 px-4 text-center">In Progress</th>
                    <th className="py-3 px-4 text-center">Solved</th>
                    <th className="py-3 px-4 text-center">Solve Rate</th>
                    <th className="py-3 px-4 text-center">Avg Resolution</th>
                  </tr>
                </thead>
                <tbody>
                  {(stats.agent_workload || []).length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-gray-600">
                        No agents found
                      </td>
                    </tr>
                  ) : (
                    stats.agent_workload.map((agent, i) => {
                      const solveRate =
                        agent.assigned > 0
                          ? Math.round((agent.solved / agent.assigned) * 100)
                          : 0;

                      return (
                        <tr
                          key={i}
                          className="border-t border-white/5 hover:bg-white/[0.02] transition"
                        >
                          <td className="py-3 px-4 font-medium text-white">
                            👤 {agent.agent}
                          </td>
                          <td className="py-3 px-4 text-center text-indigo-400 font-semibold">
                            {agent.assigned}
                          </td>
                          <td className="py-3 px-4 text-center text-amber-400 font-semibold">
                            {agent.in_progress}
                          </td>
                          <td className="py-3 px-4 text-center text-emerald-400 font-semibold">
                            {agent.solved}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-white/5 rounded-full h-2">
                                <div
                                  className="bg-indigo-500 h-2 rounded-full"
                                  style={{ width: `${solveRate}%` }}
                                />
                              </div>
                              <span className="text-xs text-gray-500 w-8">
                                {solveRate}%
                              </span>
                            </div>
                          </td>
                          <td className="py-3 px-4 text-center text-gray-400 text-sm">
                            {agent.avg_resolution_hours != null
                              ? `${agent.avg_resolution_hours}h`
                              : "—"}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
            {(role === "admin" || role === "agent") && (
              <div className="bg-[#0f1117] border border-white/5 rounded-2xl p-5">
                <h3 className="text-lg font-semibold mb-1 text-white">
                  Recent Tickets
                </h3>
                <p className="text-xs text-gray-600 mb-5">
                  Latest ticket activity across the workspace
                </p>

                {loadingTickets ? (
                  <p className="text-gray-500 text-sm">Loading...</p>
                ) : recentTickets.length === 0 ? (
                  <p className="text-gray-500 text-sm">No recent tickets</p>
                ) : (
                  <div className="space-y-3">
                    {recentTickets.map((ticket) => {
                      const meta = PRIORITY_META[ticket.priority] || PRIORITY_META.low;

                    return (
                      <div
                        key={ticket.id}
                        onClick={() => navigate(`/tickets/${ticket.id}`)}
                        className="flex justify-between items-center p-4 rounded-xl bg-white/[0.03] border border-white/5 hover:border-indigo-500/20 hover:bg-indigo-500/5 cursor-pointer transition-all duration-200"
                      >
                        <div>
                          <p className="text-sm font-medium text-white">
                            #{ticket.id} {ticket.title}
                          </p>
                        </div>

                        <span
                          className={`text-xs px-3 py-1 rounded-full border ${meta.bg} ${meta.color}`}
                        >
                          {ticket.priority}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
       </>
      )}
    </div>
  );
}
export default Dashboard;