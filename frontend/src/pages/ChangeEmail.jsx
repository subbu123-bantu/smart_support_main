import { useState } from "react";
import { toast } from "react-toastify";
import { changeEmail } from "../services/api";
import logger from "../utils/logger";

function ChangeEmail() {
  const [email, setEmail] = useState(localStorage.getItem("email") || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!email.trim() || !currentPassword) {
      toast.error("Please fill all fields");
      return;
    }

    try {
      setSaving(true);
      const response = await changeEmail({
        email: email.trim(),
        current_password: currentPassword,
      });
      localStorage.setItem("email", response.data.email);
      toast.success(response.data.message || "Email updated");
      setCurrentPassword("");
    } catch (error) {
      logger.error("Email update failed", error);
      toast.error(
        error.response?.data?.email?.[0] ||
          error.response?.data?.current_password?.[0] ||
          error.response?.data?.error ||
          "Unable to update email"
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2" style={{ letterSpacing: "-0.03em" }}>
          Change Email
        </h1>
        <p className="text-gray-500 text-sm">
          Update the email address used for your Smart Support account.
        </p>
      </div>

      <div className="bg-[#0f1117] border border-white/5 rounded-2xl p-6">
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label
              htmlFor="new-email"
              className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider"
            >
              New email
            </label>
            <input
              id="new-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition-all duration-200"
            />
          </div>

          <div>
            <label
              htmlFor="current-password"
              className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider"
            >
              Current password
            </label>
            <input
              id="current-password"
              type="password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
              placeholder="Confirm with your password"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 outline-none focus:border-indigo-500 focus:bg-indigo-500/5 transition-all duration-200"
            />
          </div>

          <button
            type="submit"
            disabled={saving}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 px-5 rounded-xl transition-all duration-200 text-sm"
          >
            {saving ? "Saving..." : "Update email"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChangeEmail;
