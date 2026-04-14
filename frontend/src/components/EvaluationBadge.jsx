function EvaluationBadge({ value }) {
  if (value === true) {
    return (
      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
        Correct
      </span>
    );
  }

  if (value === false) {
    return (
      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-500/10 border border-red-500/20 text-red-400">
        Incorrect
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 border border-amber-500/20 text-amber-400">
      Not evaluated
    </span>
  );
}

export default EvaluationBadge;