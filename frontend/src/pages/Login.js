import { useState } from "react";
import { useNavigate } from "react-router-dom";

function Login() {

  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    const response = await fetch("http://127.0.0.1:8000/api/login/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: username,
        password: password
      }),
    });

    const data = await response.json();

    console.log("LOGIN RESPONSE:", data);

    if (data.access) {

      localStorage.setItem("token", data.access);

      alert("Login successful");

      navigate("/dashboard");

    } else {
      alert("Login failed");
    }
  };

  return (
    <div>
      <h2>Login</h2>

      <form onSubmit={handleSubmit}>

        <input
          type="text"
          placeholder="Username"
          onChange={(e) => setUsername(e.target.value)}
        />

        <br/><br/>

        <input
          type="password"
          placeholder="Password"
          onChange={(e) => setPassword(e.target.value)}
        />

        <br/><br/>

        <button type="submit">Login</button>
        <a href="/register">Register</a>

      </form>
    </div>
  );
}

export default Login;