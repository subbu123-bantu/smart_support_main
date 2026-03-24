import { useNavigate } from "react-router-dom";
import { Link } from "react-router-dom";
function Navbar() {

  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  return (

    <div style={{
      background:"#333",
      color:"white",
      padding:"10px",
      display:"flex",
      justifyContent:"space-between"
    }}>

      <h3>Smart Support System</h3>

      <div className="nav-links">
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/tickets">Tickets</Link>
        <Link to="/create-ticket">Create Ticket</Link>
        
      <button className="logout-btn" onClick={handleLogout}>
        Logout
      </button>
      </div>
    </div>

  );
}

export default Navbar;