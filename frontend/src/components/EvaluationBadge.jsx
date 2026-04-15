import PropTypes from "prop-types";

function EvaluationBadge({ value }) {
  let label = "Pending";
  let styles =
    "inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium bg-yellow-500/10 text-yellow-400 border-yellow-500/20";

  if (value === true) {
    label = "Correct";
    styles =
      "inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium bg-green-500/10 text-green-400 border-green-500/20";
  } else if (value === false) {
    label = "Incorrect";
    styles =
      "inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium bg-red-500/10 text-red-400 border-red-500/20";
  }

  return <span className={styles}>{label}</span>;
}

EvaluationBadge.propTypes = {
  value: PropTypes.oneOfType([PropTypes.bool, PropTypes.oneOf([null])]),
};

export default EvaluationBadge;