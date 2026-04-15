import PropTypes from "prop-types";
import { PRIORITY_META } from "../constants";

function PriorityBadge({ priority }) {
  const meta = PRIORITY_META[priority] || PRIORITY_META.low;
  return (
    <span className={`inline-flex items-center text-xs px-2.5 py-1 rounded-full border ${meta.bg} ${meta.color}`}>
      {meta.label}
    </span>
  );
}

PriorityBadge.propTypes = {
  priority: PropTypes.string.isRequired,
};

export default PriorityBadge;
