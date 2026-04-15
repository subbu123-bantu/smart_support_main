import PropTypes from "prop-types";
import { STATUS_META } from "../constants";

function StatusBadge({ status }) {
  const meta = STATUS_META[status] || STATUS_META.open;
  return (
    <span className={`inline-flex items-center text-xs px-2.5 py-1 rounded-full border ${meta.bg} ${meta.color}`}>
      {meta.label}
    </span>
  );
}

StatusBadge.propTypes = {
  status: PropTypes.string.isRequired,
};

export default StatusBadge;
