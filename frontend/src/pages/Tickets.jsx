import { useEffect, useState,useCallback,} from "react";
import {useNavigate,useSearchParams} from "react-router-dom";
import { getTickets, updateTicket } from "../services/api";

function Tickets() {
  const role = localStorage.getItem("role");
  const navigate = useNavigate();

  const [params]= useSearchParams();
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
const getPriorityColor = (priority) => {
  switch (priority?.toLowerCase()) {
    case "urgent":
      return "bg-purple-100 text-purple-700";
    case "high":
      return "bg-red-100 text-red-600";
    case "medium":
      return "bg-yellow-100 text-yellow-600";
    case "low":
      return "bg-green-100 text-green-600";
    default:
      return "bg-gray-100 text-gray-600";
  }
  };

const getStatusColor = (status) => {
  switch (status) {
    case "open":
      return "bg-red-100 text-red-600";
    case "in_progress":
      return "bg-yellow-100 text-yellow-600";
    case "closed":
      return "bg-green-100 text-green-600";
    default:
      return "bg-gray-100 text-gray-600";
  }
  };

  return (
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

<<<<<<< HEAD
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

            {/* LEFT */}
            <div>
              <h3 className="text-lg font-semibold">
                {ticket.title}
              </h3>

              <p className="text-gray-500 text-sm mt-1">
                {ticket.description}
              </p>

              <div className="flex gap-2 mt-3">
                <span className={`text-xs px-2 py-1 rounded ${getStatusColor(ticket.status)}`}>
                  {ticket.status}
                </span>

                <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                  {ticket.category}
                </span>
              </div>
=======
      {/* TICKET CARDS */}
      <div className="space-y-4 min-h-[300px]">
        {loading && <p>Loading...</p>}
        {tickets.map((ticket) => (
          <div
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
              <div className="text-right" key={ticket.id}>
  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPriorityColor(ticket.priority)}`}>
    {ticket.priority}
  </span>
  <p className="text-xs text-gray-400 mt-2">
  #{role === "customer" ? ticket.user_ticket_id : ticket.id}
  </p>

  {role === "admin" && (
    <select
      value={ticket.assigned_to || ""}
      onClick={(e) => e.stopPropagation()}
      onChange={(e) => handleAssign(ticket.id, e.target.value)}
      className="mt-2 border px-2 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border-blue-200 cursor-pointer"
    >
      <option value="">⚠️ Unassigned</option>

      {agents.filter(a =>
        a.categories?.some(cat =>
          cat.toLowerCase() === ticket.category?.toLowerCase()
        )
      ).length > 0 && (
        <optgroup key={`recommended-${ticket.id}`} label="⭐ Recommended">
          {agents
            .filter(a => a.categories?.some(cat =>
              cat.toLowerCase() === ticket.category?.toLowerCase()
            ))
            .map(agent => (
              <option key={`rec-${ticket.id}-${agent.id}`} value={agent.id}>
                👤 {agent.username} — {agent.categories.join(', ')}
                {!agent.is_available ? ' (busy)' : ''}
              </option>
            ))}
        </optgroup>
      )}

      <optgroup key={`others-${ticket.id}`} label="Other Agents">
        {agents
          .filter(a => !a.categories?.some(cat =>
            cat.toLowerCase() === ticket.category?.toLowerCase()
          ))
          .map(agent => (
            <option key={`other-${ticket.id}-${agent.id}`} value={agent.id}>
              👤 {agent.username} — {agent.categories.length > 0 ? agent.categories.join(', ') : 'No specialization'}
              {!agent.is_available ? ' (busy)' : ''}
            </option>
          ))}
      </optgroup>
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
>>>>>>> 815f769 (working on sending a mail to user)
            </div>

            {/* RIGHT */}
            <div className="text-right">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPriorityColor(ticket.priority)}`}>
                {ticket.priority}
              </span>

              <p className="text-xs text-gray-400 mt-2">
                #{ticket.id}
              </p>

              {(role === "admin" || role === "agent") && (
                <select
                  value={ticket.status}
                  onClick={(e) => e.stopPropagation()}
                  onChange={(e) =>
                    updateStatus(ticket.id, e.target.value)
                  }
                  className="mt-3 border px-2 py-1 rounded"
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
    {/* 🔁 Pagination */}
    {!isSearchMode && (
      <div className="flex items-center gap-4 mt-6">
        <button
          onClick={handlePrev}
          disabled={!prevPage}
          className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
        >
          Previous
        </button>

        <span>Page {page}</span>

        <button
          onClick={handleNext}
          disabled={!nextPage}
          className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
        >
          Next
        </button>
      </div>
    )}
  </div>
);
}

export default Tickets;