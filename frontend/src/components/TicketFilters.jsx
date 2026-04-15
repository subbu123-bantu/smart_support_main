import PropTypes from "prop-types";
import { Search, X, Filter } from "lucide-react";

function TicketFilters({
  searchInput,
  onSearchInputChange,
  onSearch,
  onClear,
  isSearchMode,
  priority,
  onPriorityChange,
  selectedCategory,
  onCategoryChange,
  categories,
  assignedFilter,
  onAssignedChange,
  role,
  ticketCount,
}) {
  return (
    <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-4 mb-6 flex flex-wrap gap-3 items-center">
      <div className="relative flex-1 min-w-[200px]">
        <Search
          size={14}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
        />
        <input
          placeholder="Search tickets..."
          value={searchInput}
          onChange={(e) => onSearchInputChange(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
          className="w-full pl-9 pr-4 py-2 text-sm bg-white/5 border border-white/10 rounded-xl outline-none focus:border-indigo-500"
        />
      </div>

      <button
        onClick={onSearch}
        className="bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded-xl text-sm"
        type="button"
      >
        Search
      </button>

      {isSearchMode && (
        <button
          onClick={onClear}
          className="flex items-center gap-1 text-sm text-gray-400 hover:text-white"
          type="button"
        >
          <X size={14} />
          Clear
        </button>
      )}

      <div className="flex items-center gap-2 ml-auto">
        <Filter size={14} className="text-gray-500" />

        <select
          value={priority}
          onChange={onPriorityChange}
          className="bg-[#0f1117] border border-white/10 text-white rounded-xl px-3 py-2"
        >
          <option value="all">All Priority</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="urgent">Urgent</option>
        </select>

        {role === "admin" && (
          <>
            <select
              value={selectedCategory}
              onChange={onCategoryChange}
              className="bg-[#0f1117] border border-white/10 text-white rounded-xl px-3 py-2"
            >
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>

            <select
              value={assignedFilter}
              onChange={onAssignedChange}
              className="bg-[#0f1117] border border-white/10 text-white rounded-xl px-3 py-2"
            >
              <option value="">All</option>
              <option value="true">Assigned</option>
              <option value="false">Unassigned</option>
            </select>
          </>
        )}
      </div>
    </div>
  );
}

TicketFilters.propTypes = {
  searchInput: PropTypes.string.isRequired,
  onSearchInputChange: PropTypes.func.isRequired,
  onSearch: PropTypes.func.isRequired,
  onClear: PropTypes.func.isRequired,
  isSearchMode: PropTypes.bool.isRequired,
  priority: PropTypes.string.isRequired,
  onPriorityChange: PropTypes.func.isRequired,
  selectedCategory: PropTypes.string.isRequired,
  onCategoryChange: PropTypes.func.isRequired,
  categories: PropTypes.array.isRequired,
  assignedFilter: PropTypes.string.isRequired,
  onAssignedChange: PropTypes.func.isRequired,
  role: PropTypes.string.isRequired,
  ticketCount: PropTypes.number,
};

export default TicketFilters;
