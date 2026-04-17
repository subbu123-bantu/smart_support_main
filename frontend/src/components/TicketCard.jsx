import PropTypes from "prop-types";
import { useNavigate } from "react-router-dom";
import { PRIORITY_META } from "../constants";
import StatusBadge from "./StatusBadge";

function TicketCard({ ticket, role, categories, agents, onFieldUpdate, onStatusUpdate, onAssign }) {
  const navigate = useNavigate();
  const priorityMeta = PRIORITY_META[ticket.priority] || PRIORITY_META.low;

  const handleFieldUpdate = (field, value) => {
    if (onFieldUpdate) onFieldUpdate(ticket.id, { [field]: value });
  };

  const handleStatusUpdate = (value) => {
    if (onStatusUpdate) onStatusUpdate(ticket.id, value);
  };

  const handleAssign = (agentId) => {
    if (onAssign) onAssign(ticket.id, agentId);
  };

  const formatAgentLabel = (agent) => {
    const categoryNames = agent.category_names?.filter(Boolean) || [];

    if (categoryNames.length === 0) {
      return agent.username;
    }

    return `${agent.username} - ${categoryNames.join(", ")}`;
  };

  return (
    <button
      type="button"
      onClick={() => navigate(`/tickets/${ticket.id}`)}
      className="w-full text-left bg-white/[0.03] border border-white/10 rounded-2xl p-5 hover:border-indigo-500/30 hover:bg-indigo-500/5 transition cursor-pointer"
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
            <StatusBadge status={ticket.status} />
            <span className="bg-[#0f1117] border border-white/10 text-white rounded-xl px-3 py-2">
              {ticket.category_name || ticket.category}
            </span>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          <span className={`inline-flex items-center text-xs px-2.5 py-1 rounded-full border ${priorityMeta.bg} ${priorityMeta.color}`}>
            {priorityMeta.label}
          </span>

          {role === "admin" && (
            <>
              <select
                value={ticket.priority}
                onClick={(e) => e.stopPropagation()}
                onChange={(e) => handleFieldUpdate("priority", e.target.value)}
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
                onChange={(e) => handleFieldUpdate("category", e.target.value)}
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
              onChange={(e) => handleStatusUpdate(e.target.value)}
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
              onChange={(e) => handleAssign(e.target.value)}
              className="bg-[#0f1117] border border-white/10 text-white rounded-xl px-3 py-2"
            >
              <option value="">Unassigned</option>
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {formatAgentLabel(agent)}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>
    </button>
  );
}

TicketCard.propTypes = {
  ticket: PropTypes.object.isRequired,
  role: PropTypes.string.isRequired,
  categories: PropTypes.array.isRequired,
  agents: PropTypes.array.isRequired,
  onFieldUpdate: PropTypes.func,
  onStatusUpdate: PropTypes.func,
  onAssign: PropTypes.func,
};

export default TicketCard;
