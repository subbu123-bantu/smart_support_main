import { useEffect, useState } from "react";
import { getTicketStats, getTickets } from "../services/api";
import { useNavigate } from "react-router-dom";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  LineChart,
  Line,
  CartesianGrid,
} from "recharts";

const CATEGORY_COLORS = [
  "#6366f1",
  "#f59e0b",
  "#22c55e",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
];

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
    color: "text-emerald-600",
    bg: "bg-emerald-50 border-emerald-200",
  },
  medium: {
    color: "text-amber-600",
    bg: "bg-amber-50 border-amber-200",
  },
  high: {
    color: "text-orange-600",
    bg: "bg-orange-50 border-orange-200",
  },
  urgent: {
    color: "text-red-600",
    bg: "bg-red-50 border-red-200",
  },
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
    const token =
      localStorage.getItem("token") || localStorage.getItem("access");

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
      .catch((err) => {
        console.error("Error loading stats:", err);
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
      .catch((err) => {
        console.error("Error loading recent tickets:", err);
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
    <div className="p-6 bg-gray-100 min-h-screen">
      <h2 className="text-2xl font-semibold mb-6 text-gray-800">Dashboard</h2>

      {/* STAT CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div
          onClick={() => navigate("/tickets")}
          className="bg-white p-5 rounded-xl shadow hover:shadow-md transition cursor-pointer"
        >
          <p className="text-gray-500 text-sm">Total</p>
          <h2 className="text-3xl font-bold text-gray-800">
            {loadingStats ? "..." : stats.total}
          </h2>
        </div>

        <div
          onClick={() => navigate("/tickets?status=open")}
          className="bg-white p-5 rounded-xl shadow hover:shadow-md transition cursor-pointer"
        >
          <p className="text-gray-500 text-sm">Open</p>
          <h2 className="text-3xl font-bold text-red-500">
            {loadingStats ? "..." : stats.open}
          </h2>
        </div>

        <div
          onClick={() => navigate("/tickets?status=in_progress")}
          className="bg-white p-5 rounded-xl shadow hover:shadow-md transition cursor-pointer"
        >
          <p className="text-gray-500 text-sm">In Progress</p>
          <h2 className="text-3xl font-bold text-yellow-500">
            {loadingStats ? "..." : stats.in_progress}
          </h2>
        </div>

        <div
          onClick={() => navigate("/tickets?status=closed")}
          className="bg-white p-5 rounded-xl shadow hover:shadow-md transition cursor-pointer"
        >
          <p className="text-gray-500 text-sm">Closed</p>
          <h2 className="text-3xl font-bold text-green-500">
            {loadingStats ? "..." : stats.closed}
          </h2>
        </div>
      </div>

      {/* ADMIN / AGENT SECTION */}
      {(role === "admin" || role === "agent") && (
        <>
          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Status Breakdown */}
            <div className="bg-white rounded-xl p-5 shadow">
              <h3 className="text-base font-semibold text-gray-700 mb-4">
                Status Breakdown
              </h3>
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={95}
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
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Tickets Last 7 Days */}
            <div className="bg-white rounded-xl p-5 shadow">
              <h3 className="text-base font-semibold text-gray-700 mb-4">
                Tickets Last 7 Days
              </h3>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={lineData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#6366f1"
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: "#6366f1" }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Category + Priority */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="bg-white rounded-xl p-5 shadow">
              <h3 className="text-base font-semibold text-gray-700 mb-4">
                Tickets by Category
              </h3>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={categoryData} barSize={36}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
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

            <div className="bg-white rounded-xl p-5 shadow">
              <h3 className="text-base font-semibold text-gray-700 mb-4">
                Tickets by Priority
              </h3>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={priorityData} barSize={36}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
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

          {/* Agent Workload */}
          <div className="bg-white rounded-xl shadow overflow-hidden mb-8">
            <div className="p-5 border-b border-gray-100">
              <h3 className="text-base font-semibold text-gray-700">
                Agent Workload
              </h3>
              <p className="text-xs text-gray-400 mt-1">
                Performance overview of all agents
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
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
                      <td
                        colSpan={6}
                        className="py-8 text-center text-gray-400"
                      >
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
                          className="border-t border-gray-100 hover:bg-gray-50 transition"
                        >
                          <td className="py-3 px-4 font-medium text-gray-800">
                            👤 {agent.agent}
                          </td>
                          <td className="py-3 px-4 text-center text-indigo-600 font-semibold">
                            {agent.assigned}
                          </td>
                          <td className="py-3 px-4 text-center text-yellow-500 font-semibold">
                            {agent.in_progress}
                          </td>
                          <td className="py-3 px-4 text-center text-green-500 font-semibold">
                            {agent.solved}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-gray-200 rounded-full h-2">
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
                          <td className="py-3 px-4 text-center text-gray-500 text-sm">
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

          {/* Recent Tickets */}
          <div className="bg-white p-5 rounded-xl shadow">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">
              Recent Tickets
            </h3>

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
                      className="flex justify-between items-center p-4 rounded-xl border border-gray-200 hover:border-indigo-400 hover:bg-indigo-50 cursor-pointer transition"
                    >
                      <div>
                        <p className="text-sm font-medium text-gray-800">
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
        </>
      )}
    </div>
  );
}

export default Dashboard;