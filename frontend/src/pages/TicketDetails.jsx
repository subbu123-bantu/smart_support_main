import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getTicketById } from "../services/api";
import { ArrowLeft, Tag, AlertCircle, Clock } from "lucide-react";
import TicketComments from "./TicketComments";

const role = localStorage.getItem("role");

const STATUS_META = {
  open:        { color: "text-red-400", bg: "bg-red-500/10 border-red-500/20", label: "Open" },
  in_progress: { color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20", label: "In Progress" },
  closed:      { color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20", label: "Closed" },
};

const PRIORITY_META = {
  urgent: "text-red-400 bg-red-500/10 border-red-500/20",
  high:   "text-orange-400 bg-orange-500/10 border-orange-500/20",
  medium: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  low:    "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
};

function TicketDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTicketById(id)
      .then(res => setTicket(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0c0e14] text-gray-500">
        Loading ticket...
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#0c0e14] text-center">
        <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-4">
          <AlertCircle size={24} className="text-gray-500" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Ticket not found</h2>
        <p className="text-gray-500 text-sm mb-6">This ticket may have been removed.</p>
        <button
          onClick={() => navigate("/tickets")}
          className="text-indigo-400 hover:text-indigo-300 text-sm"
        >
          ← Back to tickets
        </button>
      </div>
    );
  }

  const status = STATUS_META[ticket.status] || STATUS_META.open;

 return (
  <div className="min-h-screen bg-[#0c0e14] text-white p-6">
    <button
      onClick={() => navigate("/tickets")}
      className="mb-6 text-sm text-gray-400 hover:text-white transition flex items-center gap-2"
    >
      <ArrowLeft size={14} /> Back to tickets
    </button>

    <div className="max-w-3xl mx-auto space-y-6">
      <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-8">
        <div className="flex justify-between items-start mb-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs text-gray-500 font-mono">#{ticket.id}</span>

              <span className={`text-xs px-2 py-1 rounded-full border ${status.bg} ${status.color}`}>
                {status.label}
              </span>
            </div>

            <h1 className="text-2xl font-bold leading-tight">
              {ticket.title}
            </h1>
          </div>

          <span className={`text-xs px-3 py-1 rounded-full border ${PRIORITY_META[ticket.priority]}`}>
            {ticket.priority}
          </span>
        </div>

        <div className="mb-8">
          <p className="text-gray-500 text-xs uppercase tracking-wider mb-3">
            Description
          </p>

          <div className="bg-white/[0.02] border border-white/5 rounded-xl p-5">
            <p className="text-sm text-gray-300 leading-relaxed">
              {ticket.description}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2 text-gray-500 text-xs uppercase">
              <Tag size={12} /> Category
            </div>
            <p className="text-sm font-semibold capitalize">
              {ticket.category_name || ticket.category || "—"}
            </p>
          </div>

          <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2 text-gray-500 text-xs uppercase">
              <AlertCircle size={12} /> Priority
            </div>
            <p className="text-sm font-semibold capitalize">
              {ticket.priority}
            </p>
          </div>

          <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2 text-gray-500 text-xs uppercase">
              <Clock size={12} /> Assigned
            </div>
            <p className="text-sm font-semibold">
              {ticket.assigned_to_name || "Unassigned"}
            </p>
          </div>
        </div>
      </div>
      <TicketComments ticketId={id} role={role} />
    </div>
  </div>
);
}
export default TicketDetails;