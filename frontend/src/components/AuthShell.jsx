import PropTypes from "prop-types";

function AuthShell({
  badgeText,
  heroTitle,
  heroHighlight,
  heroDescription,
  leftContent,
  formTitle,
  formSubtitle,
  footerContent,
  children,
}) {
  return (
    <div
      style={{ fontFamily: "'DM Sans', sans-serif" }}
      className="flex min-h-screen bg-[#0c0e14]"
    >
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 bg-[#0f1117] border-r border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M2 4h5v5H2zM9 7h5v5H9z" fill="white" opacity="0.9" />
              <path d="M2 10h3v4H2zM11 2h3v4h-3z" fill="white" opacity="0.5" />
            </svg>
          </div>
          <span className="text-white font-semibold text-lg tracking-tight">Smart Support</span>
        </div>

        <div>
          <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-4 py-1.5 mb-8">
            <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
            <span className="text-indigo-400 text-xs font-medium tracking-wide">{badgeText}</span>
          </div>

          <h1
            className="text-5xl font-bold text-white leading-tight mb-6"
            style={{ letterSpacing: "-0.03em" }}
          >
            {heroTitle}
            <br />
            <span className="text-indigo-400">{heroHighlight}</span>
          </h1>
          <p className="text-gray-500 text-lg leading-relaxed max-w-sm">{heroDescription}</p>

          {leftContent && <div className="mt-10">{leftContent}</div>}
        </div>

        <p className="text-gray-700 text-sm">© 2026 Smart Support. All rights reserved.</p>
      </div>

      <div className="flex flex-1 items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <div className="flex lg:hidden items-center gap-2 mb-10">
            <div className="w-7 h-7 rounded-md bg-indigo-500 flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M2 4h5v5H2zM9 7h5v5H9z" fill="white" />
              </svg>
            </div>
            <span className="text-white font-semibold">Smart Support</span>
          </div>

          <h2 className="text-2xl font-bold text-white mb-1" style={{ letterSpacing: "-0.02em" }}>
            {formTitle}
          </h2>
          <p className="text-gray-500 text-sm mb-8">{formSubtitle}</p>

          {children}

          {footerContent}
        </div>
      </div>
    </div>
  );
}

AuthShell.propTypes = {
  badgeText: PropTypes.string.isRequired,
  heroTitle: PropTypes.string.isRequired,
  heroHighlight: PropTypes.string.isRequired,
  heroDescription: PropTypes.string.isRequired,
  leftContent: PropTypes.node,
  formTitle: PropTypes.string.isRequired,
  formSubtitle: PropTypes.string.isRequired,
  footerContent: PropTypes.node.isRequired,
  children: PropTypes.node.isRequired,
};

AuthShell.defaultProps = {
  leftContent: null,
};

export default AuthShell;
