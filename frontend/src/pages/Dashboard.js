import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { getTickets, updateTicket } from "../services/api";

function Dashboard() {

  const [tickets, setTickets] = useState([]);
  const [search, setSearch] = useState("");
  const [priority, setPriority] = useState("all");
  const [loading, setLoading] = useState(false);

  /* -------- Fetch Tickets -------- */

  const fetchTickets = useCallback(async () => {

    setLoading(true);

    try {

      const res = await getTickets();

      let data = res.data.results || res.data;

      // Apply search filter
       if (search.trim() !== "") {
      data = data.filter((ticket) =>
        ticket.title.toLowerCase().includes(search.toLowerCase()) ||
        ticket.description.toLowerCase().includes(search.toLowerCase())
      );
      }

      // Apply priority filter
      if (priority !== "all") {
        data = data.filter(ticket => ticket.priority === priority);
      }

      setTickets(data);

    } catch (error) {

      console.error("Error fetching tickets:", error);

    }

    setLoading(false);

  }, [search, priority]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  /* -------- Update Ticket Status -------- */

  const updateStatus = async (id, status) => {

    try {

      await updateTicket(id, { status });

      fetchTickets(); // refresh tickets

    } catch (error) {

      console.error("Error updating ticket:", error);

    }
  };

  /* -------- Dashboard Metrics -------- */

  const totalTickets = tickets.length;

  const openTickets = tickets.filter(
    (ticket) => ticket.status === "open"
  ).length;

  const progressTickets = tickets.filter(
    (ticket) => ticket.status === "in_progress"
  ).length;

  const closedTickets = tickets.filter(
    (ticket) => ticket.status === "closed"
  ).length;

  return (
    <div style={{ padding: "20px" }}>

      <h2>Support Tickets Dashboard</h2>

      <Link to="/create-ticket">
        <button style={{ marginBottom: "20px" }}>
          Create Ticket
        </button>
      </Link>

      {/* Search + Filter */}

      <div style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>

        <input
          placeholder="Search tickets..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ padding: "6px" }}
        />

        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          style={{ padding: "6px" }}
        >
          <option value="all">All Priority</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>

      </div>

      {/* Ticket Statistics */}

      <div style={{ display: "flex", gap: "20px", marginBottom: "20px" }}>

        <div style={{ padding: "12px", border: "1px solid #ddd", borderRadius: "6px" }}>
          Total: {totalTickets}
        </div>

        <div style={{ padding: "12px", border: "1px solid #ddd", borderRadius: "6px" }}>
          Open: {openTickets}
        </div>

        <div style={{ padding: "12px", border: "1px solid #ddd", borderRadius: "6px" }}>
          In Progress: {progressTickets}
        </div>

        <div style={{ padding: "12px", border: "1px solid #ddd", borderRadius: "6px" }}>
          Closed: {closedTickets}
        </div>

      </div>

      {/* Loading */}

      {loading && <p>Loading tickets...</p>}

      {/* Tickets Table */}

      <table border="1" cellPadding="10" width="100%">

        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Description</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Update</th>
          </tr>
        </thead>

        <tbody>

          {tickets.map((ticket) => (
            <tr key={ticket.id}>

              <td>{ticket.id}</td>
              <td>{ticket.title}</td>
              <td>{ticket.description}</td>
              <td>{ticket.priority}</td>
              <td>{ticket.status}</td>

              <td>

                <select
                  value={ticket.status}
                  onChange={(e) =>
                    updateStatus(ticket.id, e.target.value)
                  }
                >

                  <option value="open">Open</option>
                  <option value="in_progress">In Progress</option>
                  <option value="closed">Closed</option>

                </select>

              </td>

            </tr>
          ))}

        </tbody>

      </table>

    </div>
  );
}

export default Dashboard;