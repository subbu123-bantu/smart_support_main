import "./App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Tickets from "./pages/Tickets";
import CreateTicket from "./pages/CreateTicket";
import TicketDetails from "./pages/TicketDetails";
import Register from "./pages/Register";
import Navbar from "./components/Navbar";
import PrivateRoute from "./components/PrivateRoute";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

function AppWrapper() {
  return (
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
}

function App() {

  const location = useLocation();

  const hideNavbar =
    location.pathname === "/" ||
    location.pathname === "/register";

  return (
    <>

      {/* <ToastContainer position="top-right" autoClose={1000} /> */}
      <ToastContainer />
      {!hideNavbar && <Navbar />}

      <Routes>

        <Route path="/" element={<Login />} />

        <Route path="/dashboard" element={<PrivateRoute>{<Dashboard />}</PrivateRoute>}/>

        <Route path="/tickets" element={<PrivateRoute>{<Tickets />}</PrivateRoute> }/>

        <Route path="/create-ticket" element={<PrivateRoute>{<CreateTicket />}</PrivateRoute>}/>

        <Route path="/ticket/:id" element={<PrivateRoute>{<TicketDetails />}</PrivateRoute>} />

        <Route path="/register" element={<Register />} />

      </Routes>
    </>
  );
}

export default AppWrapper;