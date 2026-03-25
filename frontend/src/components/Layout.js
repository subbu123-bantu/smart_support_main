import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

function Layout({ children }) {
  return (
    <div style={{ display: "flex", height: "100vh" }}>
      
      <Sidebar />

      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <Topbar />
        
        <div style={{ padding: "20px", background: "#F9FAFB", flex: 1 }}>
          {children}
        </div>
      </div>

    </div>
  );
}

export default Layout;