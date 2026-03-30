import { useEffect, useRef, useState } from "react";
import { getTickets, updateTicket } from "../services/api";

function Tickets() {
  const [tickets, setTickets] = useState([]);
  const [page, setPage] = useState(1);
  const [nextPage, setNextPage] = useState(null);
  const [prevPage, setPrevPage] = useState(null);
  const [searchInput, setSearchInput] = useState("");
  const [priority, setPriority] = useState("all");
  const [loading, setLoading] = useState(false);
  const [isSearchMode, setIsSearchMode] = useState(false);

  const pageRef = useRef(1);
  const priorityRef = useRef("all");
  const searchRef = useRef("");

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const res = await getTickets(
        pageRef.current,
        priorityRef.current,
        searchRef.current
      );
      console.log("FETCHING:", pageRef.current, priorityRef.current, searchRef.current);
      console.log("RESULTS:", res.data.results);
      setTickets(res.data.results || []);
      setNextPage(res.data.next);
      setPrevPage(res.data.previous);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const handleSearch = () => {
    if (searchInput.trim() === "") {
      handleClear();
      return;
    }
    searchRef.current = searchInput;
    pageRef.current = 1;
    setPage(1);
    setIsSearchMode(true);
    fetchTickets();
  };

  const handleClear = () => {
    searchRef.current = "";
    pageRef.current = 1;
    setPage(1);
    setSearchInput("");
    setIsSearchMode(false);
    fetchTickets();
  };

  const handlePriority = (e) => {
    priorityRef.current = e.target.value;
    pageRef.current = 1;
    setPage(1);
    setPriority(e.target.value);
    fetchTickets();
  };

  const handleNext = () => {
    const newPage = pageRef.current + 1;
    pageRef.current = newPage;
    setPage(newPage);
    fetchTickets();
  };

  const handlePrev = () => {
    const newPage = pageRef.current - 1;
    pageRef.current = newPage;
    setPage(newPage);
    fetchTickets();
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
<<<<<<< HEAD
    <div style={{ padding: "20px" }}>
      <h2>All Tickets</h2>
      <div style={{ marginBottom: "20px" }}>
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
=======
  <div className="p-6">
  <h2 className="text-2xl font-semibold mb-6">Tickets</h2>

  {/* FILTER BAR */}
  <div className="flex gap-4 mb-6 items-center">
    <input
      placeholder="Search tickets..."
      value={searchInput}
      onChange={(e) => setSearchInput(e.target.value)}
      onKeyDown={(e) => e.key === "Enter" && handleSearch()}
      className="border px-4 py-2 rounded-lg w-1/3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
    />

    <button
      onClick={handleSearch}
      className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
    >
      Search
    </button>

    {isSearchMode && (
      <button
        onClick={handleClear}
        className="bg-gray-200 px-4 py-2 rounded-lg"
      >
        Clear
      </button>
    )}

    <select
      value={priority}
      onChange={handlePriority}
      className="border px-4 py-2 rounded-lg"
    >
      <option value="all">All Priority</option>
      <option value="low">Low</option>
      <option value="medium">Medium</option>
      <option value="high">High</option>
      <option value="urgent">Urgent</option>
    </select>
  </div>

  {/* TICKET CARDS */}
    <div className="space-y-4 min-h-[300px]">
      {loading && <p>Loading...</p>}
      {tickets.map((ticket) => (
        <div
          key={ticket.id}
         onClick={() => {
            if (role === "admin" || role === "agent") {
              navigate(`/tickets/${ticket.id}`);
            }
          }}
          className="cursor-pointer bg-white p-5 rounded-xl shadow-sm border border-gray-100 
                    hover:shadow-md hover:scale-[1.02] transition transform "
        >
          <div className="flex  justify-between items-start">
>>>>>>> 6bee5ac (Auto predict)

      {loading && <p>Loading tickets...</p>}

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
                  onChange={(e) => updateStatus(ticket.id, e.target.value)}
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

      {!isSearchMode && (
        <div style={{ marginTop: "15px" }}>
          <button onClick={handlePrev} disabled={!prevPage}>Previous</button>
          <span style={{ margin: "0 10px" }}>Page {page}</span>
          <button onClick={handleNext} disabled={!nextPage}>Next</button>
        </div>
      )}
    </div>
  );
}

export default Tickets;