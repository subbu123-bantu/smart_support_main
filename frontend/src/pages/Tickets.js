import { useEffect, useState } from "react";
import { getTickets } from "../services/api";

function Tickets() {

  const [tickets, setTickets] = useState([]);
  const [page, setPage] = useState(1);
  const [next, setNext] = useState(null);
  const [previous, setPrevious] = useState(null);

  useEffect(() => {

    const fetchTickets = async () => {

      const res = await getTickets(page);

      setTickets(res.data.results);
      setNext(res.data.next);
      setPrevious(res.data.previous);

    };

    fetchTickets();

  }, [page]);

  return (
    <div>

      <h2>All Tickets</h2>

      <table>

        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Description</th>
            <th>Priority</th>
            <th>Status</th>
          </tr>
        </thead>

        <tbody>

          {tickets.map((ticket) => (

            <tr key={ticket.id}>
              <td>{ticket.id}</td>
              <td>{ticket.title}</td>
              <td>{ticket.description}</td>
              <td>{ticket.priority}</td>
              <td>{ticket.status}</td>
            </tr>

          ))}

        </tbody>

      </table>

      <div style={{ marginTop: "20px" }}>

        <button
          onClick={() => setPage(page - 1)}
          disabled={!previous}
        >
          Previous
        </button>

        <span style={{ margin: "0 10px" }}>Page {page}</span>

        <button
          onClick={() => setPage(page + 1)}
          disabled={!next}
        >
          Next
        </button>

      </div>

    </div>
  );
}

export default Tickets;