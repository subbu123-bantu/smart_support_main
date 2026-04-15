import { useEffect, useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "react-toastify";
import { getTickets, updateTicket, getAgents, assignTicket, getCategories } from "../services/api";
import TicketCard from "../components/TicketCard";
import TicketFilters from "../components/TicketFilters";
import logger from "../utils/logger";

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
      const response = await getTickets(
        page,
        ticketStatus || null,
        priority === "all" ? null : priority,
        searchQuery || null,
        assignedFilter,
        categoryFilter
      );
      setTickets(response.data.results || []);
      setNextPage(response.data.next);
      setPrevPage(response.data.previous);
    } catch (error) {
      logger.error("Failed to fetch tickets:", error);
      setTickets([]);
      setNextPage(null);
      setPrevPage(null);
    } finally {
      setLoading(false);
    }
  }, [page, ticketStatus, priority, searchQuery, assignedFilter, categoryFilter]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  useEffect(() => {
    if (role !== "admin") return;
    getAgents()
      .then((response) => setAgents(response.data))
      .catch(() => setAgents([]));
  }, [role]);

  useEffect(() => {
    if (role !== "admin") return;
    getCategories()
      .then((response) => setCategories(response.data.results || response.data))
      .catch(() => setCategories([]));
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

  const handlePriorityChange = (e) => {
    setPriority(e.target.value);
    setPage(1);
  };

  const handleCategoryChange = (e) => {
    setSelectedCategory(e.target.value);
    setPage(1);
  };

  const handleAssignedChange = (e) => {
    setAssignedFilter(e.target.value);
    setPage(1);
  };

  const updateTicketAndRefresh = async (id, data, successMessage, errorMessage) => {
    try {
      await updateTicket(id, data);
      if (successMessage) toast.success(successMessage);
      await fetchTickets();
    } catch (error) {
      logger.error(error);
      toast.error(errorMessage);
    }
  };

  const handleStatusUpdate = async (id, status) => {
    await updateTicketAndRefresh(id, { status }, null, "Failed to update");
  };

  const handleFieldUpdate = async (id, data) => {
    await updateTicketAndRefresh(id, data, "Updated", "Update failed");
  };

  const handleAssign = async (ticketId, agentId) => {
    try {
      await assignTicket(ticketId, agentId);
      toast.success("Assigned");
      await fetchTickets();
    } catch (error) {
      logger.error(error);
      toast.error("Failed");
    }
  };

  const renderTicketList = () => {
    if (loading) {
      return <div className="text-center text-gray-500 py-20">Loading...</div>;
    }
    if (tickets.length === 0) {
      return <div className="text-center text-gray-500 py-20">No tickets found</div>;
    }
    return tickets.map((ticket) => (
      <TicketCard
        key={ticket.id}
        ticket={ticket}
        role={role}
        categories={categories}
        agents={agents}
        onFieldUpdate={handleFieldUpdate}
        onStatusUpdate={handleStatusUpdate}
        onAssign={handleAssign}
      />
    ));
  };

  return (
    <div className="min-h-screen bg-[#0c0e14] text-white p-6">
      <button
        onClick={() => navigate("/dashboard")}
        className="mb-6 text-sm text-gray-400 hover:text-white transition"
        type="button"
      >
        ← Back to Dashboard
      </button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold">Tickets</h1>
        <p className="text-gray-500 text-sm mt-1">{tickets.length} results</p>
      </div>

      <TicketFilters
        searchInput={searchInput}
        onSearchInputChange={setSearchInput}
        onSearch={handleSearch}
        onClear={handleClear}
        isSearchMode={isSearchMode}
        priority={priority}
        onPriorityChange={handlePriorityChange}
        selectedCategory={selectedCategory}
        onCategoryChange={handleCategoryChange}
        categories={categories}
        assignedFilter={assignedFilter}
        onAssignedChange={handleAssignedChange}
        role={role}
      />

      <div className="space-y-3">
        {renderTicketList()}
      </div>

      {!isSearchMode && (prevPage || nextPage) && (
        <div className="flex justify-between mt-6 text-sm text-gray-400">
          <button
            onClick={() => prevPage && setPage((p) => p - 1)}
            disabled={!prevPage}
            type="button"
          >
            ← Previous
          </button>
          <span>Page {page}</span>
          <button
            onClick={() => nextPage && setPage((p) => p + 1)}
            disabled={!nextPage}
            type="button"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}

export default Tickets;
