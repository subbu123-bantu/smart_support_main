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
    <div className="bg-white p-5 rounded-xl shadow hover:shadow-md transition cursor-pointer">

  <h3 className="font-semibold text-lg">{ticket.title}</h3>

  <p className="text-gray-500 text-sm mt-1">
    {ticket.description}
  </p>

  <div className="flex gap-1 mt-1">
    
    <span className="text-xs bg-gray-100 px-2 py-1 rounded">
      {ticket.category}
    </span>
    <span className={`px-2 py-1 text-xs rounded-full ${getStatusStyle(ticket.status)}`}>
        {ticket.status.replace("_", " ")}
    </span>

    <span className={`text-xs px-2 py-1 rounded ${
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