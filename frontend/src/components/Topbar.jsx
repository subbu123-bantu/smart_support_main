function Topbar() {
  return (
    <div className="h-14 border-b border-white/5 flex items-center justify-between px-6 bg-[#0c0e14]">
      <p className="text-sm text-gray-400">
        {new Date().toLocaleDateString()}
      </p>
    </div>
  );
}

export default Topbar;