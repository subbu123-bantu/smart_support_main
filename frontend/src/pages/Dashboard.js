import { useState } from "react";
import { useNavigate } from "react-router-dom";
function Dashboard() {
  const navigate = useNavigate();
  const [token, setToken] = useState(localStorage.getItem("token"));
  const logout= ()=>{
    localStorage.removeItem("token");
    setToken("");
    navigate("/login");
  }
 
  return (
    <div>
      <h1>Dashboard</h1>

      {token ? (
        <p>You are logged in</p>
      ) : (
        <p>You are NOT logged in</p>
      )}
      <button onClick={logout}>Logout</button>
      <button onClick={()=>navigate("/tickets")}>Create</button>
    </div>
  );
}

export default Dashboard;