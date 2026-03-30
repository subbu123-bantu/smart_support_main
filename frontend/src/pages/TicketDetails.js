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
<<<<<<< HEAD
    <div>
      <h2>{ticket.title}</h2>
      <p>{ticket.description}</p>
      <p>Status: {ticket.status}</p>
      <p>Priority: {ticket.priority}</p>
    </div>
=======
    <div className="w-fit mx-3 bg-white p-5 rounded-xl shadow-md cursor-pointer">

  <h3 className="ffont-bold text-3xl">{ticket.title}</h3>

  <p className="text-gray-600 text-lg mt-3 max-w-xl mx-auto">
    {ticket.description}
  </p>

  <div className="flex gap-1 mt-1">
    
    <span className="text-xs bg-gray-100 px-3 py-2 rounded">
      {ticket.category}
    </span>
    <span className={`px-3 py-2 text-xs rounded-full ${getStatusStyle(ticket.status)}`}>
        {ticket.status.replace("_", " ")}
    </span>

    <span className={`text-xs px-3 py-2 rounded ${
      ticket.priority === "high"
        ? "bg-red-100 text-red-600"
        : ticket.priority === "medium"
        ? "bg-yellow-100 text-yellow-600"
        : "bg-green-100 text-green-600"
    }`}>
      {ticket.priority}
    </span>
  </div>
</div>
        

>>>>>>> 6bee5ac (Auto predict)
  );
}

export default TicketDetails;