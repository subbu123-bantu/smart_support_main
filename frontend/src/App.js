import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Tickets from "./pages/Tickets";
import CreateTicket from "./pages/CreateTicket";
import TicketDetails from "./pages/TicketDetails";
import Register from "./pages/Register";
import Navbar from "./components/Navbar";

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
      {!hideNavbar && <Navbar />}

      <Routes>

        <Route path="/" element={<Login />} />

        <Route path="/dashboard" element={<Dashboard />} />

        <Route path="/tickets" element={<Tickets />} />

        <Route path="/create-ticket" element={<CreateTicket />} />

        <Route path="/ticket/:id" element={<TicketDetails />} />

        <Route path="/register" element={<Register />} />

      </Routes>
    </>
  );
}

export default AppWrapper;