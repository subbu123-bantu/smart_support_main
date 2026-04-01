import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

function Layout({ children }) {
  return (
    <div className="flex h-screen">
      
      <Sidebar />

      <div className="flex flex-col flex-1">
        <Topbar />
        
        <div className="bg-gray-50 text-gray-900 font-sans min-h-screen overflow-y-auto">
          {children}
        </div>
      </div>

    </div>
  );
}

export default Layout;