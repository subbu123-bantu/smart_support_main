import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Tickets from "./pages/Tickets";
import CreateTicket from "./pages/CreateTicket";
import TicketDetails from "./pages/TicketDetails";
import Register from "./pages/Register";
import PrivateRoute from "./components/PrivateRoute";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import Layout from "./components/Layout";
import { Navigate } from "react-router-dom";

function AppWrapper() {
  return (
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
}

function App() {

  return (
    <>

      {/* <ToastContainer position="top-right" autoClose={1000} /> */}
      <ToastContainer />
      {/* {!hideSidebar && <Sidebar />} */}

      <Routes>

        <Route path="/" element={<Navigate to="/login" />} />

        <Route path="/login"  element={<Login />} />

        <Route path="/dashboard" element={<PrivateRoute><Layout><Dashboard /></Layout></PrivateRoute>} />

        <Route path="/create-ticket" element={<PrivateRoute>{<CreateTicket />}</PrivateRoute>}/>

        <Route path="/tickets" element={<PrivateRoute>{<Tickets />}</PrivateRoute> }/>

        <Route path="/tickets/:id" element={<TicketDetails />} />

        <Route path="/register" element={<Register />} />

      </Routes>
    </>
  );
}

export default AppWrapper;