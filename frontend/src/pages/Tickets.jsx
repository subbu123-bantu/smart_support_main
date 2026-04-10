import { useEffect, useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getTickets, updateTicket, getAgents, assignTicket, getCategories } from "../services/api";
import { toast } from "react-toastify";
import { Search, X, Filter } from "lucide-react";

const PRIORITY_META = {
  low: {
    label: "Low",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10 border-emerald-500/20",
  },
  medium: {
    label: "Medium",
    color: "text-amber-400",
    bg: "bg-amber-500/10 border-amber-500/20",
  },
  high: {
    label: "High",
    color: "text-orange-400",
    bg: "bg-orange-500/10 border-orange-500/20",
  },
  urgent: {
    label: "Urgent",
    color: "text-red-400",
    bg: "bg-red-500/10 border-red-500/20",
  },
};

const STATUS_META = {
  open: {
    label: "Open",
    color: "text-red-400",
    bg: "bg-red-500/10 border-red-500/20",
  },
  in_progress: {
    label: "In Progress",
    color: "text-amber-400",
    bg: "bg-amber-500/10 border-amber-500/20",
  },
  closed: {
    label: "Closed",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10 border-emerald-500/20",
  },
};

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
  const [assignedFilter, setAssignedFilter] = useState("");
  const [agents, setAgents] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("");

  const categoryFilter = role === "admin" ? selectedCategory : null;

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getTickets(
        page,
        ticketStatus || null,
        priority === "all" ? null : priority,
        searchQuery || null,
        assignedFilter,
        categoryFilter
      );

      setTickets(res.data.results || []);
      setNextPage(res.data.next);
      setPrevPage(res.data.previous);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [page, ticketStatus, priority, searchQuery, assignedFilter, categoryFilter]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  useEffect(() => {
    if (role === "admin") {
      getAgents().then((res) => setAgents(res.data));
    }
  }, [role]);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const res = await getCategories();
        setCategories(res.data.results || res.data);
      } catch {
        console.error("Failed to load categories");
      }
    };

    if (role === "admin") {
      fetchCategories();
    }
  }, [role]);

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

  const updateStatus = async (id, status) => {
    try {
      await updateTicket(id, { status });
      fetchTickets();
    } catch {
      toast.error("Failed to update");
    }
  };

  const updateField = async (id, data) => {
    try {
      await updateTicket(id, data);
      toast.success("Updated");
      fetchTickets();
    } catch {
      toast.error("Update failed");
    }
  };

  const handleAssign = async (ticketId, agentId) => {
    try {
      await assignTicket(ticketId, agentId);
      toast.success("Assigned");
      fetchTickets();
    } catch {
      toast.error("Failed");
    }
  };

  return (
    <div className="min-h-screen bg-[#0c0e14] text-white p-6">
      <button
        onClick={() => navigate("/dashboard")}
        className="mb-6 text-sm text-gray-400 hover:text-white transition"
      >
        ← Back to Dashboard
      </button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold">Tickets</h1>
        <p className="text-gray-500 text-sm mt-1">{tickets.length} results</p>
      </div>

      <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-4 mb-6 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            placeholder="Search tickets..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="w-full pl-9 pr-4 py-2 text-sm bg-white/5 border border-white/10 rounded-xl outline-none focus:border-indigo-500"
          />
        </div>

        <button
          onClick={handleSearch}
          className="bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded-xl text-sm"
        >
          Search
        </button>

        {isSearchMode && (
          <button
            onClick={handleClear}
            className="flex items-center gap-1 text-sm text-gray-400 hover:text-white"
          >
            <X size={14} />
            Clear
          </button>
        )}

        <div className="flex items-center gap-2 ml-auto">
          <Filter size={14} className="text-gray-500" />

          <select
            value={priority}
            onChange={(e) => {
              setPriority(e.target.value);
              setPage(1);
            }}
            className="bg-[#0f1117] border border-white/10 text-white rounded-xl px-3 py-2"
          >
            <option value="all">All Priority</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>

          {role === "admin" && (
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                setPage(1);
              }}
              className="bg-[#0f1117] border border-white/10 text-white rounded-xl px-3 py-2"
            >
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          )}

          {role === "admin" && (
            <select
              value={assignedFilter}
              onChange={(e) => {
                setAssignedFilter(e.target.value);
                setPage(1);
              }}
              className="bg-[#0f1117] border border-white/10 text-white rounded-xl px-3 py-2"
            >
              <option value="">All</option>
              <option value="true">Assigned</option>
              <option value="false">Unassigned</option>
            </select>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {loading ? (
          <div className="text-center text-gray-500 py-20">Loading...</div>
        ) : tickets.length === 0 ? (
          <div className="text-center text-gray-500 py-20">No tickets found</div>
        ) : (
          tickets.map((ticket) => {
            const pri = PRIORITY_META[ticket.priority] || PRIORITY_META.low;
            const stat = STATUS_META[ticket.status] || STATUS_META.open;

            return (
              <div
                key={ticket.id}
                onClick={() => role !== "customer" && navigate(`/tickets/${ticket.id}`)}
                className="bg-white/[0.03] border border-white/10 rounded-2xl p-5 hover:border-indigo-500/30 hover:bg-indigo-500/5 transition cursor-pointer"
              >
                <div className="flex justify-between gap-4">
                  <div className="flex-1">
                    <p className="text-xs text-gray-500 mb-1">
                      #{role === "customer" ? ticket.user_ticket_id : ticket.id}
                    </p>

                    <h3 className="text-sm font-semibold">{ticket.title}</h3>
                    <p className="text-xs text-gray-500 mt-1 line-clamp-1">
                      {ticket.description}
                    </p>

                    <div className="flex gap-2 mt-3 flex-wrap">
                      <span
                        className={`inline-flex items-center text-xs px-2.5 py-1 rounded-full border ${stat.bg} ${stat.color}`}
                      >
                        {stat.label}
                      </span>

                      <span className="bg-[#0f1117] border border-white/10 text-white rounded-xl px-3 py-2">
                        {ticket.category_name || ticket.category}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-2">
                    <span
                      className={`inline-flex items-center text-xs px-2.5 py-1 rounded-full border ${pri.bg} ${pri.color}`}
                    >
                      {pri.label}
                    </span>

                    {role === "admin" && (
                      <>
                        <select
                          value={ticket.priority}
                          onClick={(e) => e.stopPropagation()}
                          onChange={(e) =>
                            updateField(ticket.id, { priority: e.target.value })
                          }
                          className="bg-[#0f1117] border border-white/10 text-white rounded-xl px-3 py-2"
                        >
                          <option value="low">Low</option>
                          <option value="medium">Medium</option>
                          <option value="high">High</option>
                          <option value="urgent">Urgent</option>
                        </select>

                        <select
                          value={ticket.category}
                          onClick={(e) => e.stopPropagation()}
                          onChange={(e) =>
                            updateField(ticket.id, { category: e.target.value })
                          }
                          className="bg-[#0f1117] border border-white/10 text-white rounded-xl px-3 py-2"
                        >
                          {categories.map((cat) => (
                            <option key={cat.id} value={cat.id}>
                              {cat.name}
                            </option>
                          ))}
                        </select>
                      </>
                    )}

                    {(role === "admin" || role === "agent") && (
                      <select
                        value={ticket.status}
                        onClick={(e) => e.stopPropagation()}
                        onChange={(e) => updateStatus(ticket.id, e.target.value)}
                        className="bg-[#0f1117] border border-white/10 text-white rounded-xl px-3 py-2"
                      >
                        <option value="open">Open</option>
                        <option value="in_progress">In Progress</option>
                        <option value="closed">Closed</option>
                      </select>
                    )}

                    {role === "admin" && (
                      <select
                        value={ticket.assigned_to || ""}
                        onClick={(e) => e.stopPropagation()}
                        onChange={(e) => handleAssign(ticket.id, e.target.value)}
                        className="bg-[#0f1117] border border-white/10 text-white rounded-xl px-3 py-2"
                      >
                        <option value="">Unassigned</option>
                        {agents.map((agent) => (
                          <option key={agent.id} value={agent.id}>
                            {agent.username}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {!isSearchMode && (prevPage || nextPage) && (
        <div className="flex justify-between mt-6 text-sm text-gray-400">
          <button onClick={() => prevPage && setPage((p) => p - 1)} disabled={!prevPage}>
            ← Previous
          </button>
          <span>Page {page}</span>
          <button onClick={() => nextPage && setPage((p) => p + 1)} disabled={!nextPage}>
            Next →
          </button>
        </div>
      )}
    </div>
  );
}

export default Tickets;