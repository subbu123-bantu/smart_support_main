import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { createTicket, predictTicket } from "../services/api";

function CreateTicket() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  // Internal AI-assigned values
  const [category, setCategory] = useState("other");
  const [priority, setPriority] = useState("low");
  const [autoAssign, setAutoAssign] = useState(true); // true = confident, false = goes to admin

  const navigate = useNavigate();

  // Predict category & priority behind the scenes
  const handleAutoPredict = async (text) => {
    if (!text) return;
    setLoading(true);
    try {
      const res = await predictTicket({ text });
      setCategory(res.data.predicted_category);
      setPriority(res.data.predicted_priority);

      // If AI confidence is low, mark for admin review
      const catConf = res.data.category_confidence;
      const priConf = res.data.priority_confidence;
      setAutoAssign(catConf >= 0.7 && priConf >= 0.7);

    } catch (err) {
      console.error("Prediction error:", err);
      setAutoAssign(false);
    } finally {
      setLoading(false);
    }
  };

  // Debounce AI prediction
  useEffect(() => {
    const timer = setTimeout(() => handleAutoPredict(description), 500);
    return () => clearTimeout(timer);
  }, [description]);

  // Submit ticket (category & priority sent to backend)
  const handleSubmit = async (e) => {
  e.preventDefault();

  try {
    await createTicket({
      title,
      description,
      category,
      priority,
      auto_assign: autoAssign,
    });

    navigate("/tickets"); // only on success

  } catch (err) {
    console.log(err.response?.data); //  THIS is what you need
  }
  };

  return (
    <div className="create-ticket-container">
      <form className="create-ticket-card" onSubmit={handleSubmit}>
        <h2>Create Ticket</h2>

        <input
          className="ticket-input"
          type="text"
          placeholder="Ticket Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />

        <textarea
          className="ticket-textarea"
          placeholder="Describe your issue"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
        />

        {loading && <p style={{ color: "#555" }}>AI is assigning category & priority...</p>}

        {!loading && !autoAssign && (
          <p style={{ color: "orange" }}>Low confidence prediction - ticket will be assigned to admin for review.</p>
        )}

        <button className="create-ticket-btn" type="submit">
          Create Ticket
        </button>
      </form>
    </div>
  );
}

export default CreateTicket;