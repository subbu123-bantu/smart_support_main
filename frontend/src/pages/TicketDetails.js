import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getTicketById } from "../services/api";

function TicketDetails() {
  const { id } = useParams();
  const [ticket, setTicket] = useState(null);

  const getStatusStyle = (status) => {
  switch (status) {
    case "open":
      return "bg-red-100 text-red-600";
    case "in_progress":
      return "bg-yellow-100 text-yellow-600";
    case "closed":
      return "bg-green-100 text-green-600";
    default:
      return "bg-gray-100 text-gray-600";
  }
};

  useEffect(() => {
    const fetchTicket = async () => {
      try {
        const res = await getTicketById(id);
        setTicket(res.data);
      } catch (err) {
        console.error(err);
      }
    };

    fetchTicket();
  }, [id]);

  if (!ticket) return <p>Loading...</p>;
  console.log("Ticket Details Page Loaded", ticket);

  

  return (
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
        

  );
}

export default TicketDetails;