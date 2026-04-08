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
      const res = await loginUser({ username, password });
      const { access, role, username:loggedInUsername  } = res.data.user;

      localStorage.setItem("access", access);
      localStorage.setItem("role", role);
      localStorage.setItem("username",loggedInUsername );

      toast.success("Login successful!", { autoClose: 800 });
      console.log(res.data);
      navigate("/dashboard");
    } catch (error) {
      console.log(error.response?.data); // 🔥 IMPORTANT
      toast.error(error.response?.data?.error || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif" }} className="flex min-h-screen bg-[#0c0e14]">

      {/* ── Left Panel ── */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 bg-[#0f1117] border-r border-white/5">
        
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M2 4h5v5H2zM9 7h5v5H9z" fill="white" opacity="0.9"/>
              <path d="M2 10h3v4H2zM11 2h3v4h-3z" fill="white" opacity="0.5"/>
            </svg>
          </div>
          <span className="text-white font-semibold text-lg tracking-tight">Smart Support</span>
        </div>

        {/* Center content */}
        <div>
          <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-4 py-1.5 mb-8">
            <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
            <span className="text-indigo-400 text-xs font-medium tracking-wide">AI-Powered Support Platform</span>
          </div>

          <h1 className="text-5xl font-bold text-white leading-tight mb-6" style={{ letterSpacing: '-0.03em' }}>
            Resolve tickets<br />
            <span className="text-indigo-400">10x faster.</span>
          </h1>
          <p className="text-gray-500 text-lg leading-relaxed max-w-sm">
            Intelligent ticket routing, auto-classification, and real-time agent workload balancing.
          </p>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-6 mt-12">
            {[
              { value: "98%", label: "Resolution rate" },
              { value: "<2h", label: "Avg response time" },
              { value: "50k+", label: "Tickets resolved" },
            ].map((s, i) => (
              <div key={i}>
                <p className="text-2xl font-bold text-white" style={{ letterSpacing: '-0.02em' }}>{s.value}</p>
                <p className="text-gray-600 text-sm mt-1">{s.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <p className="text-gray-700 text-sm">© 2026 Smart Support. All rights reserved.</p>
      </div>

      {/* ── Right Panel — Login Form ── */}
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="w-full max-w-sm">

          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-2 mb-10">
            <div className="w-7 h-7 rounded-md bg-indigo-500 flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M2 4h5v5H2zM9 7h5v5H9z" fill="white"/>
              </svg>
            </div>
            <span className="text-white font-semibold">Smart Support</span>
          </div>

          <h2 className="text-2xl font-bold text-white mb-1" style={{ letterSpacing: '-0.02em' }}>
            Welcome back
          </h2>
          <p className="text-gray-500 text-sm mb-8">Sign in to your workspace</p>

          <form onSubmit={handleSubmit} className="space-y-4">

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition-all duration-200"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">
                Password
              </label>
              <input
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
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                  </svg>
                  Signing in...
                </>
              ) : "Sign in"}
            </button>

          </form>

          <div className="mt-6 pt-6 border-t border-white/5 text-center">
            <p className="text-gray-600 text-sm">
              Don't have an account?{" "}
              <span
                onClick={() => navigate("/register")}
                className="text-indigo-400 cursor-pointer hover:text-indigo-300 transition-colors"
              >
                Create one
              </span>
            </p>
          </div>

          {/* Role hint badges */}
          <div className="mt-8 flex flex-wrap gap-2 justify-center">
            {["Admin", "Agent", "Customer"].map((r) => (
              <span key={r} className="text-xs px-3 py-1 rounded-full bg-white/5 text-gray-600 border border-white/5">
                {r} portal
              </span>
            ))}
          </div>

        </div>
      </div>
    </div>
  );
}

export default Login;