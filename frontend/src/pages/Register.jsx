import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import AuthShell from "../components/AuthShell";
import { registerUser } from "../services/api";
import logger from "../utils/logger";

function Register() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!username || !email || !password || !confirm) {
      toast.error("Please fill all fields");
      return;
    }

    if (password !== confirm) {
      toast.error("Passwords do not match");
      return;
    }

    try {
      setLoading(true);
      await registerUser({ username, email, password });
      toast.success("Account created! Please sign in.");
      navigate("/");
    } catch (err) {
      logger.error("Registration failed", err);
      const msg =
        err.response?.data?.username?.[0] ||
        err.response?.data?.email?.[0] ||
        "Registration failed";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const features = [
    { icon: "⚡", title: "Instant routing", desc: "AI assigns your ticket to the right team in seconds" },
    { icon: "🔍", title: "Auto-classification", desc: "Smart categorisation without any manual input" },
    { icon: "📬", title: "Live updates", desc: "Email notifications at every stage of resolution" },
  ];

  return (
    <AuthShell
      badgeText="Get started in seconds"
      heroTitle="Support that"
      heroHighlight="actually works."
      heroDescription="Join thousands of teams using Smart Support to resolve issues faster with AI-powered workflows."
      leftContent={
        <div className="space-y-5">
          {features.map((feature) => (
            <div key={feature.title} className="flex items-start gap-4">
              <div className="w-9 h-9 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-base flex-shrink-0">
                {feature.icon}
              </div>
              <div>
                <p className="text-white text-sm font-medium">{feature.title}</p>
                <p className="text-gray-600 text-sm mt-0.5">{feature.desc}</p>
              </div>
            </div>
          ))}
        </div>
      }
      formTitle="Create your account"
      formSubtitle="Free to get started. No credit card needed."
      footerContent={
        <div className="mt-6 pt-6 border-t border-white/5 text-center">
          <p className="text-gray-600 text-sm">
            Already have an account?{" "}
            <button
              type="button"
              onClick={() => navigate("/")}
              onKeyDown={(e) => e.key === "Enter" && navigate("/")}
              className="text-indigo-400 cursor-pointer hover:text-indigo-300 transition-colors"
            >
              Sign in
            </button>
          </p>
        </div>
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
            placeholder="Choose a username"
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition-all duration-200"
          />
        </div>

        <div>
          <label
            htmlFor="email"
            className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider"
          >
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
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
            placeholder="Create a password"
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition-all duration-200"
          />
        </div>

        <div>
          <label
            htmlFor="confirm-password"
            className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider"
          >
            Confirm password
          </label>
          <input
            id="confirm-password"
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="Re-enter your password"
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition-all duration-200"
          />
          {confirm && (
            <p className={`text-xs mt-1.5 ${password === confirm ? "text-emerald-500" : "text-red-400"}`}>
              {password === confirm ? "Passwords match" : "Passwords do not match"}
            </p>
          )}
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
              Creating account...
            </>
          ) : (
            "Create account"
          )}
        </button>
      </form>
    </AuthShell>
  );
}

export default Register;
