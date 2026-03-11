import { useNavigate } from "react-router-dom";

function Navbar() {

  const navigate = useNavigate();

  const logout = () => {
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

      <button onClick={logout}>
        Logout
      </button>

    </div>

  );
}

export default Navbar;