import { Link } from "react-router-dom";
import PropTypes from "prop-types";
import { ticketShape } from "./propTypes";

const PRIORITY_META = {
  low: {
    color: "text-emerald-400",
    bg: "bg-emerald-500/10 border-emerald-500/20",
  },
  medium: {
    color: "text-amber-400",
    bg: "bg-amber-500/10 border-amber-500/20",
  },
  high: {
    color: "text-orange-400",
    bg: "bg-orange-500/10 border-orange-500/20",
  },
  urgent: {
    color: "text-red-400",
    bg: "bg-red-500/10 border-red-500/20",
  },
};

function RecentTicketsSection({ loadingTickets, recentTickets }) {
  let content;

  if (loadingTickets) {
    content = <p className="text-gray-500 text-sm">Loading...</p>;
  } else if (recentTickets.length === 0) {
    content = <p className="text-gray-500 text-sm">No recent tickets</p>;
  } else {
    content = (
      <div className="space-y-3">
        {recentTickets.map((ticket) => {
          const meta = PRIORITY_META[ticket.priority] || PRIORITY_META.low;

          return (
            <Link
              key={ticket.id}
              to={`/tickets/${ticket.id}`}
              className="flex justify-between items-center p-4 rounded-xl bg-white/[0.03] border border-white/5 hover:border-indigo-500/20 hover:bg-indigo-500/5 transition-all duration-200"
            >
              <div>
                <p className="text-sm font-medium text-white">
                  #{ticket.id} {ticket.title}
                </p>
              </div>

              <span
                className={`text-xs px-3 py-1 rounded-full border ${meta.bg} ${meta.color}`}
              >
                {ticket.priority}
              </span>
            </Link>
          );
        })}
      </div>
    );
  }

  return (
    <div className="bg-[#0f1117] border border-white/5 rounded-2xl p-5">
      <h3 className="text-lg font-semibold mb-1 text-white">Recent Tickets</h3>
      <p className="text-xs text-gray-600 mb-5">
        Latest ticket activity across the workspace
      </p>
      {content}
    </div>
  );
}

RecentTicketsSection.propTypes = {
  loadingTickets: PropTypes.bool.isRequired,
  recentTickets: PropTypes.arrayOf(ticketShape).isRequired,
};

export default RecentTicketsSection;