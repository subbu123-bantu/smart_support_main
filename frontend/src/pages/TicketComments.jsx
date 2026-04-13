import { useEffect, useState } from "react";
import { getTicketComments, addTicketComment } from "../services/api";
import { toast } from "react-toastify";

function TicketComments({ ticketId, role }) {
  const [comments, setComments] = useState([]);
  const [message, setMessage] = useState("");
  const [isInternal, setIsInternal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const fetchComments = async () => {
    setLoading(true);
    try {
      const res = await getTicketComments(ticketId);
      const data = res.data.results || res.data;
      setComments(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
      toast.error("Failed to load comments");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (ticketId) fetchComments();
  });

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!message.trim()) {
      toast.error("Comment cannot be empty");
      return;
    }

    setSubmitting(true);
    try {
      await addTicketComment(ticketId, {
        message,
        is_internal: role === "customer" ? false : isInternal,
      });

      toast.success("Comment added");
      setMessage("");
      setIsInternal(false);
      fetchComments();
    } catch (err) {
      console.error(err);
      toast.error("Failed to add comment");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mt-8 bg-white/[0.03] border border-white/10 rounded-2xl p-5">
      <h3 className="text-lg font-semibold text-white mb-4">Comments</h3>

      {loading ? (
        <p className="text-sm text-gray-500">Loading comments...</p>
      ) : comments.length === 0 ? (
        <p className="text-sm text-gray-500">No comments yet</p>
      ) : (
        <div className="space-y-4 mb-6">
          {comments.map((comment) => (
            <div
              key={comment.id}
              className="bg-white/[0.02] border border-white/5 rounded-xl p-4"
            >
              <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-white">
                    {comment.username}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-gray-400 border border-white/10">
                    {comment.user_role}
                  </span>
                  {comment.is_internal && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                      Internal
                    </span>
                  )}
                </div>
                <span className="text-xs text-gray-500">
                  {new Date(comment.created_at).toLocaleString()}
                </span>
              </div>

              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                {comment.message}
              </p>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          rows={4}
          placeholder="Write a comment..."
          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 outline-none focus:border-indigo-500 resize-none"
        />

        {(role === "admin" || role === "agent") && (
          <label className="flex items-center gap-2 text-sm text-gray-400">
            <input
              type="checkbox"
              checked={isInternal}
              onChange={(e) => setIsInternal(e.target.checked)}
              className="accent-indigo-500"
            />
            Mark as internal note
          </label>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-xl transition"
        >
          {submitting ? "Posting..." : "Add Comment"}
        </button>
      </form>
    </div>
  );
}

export default TicketComments;