import { useEffect, useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getTickets, updateTicket,getAgents, assignTicket } from "../services/api";
import { toast } from "react-toastify";

function Tickets() {
  const role = localStorage.getItem("role");
  const navigate = useNavigate();

  const [params] = useSearchParams();
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
  const [assignedFilter, setAssignedFilter] = useState(""); // ✅ add this
  const [agents, setAgents] = useState([]);

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getTickets(
        page,
        ticketStatus || null,
        priority === "all" ? null : priority,
        searchQuery || null,
        assignedFilter  // ✅ pass it here
      );
      setTickets(res.data.results || []);
      setNextPage(res.data.next);
      setPrevPage(res.data.previous);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [page, priority, searchQuery, ticketStatus, assignedFilter]); // ✅ add assignedFilter

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

  const handleNext = () => { if (nextPage) setPage((p) => p + 1); };
  const handlePrev = () => { if (prevPage) setPage((p) => p - 1); };

  const updateStatus = async (id, status) => {
    try {
      await updateTicket(id, { status });
      fetchTickets();
    } catch (err) {
      console.error(err);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case "urgent": return "bg-purple-100 text-purple-700";
      case "high": return "bg-red-100 text-red-600";
      case "medium": return "bg-yellow-100 text-yellow-600";
      case "low": return "bg-green-100 text-green-600";
      default: return "bg-gray-100 text-gray-600";
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "open": return "bg-red-100 text-red-600";
      case "in_progress": return "bg-yellow-100 text-yellow-600";
      case "closed": return "bg-green-100 text-green-600";
      default: return "bg-gray-100 text-gray-600";
    }
  };

  useEffect(() => {
    if (role === "admin") {
      getAgents().then(res => setAgents(res.data));
    }
  }, [role]);
  
  const handleAssign = async (ticketId, agentId) => {
  try {
    await assignTicket(ticketId, agentId);
    toast.success("Ticket assigned!");
    fetchTickets();
  } catch (err) {
    toast.error("Failed to assign ticket");
  }
};

  return (
    <div className="p-6">
      <h2 className="text-2xl font-semibold mb-6">Tickets</h2>

      {/* FILTER BAR */}
      <div className="flex gap-4 mb-6 items-center flex-wrap">
        <input
          placeholder="Search tickets..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          className="border px-4 py-2 rounded-lg w-1/3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button onClick={handleSearch} className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">
          Search
        </button>
        {isSearchMode && (
          <button onClick={handleClear} className="bg-gray-200 px-4 py-2 rounded-lg">
            Clear
          </button>
        )}
        <select value={priority} onChange={handlePriority} className="border px-4 py-2 rounded-lg">
          <option value="all">All Priority</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="urgent">Urgent</option>
        </select>

        {/* ✅ Assigned filter — only for admin */}
        {role === "admin" && (
          <select
            value={assignedFilter}
            onChange={(e) => { setAssignedFilter(e.target.value); setPage(1); }}
            className="border px-4 py-2 rounded-lg"
          >
            <option value="">All Tickets</option>
            <option value="true">Assigned</option>
            <option value="false">Unassigned</option>
          </select>
        )}
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
            className="cursor-pointer bg-white p-5 rounded-xl shadow-sm border border-gray-100 hover:shadow-md hover:scale-[1.02] transition transform"
          >
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold">{ticket.title}</h3>
                <p className="text-gray-500 text-sm mt-1">{ticket.description}</p>
                <div className="flex gap-2 mt-3">
                  <span className={`text-xs px-2 py-1 rounded ${getStatusColor(ticket.status)}`}>
                    {ticket.status}
                  </span>
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded">{ticket.category}</span>
                </div>
              </div>
              <div className="text-right">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPriorityColor(ticket.priority)}`}>
                  {ticket.priority}
                </span>
                <p className="text-xs text-gray-400 mt-2">#{ticket.id}</p>

                {/* ✅ show assigned agent name for admin */}
                {role === "admin" && (
                  <select
                    value={ticket.assigned_to || ""}
                    onClick={(e) => e.stopPropagation()}
                    onChange={(e) => handleAssign(ticket.id, e.target.value)}
                    className="mt-2 border px-2 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border-blue-200 cursor-pointer"
                  >
                    <option value="">⚠️ Unassigned</option>
                    {agents.map(agent => (
                      <option key={agent.id} value={agent.id}>
                        👤 {agent.username}
                      </option>
                    ))}
                  </select>
                )}
                {(role === "admin" || role === "agent") && (
                  <select
                    value={ticket.status}
                    onClick={(e) => e.stopPropagation()}
                    onChange={(e) => updateStatus(ticket.id, e.target.value)}
                    className="mt-2 border px-2 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border-blue-200 cursor-pointer"
                  >
                    <option value="open">Open</option>
                    <option value="in_progress">In Progress</option>
                    <option value="closed">Closed</option>
                  </select>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* PAGINATION */}
      {!isSearchMode && (
        <div className="flex items-center gap-4 mt-6">
          <button onClick={handlePrev} disabled={!prevPage} className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50">
            Previous
          </button>
          <span>Page {page}</span>
          <button onClick={handleNext} disabled={!nextPage} className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50">
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default Tickets;