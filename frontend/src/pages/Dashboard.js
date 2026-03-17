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
    <div style={{ padding: "20px" }}>

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

        <div style={cardStyle}>
          <h3>Closed</h3>
          <p>{stats.closed}</p>
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