import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { getTicketById } from "../services/api";

function TicketDetails() {
  const { id } = useParams();
  const [ticket, setTicket] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getTicketById(id)
      .then(res => setTicket(res.data)) // adjust if res.data.ticket exists
      .catch(err => setError("Failed to load ticket"));
  }, [id]);

  if (error) return <p>{error}</p>;
  if (!ticket) return <p>Loading...</p>;

  return (
    <div>
      <h2>{ticket.title}</h2>
      <p>{ticket.description}</p>
      <p>Status: {ticket.status}</p>
      <p>Priority: {ticket.priority}</p>
    </div>
  );
}

export default TicketDetails;