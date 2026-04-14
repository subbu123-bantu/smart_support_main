import "./App.css";
import { BrowserRouter, Routes, Route ,Navigate} from "react-router-dom";
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

      <Routes>

        <Route path="/" element={<Navigate to="/login" />} />

        <Route path="/login"  element={<Login />} />

        <Route path="/dashboard" element={<PrivateRoute><Layout><Dashboard /></Layout></PrivateRoute>} />

        <Route path="/create-ticket" element={<PrivateRoute><Layout>{<CreateTicket />}</Layout></PrivateRoute>}/>

        <Route path="/tickets" element={<PrivateRoute><Layout>{<Tickets />}</Layout></PrivateRoute> }/>

        <Route path="/tickets/:id" element={<PrivateRoute>{<TicketDetails />}</PrivateRoute>} />

        <Route path="/register" element={<Register />} />

      </Routes>
    </>
  );
}

export default AppWrapper;