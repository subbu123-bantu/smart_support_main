import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { createTicket, predictTicket } from "../services/api";

function CreateTicket() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  const [category, setCategory] = useState("other");
  const [priority, setPriority] = useState("low");
  const [autoAssign, setAutoAssign] = useState(true);

  const role = localStorage.getItem("role");
  const navigate = useNavigate();

  const handleAutoPredict = async (text) => {
    if (!text) return;

    try {
      const res = await predictTicket({ text });
      setCategory(res.data.predicted_category);
      setPriority(res.data.predicted_priority);

      const catConf = res.data.category_confidence;
      const priConf = res.data.priority_confidence;

      setAutoAssign(catConf >= 0.7 && priConf >= 0.7);

    } catch {
      setAutoAssign(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => handleAutoPredict(description), 500);
    return () => clearTimeout(timer);
  }, [description]);

  const handleSubmit = async (e) => {
  e.preventDefault();

  if (loading) return;  // 🔒 prevent duplicate

  setLoading(true);

  try {
    await createTicket({
      title,
      description,
      category,
      priority,
      auto_assign: autoAssign,
    });

    navigate("/tickets");
  } finally {
    setLoading(false);
  }
};
  return (
 <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-indigo-200 via-purple-100 to-gray-100">

  <div className="bg-white/80 backdrop-blur-md p-8 rounded-2xl shadow-xl w-full max-w-md">

    <h2 className="text-2xl font-semibold text-center mb-6">
      Create Ticket
    </h2>

    <form onSubmit={handleSubmit} className="space-y-4">

      <input
        type="text"
        placeholder="Ticket Title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400"
      />

      <textarea
        placeholder="Describe your issue"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        className="w-full px-4 py-2 border rounded-lg h-28 resize-none focus:ring-2 focus:ring-indigo-400"
      />

      {loading && (
        <p className="text-sm text-indigo-500">
          🤖 AI analyzing...
        </p>
      )}

      {!loading && !autoAssign && (
        <p className="text-sm text-yellow-500">
          ⚠️ Sent to admin for review
        </p>
      )}

      <button className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition shadow-md">
        Create Ticket
      </button>

    </form>

  </div>
</div>
);
}

export default CreateTicket;