import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import AuthShell from "../components/AuthShell";
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
      const res = await loginUser({ username, password });
      const { access, role, username: loggedInUsername } = res.data.user;

      localStorage.setItem("access", access);
      localStorage.setItem("role", role);
      localStorage.setItem("username", loggedInUsername);

      toast.success("Login successful!", { autoClose: 800 });
      navigate("/dashboard");
    } catch (error) {
      toast.error(error.response?.data?.error || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      badgeText="AI-Powered Support Platform"
      heroTitle="Resolve tickets"
      heroHighlight="10x faster."
      heroDescription="Intelligent ticket routing, auto-classification, and real-time agent workload balancing."
      formTitle="Welcome back"
      formSubtitle="Sign in to your workspace"
      footerContent={
        <>
          <div className="mt-6 pt-6 border-t border-white/5 text-center">
            <p className="text-gray-600 text-sm">
              Don't have an account?{" "}
              <button
                type="button"
                onClick={() => navigate("/register")}
                onKeyDown={(e) => e.key === "Enter" && navigate("/register")}
                className="text-indigo-400 cursor-pointer hover:text-indigo-300 transition-colors"
              >
                Create one
              </button>
            </p>
          </div>

          <div className="mt-8 flex flex-wrap gap-2 justify-center">
            {["Admin", "Agent", "Customer"].map((roleName) => (
              <span
                key={roleName}
                className="text-xs px-3 py-1 rounded-full bg-white/5 text-gray-600 border border-white/5"
              >
                {roleName} portal
              </span>
            ))}
          </div>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="username"
            className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider"
          >
            Username
          </label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter your username"
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition-all duration-200"
          />
        </div>

        <div>
          <label
            htmlFor="password"
            className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider"
          >
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition-all duration-200"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 rounded-xl transition-all duration-200 text-sm mt-2 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Signing in...
            </>
          ) : (
            "Sign in"
          )}
        </button>
      </form>
    </AuthShell>
  );
}

export default Login;
