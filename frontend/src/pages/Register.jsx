import { useState } from "react";
import { registerUser } from "../services/api";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";

function Register() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      await registerUser({ username, email, password });
      toast.success("Registered successfully!");
      navigate("/");
    } catch {
      toast.error("Registration failed");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-indigo-200 via-purple-100 to-gray-100">

  <div className="bg-white/80 backdrop-blur-md p-8 rounded-2xl shadow-xl w-full max-w-md">

    <h2 className="text-2xl font-semibold text-center mb-6">
      Create Account
    </h2>

    <form onSubmit={handleSubmit} className="space-y-4">

      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400"
      />

      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400"
      />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400"
      />

      <button className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition shadow-md">
        Register
      </button>

    </form>

    <p className="text-center mt-4 text-sm">
      Already have an account? 
      <span
        onClick={() => navigate("/")}
        className="text-indigo-600 cursor-pointer ml-1 hover:underline"
      >
        Login
      </span>
    </p>

  </div>
  </div>
  );
}

export default Register;