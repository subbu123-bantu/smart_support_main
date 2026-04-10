import { useEffect, useState } from "react";
import { getTicketStats, getTickets } from "../services/api";
import { useNavigate } from "react-router-dom";

const PRIORITY_META = {
  low:    { color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  medium: { color: "text-amber-400",   bg: "bg-amber-500/10 border-amber-500/20"   },
  high:   { color: "text-orange-400",  bg: "bg-orange-500/10 border-orange-500/20"  },
  urgent: { color: "text-red-400",     bg: "bg-red-500/10 border-red-500/20"        },
};

function Dashboard() {
  const navigate = useNavigate();
  const role = localStorage.getItem("role");

  const [stats, setStats] = useState({
    total: 0,
    open: 0,
    in_progress: 0,
    closed: 0,
  });

  const [recentTickets, setRecentTickets] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await getTicketStats();
        setStats(res.data);
      } catch (error) {
        console.error(error);
      }
    };

    if (localStorage.getItem("access")) fetchStats();
  }, []);

  useEffect(() => {
    const fetchRecent = async () => {
      setLoading(true);
      try {
        const res = await getTickets(1);
        setRecentTickets(res.data.results.slice(0, 5));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (role === "admin" || role === "agent") fetchRecent();
  }, [role]);

  return (
    <div className="min-h-screen bg-[#0c0e14] text-white p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">
          Overview of your support system
        </p>
      </div>

      {/* 🔹 Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

        {/* Total */}
        <div
          onClick={() => navigate("/tickets")}
          className="bg-white/[0.03] border border-white/10 p-5 rounded-2xl cursor-pointer hover:border-indigo-500/40 hover:bg-indigo-500/5 transition"
        >
          <p className="text-gray-500 text-sm mb-1">Total Tickets</p>
          <h2 className="text-3xl font-bold">{stats.total}</h2>
        </div>

        {/* Open */}
        <div
          onClick={() => navigate("/tickets?status=open")}
          className="bg-white/[0.03] border border-white/10 p-5 rounded-2xl cursor-pointer hover:border-red-500/40 hover:bg-red-500/5 transition"
        >
          <p className="text-gray-500 text-sm mb-1">Open</p>
          <h2 className="text-3xl font-bold text-red-400">{stats.open}</h2>
        </div>

        {/* In Progress */}
        <div
          onClick={() => navigate("/tickets?status=in_progress")}
          className="bg-white/[0.03] border border-white/10 p-5 rounded-2xl cursor-pointer hover:border-amber-500/40 hover:bg-amber-500/5 transition"
        >
          <p className="text-gray-500 text-sm mb-1">In Progress</p>
          <h2 className="text-3xl font-bold text-amber-400">{stats.in_progress}</h2>
        </div>

        {/* Closed */}
        <div
          onClick={() => navigate("/tickets?status=closed")}
          className="bg-white/[0.03] border border-white/10 p-5 rounded-2xl cursor-pointer hover:border-emerald-500/40 hover:bg-emerald-500/5 transition"
        >
          <p className="text-gray-500 text-sm mb-1">Closed</p>
          <h2 className="text-3xl font-bold text-emerald-400">{stats.closed}</h2>
        </div>

      </div>

      {/* 🔹 Recent Activity */}
      {(role === "admin" || role === "agent") && (
        <div className="mt-10 bg-white/[0.03] border border-white/10 rounded-2xl p-5">

          <h3 className="text-lg font-semibold mb-5">Recent Activity</h3>

          {loading ? (
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
                    className="flex justify-between items-center p-4 rounded-xl bg-white/[0.02] border border-white/5 hover:border-indigo-500/30 hover:bg-indigo-500/5 cursor-pointer transition"
                  >
                    <div>
                      <p className="text-sm font-medium">
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
    </div>
  );
}

export default Dashboard;