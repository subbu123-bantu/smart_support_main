import { Link } from "react-router-dom";
import PropTypes from "prop-types";
import { statsShape } from "./propTypes";

function StatsCards({ stats, loadingStats }) {
  const cards = [
    {
      label: "Total Tickets",
      value: stats?.total ?? 0,
      to: "/tickets",
      valueColor: "text-white",
      hoverColor: "hover:border-indigo-500/20",
    },
    {
      label: "Open",
      value: stats?.open ?? 0,
      to: "/tickets?status=open",
      valueColor: "text-red-400",
      hoverColor: "hover:border-red-500/20",
    },
    {
      label: "In Progress",
      value: stats?.in_progress ?? 0,
      to: "/tickets?status=in_progress",
      valueColor: "text-amber-400",
      hoverColor: "hover:border-amber-500/20",
    },
    {
      label: "Closed",
      value: stats?.closed ?? 0,
      to: "/tickets?status=closed",
      valueColor: "text-emerald-400",
      hoverColor: "hover:border-emerald-500/20",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
      {cards.map((card) => (
        <Link
          key={card.label}
          to={card.to}
          className={`block bg-[#0f1117] border border-white/5 rounded-2xl p-5 transition-all duration-200 hover:bg-[#12151d] ${card.hoverColor}`}
        >
          <p className="text-gray-500 text-sm mb-2">{card.label}</p>
          <h2
            className={`text-3xl font-bold ${card.valueColor}`}
            style={{ letterSpacing: "-0.02em" }}
          >
            {loadingStats ? "..." : card.value}
          </h2>
        </Link>
      ))}
    </div>
  );
}

StatsCards.propTypes = {
  stats: statsShape.isRequired,
  loadingStats: PropTypes.bool.isRequired,
};

export default StatsCards;