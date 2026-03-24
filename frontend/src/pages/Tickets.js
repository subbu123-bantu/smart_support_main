import { useEffect, useState,useCallback} from "react";
import { useLocation } from "react-router-dom";
import { getTickets, updateTicket } from "../services/api";

function Tickets() {
  const location = useLocation();

  const params = new URLSearchParams(location.search);
  const ticketStatus = params.get("status") || "";

  const [tickets, setTickets] = useState([]);
  const [page, setPage] = useState(1);
  const [nextPage, setNextPage] = useState(null);
  const [prevPage, setPrevPage] = useState(null);
  const [searchInput, setSearchInput] = useState("");
  const [priority, setPriority] = useState("all");
  const [loading, setLoading] = useState(false);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  //Extract status from URL


  const fetchTickets = useCallback(async () => {
  setLoading(true);

  try {
    const res = await getTickets(
      page,
      ticketStatus || null,
      priority === "all" ? null : priority,
      searchQuery || null
    );

    setTickets(res.data.results || []);
    setNextPage(res.data.next);
    setPrevPage(res.data.previous);

  } catch (err) {
    console.error(err);
  } finally {
    setLoading(false);
  }
}, [page, priority, searchQuery,ticketStatus]);

// useEffect
useEffect(() => {
  fetchTickets();
}, [fetchTickets]);

  const handleSearch = () => {
  setSearchQuery(searchInput);
  setPage(1);
  setIsSearchMode(true);
  };

  const handleClear = () => {
  setSearchInput("");
  setSearchQuery("");
  setPage(1);
  setIsSearchMode(false);
  };

  const handlePriority = (e) => {
    setPriority(e.target.value);
    setPage(1);
  };

  const handleNext = () => {
  if (!nextPage) return;
  setPage((p) => p + 1);
  };

  const handlePrev = () => {
    if (!prevPage) return;
    setPage((p) => p - 1);
  };

  const updateStatus = async (id, status) => {
    try {
      await updateTicket(id, { status });
      fetchTickets();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>All Tickets {ticketStatus && `(${ticketStatus})`}</h2>

      {/* Filters */}
      <div className="search-bar">
        <input
          placeholder="Search tickets..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />

        <button onClick={handleSearch}>Search</button>

        {isSearchMode && <button onClick={handleClear}>Clear</button>}

        <select
          value={priority}
          onChange={handlePriority}
          style={{ marginLeft: "10px" }}
        >
          <option value="all">All Priority</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>

      {loading && <p>Loading tickets...</p>}

      {/* Table */}
      <table border="1" cellPadding="10" width="100%">
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Description</th>
            <th>Category</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Update</th>
          </tr>
        </thead>

        <tbody>
          {tickets.length === 0 ? (
            <tr>
              <td colSpan="7">No tickets found</td>
            </tr>
          ) : (
            tickets.map((ticket, index) => (
              <tr key={ticket.id || index}>
                <td>{ticket.id}</td>
                <td>{ticket.title}</td>
                <td>{ticket.description}</td>
                <td>{ticket.category}</td>
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
            ))
          )}
        </tbody>
      </table>

      {/* Pagination */}
      {!isSearchMode && (
        <div style={{ marginTop: "15px" }}>
          <button onClick={handlePrev} disabled={!prevPage}>
            Previous
          </button>

          <span style={{ margin: "0 10px" }}>Page {page}</span>

          <button onClick={handleNext} disabled={!nextPage}>
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default Tickets;