import { Link } from "react-router-dom";
import PropTypes from "prop-types";
import { ticketShape } from "./propTypes";
import PriorityBadge from "../PriorityBadge";

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

              <PriorityBadge priority={ticket.priority} />
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
