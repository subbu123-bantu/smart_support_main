import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { createTicket, predictTicket } from "../services/api";
import { toast } from "react-toastify";

const CATEGORY_META = {
  billing:        { icon: "💳", label: "Billing" },
  technical:      { icon: "🔧", label: "Technical" },
  authentication: { icon: "🔐", label: "Authentication" },
  network:        { icon: "📡", label: "Network" },
  account:        { icon: "👤", label: "Account" },
  other:          { icon: "📂", label: "Other" },
};

const PRIORITY_META = {
  low:    { color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20", dot: "bg-emerald-400" },
  medium: { color: "text-amber-400",   bg: "bg-amber-500/10 border-amber-500/20",   dot: "bg-amber-400"   },
  high:   { color: "text-orange-400",  bg: "bg-orange-500/10 border-orange-500/20",  dot: "bg-orange-400"  },
  urgent: { color: "text-red-400",     bg: "bg-red-500/10 border-red-500/20",        dot: "bg-red-400"     },
};

function CreateTicket() {
  const [title, setTitle]           = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [predicting, setPredicting] = useState(false);

  const [category, setCategory] = useState("other");
  const [priority, setPriority] = useState("low");
  const [autoAssign, setAutoAssign] = useState(true);
  const [confidence, setConfidence] = useState(null);

  const navigate = useNavigate();

  const handleAutoPredict = async (text) => {
    if (!text || text.trim().length < 10) return;
    setPredicting(true);
    try {
      const res = await predictTicket({ text });
      setCategory(res.data.predicted_category || "other");
      setPriority(res.data.predicted_priority || "low");
      const catConf = res.data.category_confidence ?? res.data.confidence;
      const priConf = res.data.priority_confidence ?? 1;
      setConfidence(catConf);
      setAutoAssign(catConf >= 0.7 && priConf >= 0.7);
    } catch {
      setAutoAssign(false);
      setConfidence(null);
    } finally {
      setPredicting(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => handleAutoPredict(description), 600);
    return () => clearTimeout(timer);
  }, [description]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (submitting) return;

    if (!title.trim() || !description.trim()) {
      toast.error("Please fill in both fields");
      return;
    }

    setSubmitting(true);
    try {
      await createTicket({
        title: title.trim(),
        description: description.trim(),
      });

      toast.success("Ticket submitted!");
      navigate("/tickets");
    } catch (err) {
      console.log(err.response?.data);
      toast.error(
        err.response?.data?.detail ||
        err.response?.data?.category?.[0] ||
        "Failed to create ticket"
      );
    } finally {
      setSubmitting(false);
    }
  };
  const catMeta  = CATEGORY_META[category]  || CATEGORY_META.other;
  const priMeta  = PRIORITY_META[priority]   || PRIORITY_META.low;

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif" }} className="flex min-h-screen bg-[#0c0e14]">

      {/* ── Left Panel ── */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 bg-[#0f1117] border-r border-white/5">

        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M2 4h5v5H2zM9 7h5v5H9z" fill="white" opacity="0.9"/>
              <path d="M2 10h3v4H2zM11 2h3v4h-3z" fill="white" opacity="0.5"/>
            </svg>
          </div>
          <span className="text-white font-semibold text-lg tracking-tight">Smart Support</span>
        </div>

        {/* Center content */}
        <div>
          <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-4 py-1.5 mb-8">
            <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
            <span className="text-indigo-400 text-xs font-medium tracking-wide">AI classifies as you type</span>
          </div>

          <h1 className="text-5xl font-bold text-white leading-tight mb-6" style={{ letterSpacing: "-0.03em" }}>
            Tell us what's<br />
            <span className="text-indigo-400">going wrong.</span>
          </h1>
          <p className="text-gray-500 text-lg leading-relaxed max-w-sm mb-10">
            Describe your issue and our AI will instantly classify it, set a priority, and route it to the right team.
          </p>

          {/* Live AI Preview Card */}
          <div className="bg-white/[0.03] border border-white/8 rounded-2xl p-5">
            <p className="text-gray-600 text-xs uppercase tracking-widest mb-4">AI prediction preview</p>

            <div className="flex items-center justify-between mb-3">
              <span className="text-gray-500 text-sm">Category</span>
              <span className="flex items-center gap-2 text-sm text-white font-medium">
                {predicting ? (
                  <svg className="animate-spin w-3.5 h-3.5 text-indigo-400" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                  </svg>
                ) : (
                  <span>{catMeta.icon}</span>
                )}
                {catMeta.label}
              </span>
            </div>

            <div className="flex items-center justify-between mb-4">
              <span className="text-gray-500 text-sm">Priority</span>
              <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border ${priMeta.bg} ${priMeta.color}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${priMeta.dot}`}/>
                {priority.charAt(0).toUpperCase() + priority.slice(1)}
              </span>
            </div>

            {/* Confidence bar */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-gray-600 text-xs">Confidence</span>
                <span className="text-gray-500 text-xs">
                  {confidence != null ? `${Math.round(confidence * 100)}%` : "—"}
                </span>
              </div>
              <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: confidence != null ? `${Math.round(confidence * 100)}%` : "0%",
                    background: confidence != null
                      ? confidence >= 0.8 ? "#6366f1" : confidence >= 0.6 ? "#f59e0b" : "#ef4444"
                      : "#6366f1",
                  }}
                />
              </div>
            </div>

            {!autoAssign && confidence != null && (
              <p className="text-amber-500/80 text-xs mt-3 flex items-center gap-1.5">
                <span>⚠</span> Low confidence — sent for admin review
              </p>
            )}
          </div>
        </div>

        <p className="text-gray-700 text-sm">© 2026 Smart Support. All rights reserved.</p>
      </div>

      {/* ── Right Panel — Form ── */}
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="w-full max-w-sm">

          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-2 mb-10">
            <div className="w-7 h-7 rounded-md bg-indigo-500 flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M2 4h5v5H2zM9 7h5v5H9z" fill="white"/>
              </svg>
            </div>
            <span className="text-white font-semibold">Smart Support</span>
          </div>

          <h2 className="text-2xl font-bold text-white mb-1" style={{ letterSpacing: "-0.02em" }}>
            New support ticket
          </h2>
          <p className="text-gray-500 text-sm mb-8">We'll route your issue to the right team automatically.</p>

          {/* Mobile — AI pill */}
          <div className="flex lg:hidden items-center gap-2 mb-6">
            {predicting ? (
              <span className="inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <svg className="animate-spin w-3 h-3" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                </svg>
                AI analyzing...
              </span>
            ) : confidence != null ? (
              <span className="inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-gray-400">
                {catMeta.icon} {catMeta.label} · <span className={priMeta.color}>{priority}</span>
              </span>
            ) : null}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">
                Ticket title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Brief summary of the issue"
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition-all duration-200"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the issue in detail — what happened, when, and any error messages…"
                rows={5}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition-all duration-200 resize-none"
              />
              <p className="text-gray-700 text-xs mt-1.5">
                {description.length < 10
                  ? `${10 - description.length} more characters for AI analysis`
                  : "AI is analyzing your description…"}
              </p>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 rounded-xl transition-all duration-200 text-sm flex items-center justify-center gap-2"
            >
              {submitting ? (
                <>
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                  </svg>
                  Submitting…
                </>
              ) : "Submit ticket"}
            </button>

          </form>

          <div className="mt-6 pt-6 border-t border-white/5 text-center">
            <p className="text-gray-600 text-sm">
              Changed your mind?{" "}
              <span
                onClick={() => navigate("/tickets")}
                className="text-indigo-400 cursor-pointer hover:text-indigo-300 transition-colors"
              >
                Back to tickets
              </span>
            </p>
          </div>

        </div>
      </div>
    </div>
  );
}

export default CreateTicket;