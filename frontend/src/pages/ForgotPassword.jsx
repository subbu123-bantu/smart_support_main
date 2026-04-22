import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import AuthShell from "../components/AuthShell";
import { requestPasswordReset } from "../services/api";

function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!email.trim()) {
      toast.error("Please enter your email");
      return;
    }

    try {
      setLoading(true);
      const response = await requestPasswordReset({ email: email.trim() });
      toast.success(response.data.message || "Reset instructions sent");
      navigate("/login");
    } catch (error) {
      toast.error(error.response?.data?.email?.[0] || "Unable to process request");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      badgeText="Account Recovery"
      heroTitle="Reset your"
      heroHighlight="password."
      heroDescription="Enter your account email and we will send you a secure reset link."
      formTitle="Forgot password"
      formSubtitle="We will email you a password reset link."
      footerContent={
        <div className="mt-6 pt-6 border-t border-white/5 text-center">
          <p className="text-gray-600 text-sm">
            Remembered it?{" "}
            <button
              type="button"
              onClick={() => navigate("/login")}
              className="text-indigo-400 cursor-pointer hover:text-indigo-300 transition-colors"
            >
              Back to sign in
            </button>
          </p>
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="forgot-email"
            className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider"
          >
            Email
          </label>
          <input
            id="forgot-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition-all duration-200"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 rounded-xl transition-all duration-200 text-sm"
        >
          {loading ? "Sending..." : "Send reset link"}
        </button>
      </form>
    </AuthShell>
  );
}

export default ForgotPassword;
