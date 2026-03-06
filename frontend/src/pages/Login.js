import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
  e.preventDefault();
  try {
    const response = await axios.post(
      "http://127.0.0.1:8000/api/login/",
      {
        username: username,
        password: password,
      }
    );

    console.log("Login Success:", response.data);

    // Save token
    localStorage.setItem("access", response.data.access);
    localStorage.setItem("refresh", response.data.refresh);

    navigate("/dashboard"); 
  } catch (error) {
    console.error("Login Failed:", error.response?.data);
  }
};

  return (
    <div style={{ padding: "20px" }}>
      <h2>Login</h2>

      <form onSubmit={handleSubmit}>
        <div>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>

        <div style={{ marginTop: "10px" }}>
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <button style={{ marginTop: "10px" }} type="submit">
          Login
        </button>
      </form>
    </div>
  );
}

export default Login;