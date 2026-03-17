import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createTicket } from "../services/api";

function CreateTicket() {

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    await createTicket({
      title,
      description
    });

    navigate("/tickets");
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
        />

        <textarea
          className="ticket-textarea"
          placeholder="Describe your issue"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />

        <button className="create-ticket-btn">
          Create Ticket
        </button>

      </form>

    </div>
  );
}

export default CreateTicket;