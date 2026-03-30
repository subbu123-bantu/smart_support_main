import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getTicketStats } from "../services/api";

function Dashboard() {

  const [stats, setStats] = useState({
    total: 0,
    open: 0,
    in_progress: 0,
    closed: 0
  });

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

  return (
<<<<<<< HEAD
    <div style={{ padding: "20px" }}>
=======
    <div className="p-6 bg-gray-100 min-h-screen overflow-y-">
>>>>>>> 6bee5ac (Auto predict)

      <h2>Support Tickets Dashboard</h2>

      {/* Navigation Buttons */}
      <div style={{ marginBottom: "20px" }}>
        <Link to="/tickets">
          <button>View All Tickets</button>
        </Link>

        <Link to="/create-ticket">
          <button style={{ marginLeft: "10px" }}>
            Create Ticket
          </button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div style={{ display: "flex", gap: "20px" }}>

        <div style={cardStyle}>
          <h3>Total Tickets</h3>
          <p>{stats.total}</p>
        </div>

        <div style={cardStyle}>
          <h3>Open</h3>
          <p>{stats.open}</p>
        </div>

        <div style={cardStyle}>
          <h3>In Progress</h3>
          <p>{stats.in_progress}</p>
        </div>

<<<<<<< HEAD
        <div style={cardStyle}>
          <h3>Closed</h3>
          <p>{stats.closed}</p>
=======
        <div className="bg-white p-5 rounded-xl shadow hover:shadow-md cursor-pointer"
           onClick={() => navigate("/tickets?status=closed")} >
          <p className="text-gray-500 text-sm">Closed</p>
          <h2 className="text-3xl font-bold text-green-500">{stats.closed}</h2>
>>>>>>> 6bee5ac (Auto predict)
        </div>

      </div>

    </div>
  );
}

const cardStyle = {
  padding: "20px",
  border: "1px solid #ddd",
  borderRadius: "6px",
  width: "150px",
  textAlign: "center"
};

export default Dashboard;