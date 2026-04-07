import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { loginUser } from "../services/api";

function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!username || !password) {
      toast.error("Please fill all fields");
      return;
    }

    try {
      setLoading(true);
      // ✅ clean version - only once
      const res = await loginUser({ username, password });
      const { access, role } = res.data.user;
      localStorage.setItem("access", access);
      localStorage.setItem("role", role);
      toast.success("Login successful!", { autoClose: 800 });
      navigate("/dashboard");

    } catch (error) {
      console.log(error.response?.data);
      toast.error("Invalid username or password");
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-indigo-200 via-purple-100 to-gray-100">

  <div className="bg-white/80 backdrop-blur-md p-8 rounded-2xl shadow-xl w-full max-w-md">

    <h2 className="text-2xl font-semibold text-center mb-6 text-gray-800">
      Smart Support Login
    </h2>

    <form onSubmit={handleSubmit} className="space-y-4">

      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400 outline-none"
      />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400 outline-none"
      />

      <button
        className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition duration-200 shadow-md"
        disabled={loading}
        
      >
        {loading ? "Logging in..." : "Login"}
      </button>

    </form>

    <p className="text-center mt-4 text-sm text-gray-600">
      Don’t have an account? 
      <span
        onClick={() => navigate("/register")}
        className="text-indigo-600 cursor-pointer ml-1 hover:underline"
      >
        Register
      </span>
    </p>

    </div>
  </div>
  );
}

export default Login;