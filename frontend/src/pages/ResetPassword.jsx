import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "react-toastify";
import AuthShell from "../components/AuthShell";
import { resetPassword } from "../services/api";
import logger from "../utils/logger";

function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const uid = useMemo(() => searchParams.get("uid") || "", [searchParams]);
  const token = useMemo(() => searchParams.get("token") || "", [searchParams]);
  const hasValidLinkData = Boolean(uid && token);

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!hasValidLinkData) {
      toast.error("Reset link is invalid");
      return;
    }

    if (!password || !confirmPassword) {
      toast.error("Please fill all fields");
      return;
    }

    if (password !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    try {
      setLoading(true);
      const response = await resetPassword({
        uid,
        token,
        password,
        confirm_password: confirmPassword,
      });
      toast.success(response.data.message || "Password reset successful");
      navigate("/login");
    } catch (error) {
      logger.error("Password reset failed", error);
      toast.error(
        error.response?.data?.error ||
          error.response?.data?.confirm_password?.[0] ||
          error.response?.data?.password?.[0] ||
          "Unable to reset password"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      badgeText="Secure Password Reset"
      heroTitle="Choose a new"
      heroHighlight="password."
      heroDescription="Use a strong password you have not used elsewhere."
      formTitle="Reset password"
      formSubtitle="Enter and confirm your new password."
      footerContent={
        <div className="mt-6 pt-6 border-t border-white/5 text-center">
          <p className="text-gray-600 text-sm">
            Need a new link?{" "}
            <button
              type="button"
              onClick={() => navigate("/forgot-password")}
              className="text-indigo-400 cursor-pointer hover:text-indigo-300 transition-colors"
            >
              Request another
            </button>
          </p>
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {!hasValidLinkData && (
          <p className="text-sm text-red-400">This reset link is missing required information.</p>
        )}

        <div>
          <label
            htmlFor="new-password"
            className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider"
          >
            New password
          </label>
          <input
            id="new-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter a new password"
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition-all duration-200"
          />
        </div>

        <div>
          <label
            htmlFor="confirm-new-password"
            className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider"
          >
            Confirm password
          </label>
          <input
            id="confirm-new-password"
            type="password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            placeholder="Re-enter your new password"
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition-all duration-200"
          />
        </div>

        <button
          type="submit"
          disabled={loading || !hasValidLinkData}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 rounded-xl transition-all duration-200 text-sm"
        >
          {loading ? "Resetting..." : "Reset password"}
        </button>
      </form>
    </AuthShell>
  );
}

export default ResetPassword;
