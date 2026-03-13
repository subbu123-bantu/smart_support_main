import { useState } from "react";
import { registerUser } from "../services/api";
import { useNavigate } from "react-router-dom";

function Register() {

  const [username,setUsername]=useState("");
  const [email,setEmail]=useState("");
  const [password,setPassword]=useState("");

  const navigate = useNavigate();

  const handleSubmit = async (e) =>{
    e.preventDefault();

    await registerUser({
      username,
      email,
      password
    });

    navigate("/");
  }

  return (

    <div className="auth-container">

      <form className="auth-card" onSubmit={handleSubmit}>

        <h2>Register</h2>

        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e)=>setUsername(e.target.value)}
        />

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e)=>setEmail(e.target.value)}
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e)=>setPassword(e.target.value)}
        />

        <button type="submit">Register</button>
        <p>
          Already have an account? <a href="/">Login</a>
        </p>

      </form>

    </div>

  );
}

export default Register;