import PropTypes from "prop-types";

function FeedbackCard({ title, children }) {
  return (
    <div className="bg-white/[0.03] border border-white/5 rounded-xl p-4">
      <p className="text-xs text-gray-600 mb-2 uppercase tracking-wider">
        {title}
      </p>
      {children}
    </div>
  );
}

FeedbackCard.propTypes = {
  title: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
};

export default FeedbackCard;