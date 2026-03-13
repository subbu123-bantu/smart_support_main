import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { getTickets, updateTicket } from "../services/api";

function Dashboard() {
  const [tickets, setTickets] = useState([]);
  const [searchInput, setSearchInput] = useState("");      // what user types
  const [searchResults, setSearchResults] = useState([]);  // search-only results
  const [isSearching, setIsSearching] = useState(false);   // are we in search mode?
  const [priority, setPriority] = useState("all");
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [nextPage, setNextPage] = useState(null);
  const [prevPage, setPrevPage] = useState(null);
  const [total, setTotal] = useState(0);

  /* -------- Fetch Paginated Tickets (no search) -------- */
  const fetchTickets = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getTickets(page, priority);
      const apiData = res.data;

      setTickets(apiData.results || []);
      setTotal(apiData.count);
      setNextPage(apiData.next);
      setPrevPage(apiData.previous);
    } catch (error) {
      console.error("Error fetching tickets:", error);
    } finally {
      setLoading(false);
    }
  }, [page, priority]);

  useEffect(() => {
    if (!isSearching) fetchTickets();
  }, [fetchTickets, isSearching]);

  /* -------- Search (calls backend with ?search=) -------- */
 const handleSearch = async () => {
  if (searchInput.trim() === "") {
    setIsSearching(false);
    setSearchResults([]);
    return;
  }

  setIsSearching(true);
  setLoading(true);

  try {
    let allResults = [];
    let currentPage = 1;
    let hasMore = true;

    while (hasMore) {
      const res = await getTickets(currentPage, priority, searchInput);
      const data = res.data;

      console.log("=== SEARCH DEBUG ===");
      console.log("Page fetched:", currentPage);
      console.log("Full response:", data);
      console.log("Results array:", data.results);
      console.log("Has next:", data.next);

      allResults = [...allResults, ...(data.results || [])];

      if (data.next) {
        currentPage += 1;
      } else {
        hasMore = false;
      }
    }

    console.log("FINAL allResults:", allResults);
    setSearchResults(allResults);
  } catch (error) {
    console.error("Search error:", error);
  } finally {
    setLoading(false);
  }
};

  const clearSearch = () => {
    setSearchInput("");
    setSearchResults([]);
    setIsSearching(false);
  };

  /* -------- Update Ticket Status -------- */
  const updateStatus = async (id, status) => {
    try {
      await updateTicket(id, { status });
      if (isSearching) {
        handleSearch(); // refresh search results
      } else {
        fetchTickets();
      }
    } catch (error) {
      console.error("Error updating ticket:", error);
    }
  };

  /* -------- Reset page on priority change -------- */
  const handlePriorityChange = (e) => {
    setPriority(e.target.value);
    setPage(1);
  };

  const totalTickets = total;
  const openTickets = tickets.filter(t => t.status === "open").length;
  const progressTickets = tickets.filter(t => t.status === "in_progress").length;
  const closedTickets = tickets.filter(t => t.status === "closed").length;

  const TicketTable = ({ data }) => (
    <table border="1" cellPadding="10" width="100%">
      <thead>
        <tr>
          <th>ID</th><th>Title</th><th>Description</th>
          <th>Priority</th><th>Status</th><th>Update</th>
        </tr>
      </thead>
      <tbody>
        {data.map((ticket) => (
          <tr key={ticket.id}>
            <td>{ticket.id}</td>
            <td>{ticket.title}</td>
            <td>{ticket.description}</td>
            <td>{ticket.priority}</td>
            <td>{ticket.status}</td>
            <td>
              <select
                value={ticket.status ?? "open"}
                onChange={(e) => updateStatus(ticket.id, e.target.value)}
              >
                <option value="open">Open</option>
                <option value="in_progress">In Progress</option>
                <option value="closed">Closed</option>
              </select>
            </td>
            <td>{ticket.status ?? "open"}</td>
          </tr>
        ))}
        {data.length === 0 && !loading && (
          <tr><td colSpan="6">No tickets found</td></tr>
        )}
      </tbody>
    </table>
  );

  return (
    <div style={{ padding: "20px" }}>
      <h2>Support Tickets Dashboard</h2>

      <Link to="/create-ticket">
        <button style={{ marginBottom: "20px" }}>Create Ticket</button>
      </Link>

      {/* Search + Filter */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
        <input
          placeholder="Search tickets..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          style={{ padding: "6px" }}
        />
        <button onClick={handleSearch}>Search</button>
        {isSearching && <button onClick={clearSearch}>Clear</button>}

        <select value={priority} onChange={handlePriorityChange} style={{ padding: "6px" }}>
          <option value="all">All Priority</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>

      {/* Stats */}
      <div style={{ display: "flex", gap: "20px", marginBottom: "20px" }}>
        <div style={{ padding: "12px", border: "1px solid #ddd", borderRadius: "6px" }}>Total: {totalTickets}</div>
        <div style={{ padding: "12px", border: "1px solid #ddd", borderRadius: "6px" }}>Open: {openTickets}</div>
        <div style={{ padding: "12px", border: "1px solid #ddd", borderRadius: "6px" }}>In Progress: {progressTickets}</div>
        <div style={{ padding: "12px", border: "1px solid #ddd", borderRadius: "6px" }}>Closed: {closedTickets}</div>
      </div>

      {loading && <p>Loading tickets...</p>}

      {/* Search Results (separate section) */}
      {isSearching && (
        <div>
          <h3>Search Results for "{searchInput}" ({searchResults.length} found)</h3>
          <TicketTable data={searchResults} />
        </div>
      )}

      {/* Main Paginated Table (always visible) */}
      {!isSearching && (
        <div>
          <h3>All Tickets</h3>
          <TicketTable data={tickets} />

          <div style={{ marginTop: "10px" }}>
            <button onClick={() => setPage(p => p - 1)} disabled={!prevPage}>Previous</button>
            <span style={{ margin: "0 10px" }}>Page {page}</span>
            <button onClick={() => setPage(p => p + 1)} disabled={!nextPage}>Next</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;