import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getTicketById } from "../services/api";

function TicketDetails() {
  const { id } = useParams(); //Use param is used to access the dynamic segments of the url
  const [ticket, setTicket] = useState(null);

  const getStatusStyle = (status) => {
    switch (status) {
      case "open":
        return "bg-red-50 text-red-600 border-red-200";
      case "in_progress":
        return "bg-yellow-50 text-yellow-700 border-yellow-200";
      case "closed":
        return "bg-green-50 text-green-700 border-green-200";
      default:
        return "bg-gray-50 text-gray-600 border-gray-200";
    }
  };

  const getPriorityStyle = (priority) => {
    switch (priority) {
      case "high":
        return "bg-red-50 text-red-600 border-red-200";
      case "medium":
        return "bg-yellow-50 text-yellow-700 border-yellow-200";
      default:
        return "bg-green-50 text-green-700 border-green-200";
    }
  };

  useEffect(() => {
    const fetchTicket = async () => {
      try {
        const res = await getTicketById(id);
        setTicket(res.data);
        console.log(res.data);
      } catch (err) {
        console.error(err);
      }
    };

    fetchTicket();
  }, [id]);

  if (!ticket) {
    return (
      <div className="flex flex-col justify-center items-center h-80 text-center">
        
        <h1 className="text-5xl font-bold text-gray-800 mb-3">
          404
        </h1>

        <p className="text-2xl font-semibold text-gray-700 mb-2">
          Ticket Not Found
        </p>

        <p className="text-gray-500 text-base">
          The ticket you are looking for does not exist or may have been removed.
        </p>

      </div>
    );
  }

  return (
  <div className="min-h-screen bg-gray-50 flex justify-center p-8">
    <div className="w-full max-w-4xl bg-white rounded-2xl shadow-lg border border-gray-100 p-8">

      {/* Header */}
      <div className="border-b pb-6 mb-6">
        <h1 className="text-4xl font-semibold text-gray-900 leading-tight">
          {ticket.title}
        </h1>

        <p className="text-sm text-gray-500 mt-2">
          Ticket ID: #{ticket.id}
        </p>
      </div>

      {/* Description */}
      <div className="mb-8">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Description
        </h2>

        <div className="bg-gray-50 border rounded-xl p-6">
          <p className="text-gray-800 text-lg leading-relaxed">
            {ticket.description}
          </p>
        </div>
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-4">

        <span className="text-sm px-5 py-2.5 rounded-full bg-gray-100 text-gray-800 border shadow-sm">
          {ticket.category}
        </span>

        <span
          className={`text-sm px-5 py-2.5 rounded-full border shadow-sm font-medium ${getStatusStyle(
            ticket.status
          )}`}
        >
          {ticket.status.replace("_", " ")}
        </span>

        <span
          className={`text-sm px-5 py-2.5 rounded-full border shadow-sm font-medium ${getPriorityStyle(
            ticket.priority
          )}`}
        >
          {ticket.priority}
        </span>
      </div>
    </div>
  </div>
);
}

export default TicketDetails; 