import { useEffect, useState } from "react";
import { getTicketStats, getTickets } from "../services/api";
import { useNavigate } from "react-router-dom";

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

  // 🔹 Fetch Stats
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await getTicketStats();
        setStats(res.data);
      } catch (error) {
        console.error("Error loading stats:", error);
      }
    };

    fetchStats();
  }, []);

  // 🔹 Fetch Recent Tickets
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

    if (role === "admin" || role === "agent") {
      fetchRecent();
    }
  }, [role]);

  return (
    <div className="p-6 bg-gray-100 min-h-screen overflow-y=none">

      <h2 className="text-2xl font-semibold mb-6">Dashboard</h2>

      {/* 🔹 Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

        <div className="bg-white p-5 rounded-xl shadow hover:shadow-md transition">
          <p className="text-gray-500 text-sm">Total</p>
          <h2 className="text-3xl font-bold">{stats.total}</h2>
        </div>

        <div
          onClick={() => navigate("/tickets?status=open")}
          className="bg-white p-5 rounded-xl shadow hover:shadow-md cursor-pointer"
        >
          <p className="text-gray-500 text-sm">Open</p>
          <h2 className="text-3xl font-bold text-red-500">{stats.open}</h2>
        </div>

        <div
          onClick={() => navigate("/tickets?status=in_progress")}
          className="bg-white p-5 rounded-xl shadow hover:shadow-md cursor-pointer"
        >
          <p className="text-gray-500 text-sm">In Progress</p>
          <h2 className="text-3xl font-bold text-yellow-500">{stats.in_progress}</h2>
        </div>

        <div className="bg-white p-5 rounded-xl shadow hover:shadow-md">
          <p className="text-gray-500 text-sm">Closed</p>
          <h2 className="text-3xl font-bold text-green-500">{stats.closed}</h2>
        </div>

      </div>

      {/* 🔹 Recent Activity (ONLY admin/agent) */}
      {(role === "admin" || role === "agent") && (
        <div className="bg-white p-5 rounded-xl shadow mt-8">
          <h3 className="text-lg font-semibold mb-4">
            Recent Activity
          </h3>

          {loading ? (
            <p className="text-gray-500">Loading...</p>
          ) : recentTickets.length === 0 ? (
            <p className="text-gray-500">No recent tickets</p>
          ) : (
            <div className="space-y-3">
              {recentTickets.map((ticket) => (
                <div
                  key={ticket.id}
                  onClick={() => navigate(`/tickets/${ticket.id}`)} // ✅ only admin/agent reach here
                  className="flex justify-between items-center bg-gray-50 p-3 rounded-md cursor-pointer hover:bg-gray-100"
                >
                  <span className="text-sm font-medium">
                    #{ticket.id} {ticket.title}
                  </span>

                  <span
                    className={`text-xs font-semibold px-2 py-1 rounded ${
                      ticket.priority === "urgent"
                        ? "bg-purple-100 text-purple-700"
                        : ticket.priority === "high"
                        ? "bg-red-100 text-red-600"
                        : ticket.priority === "medium"
                        ? "bg-yellow-100 text-yellow-600"
                        : "bg-green-100 text-green-600"
                    }`}
                  >
                    {ticket.priority}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

    </div>
  );
}

export default Dashboard;