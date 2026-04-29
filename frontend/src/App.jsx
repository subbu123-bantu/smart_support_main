import PropTypes from "prop-types";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import PrivateRoute from "./components/PrivateRoute";
import ChangeEmail from "./pages/ChangeEmail";
import CreateTicket from "./pages/CreateTicket";
import Dashboard from "./pages/Dashboard";
import ForgotPassword from "./pages/ForgotPassword";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ResetPassword from "./pages/ResetPassword";
import TicketDetails from "./pages/TicketDetails";
import Tickets from "./pages/Tickets";

function ProtectedLayout({ allowedRoles }) {
  return (
    <PrivateRoute allowedRoles={allowedRoles}>
      <Layout>
        <Outlet />
      </Layout>
    </PrivateRoute>
  );
}

ProtectedLayout.propTypes = {
  allowedRoles: PropTypes.arrayOf(PropTypes.string).isRequired,
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        <Route element={<ProtectedLayout allowedRoles={["admin", "agent", "customer"]} />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/tickets" element={<Tickets />} />
          <Route path="/tickets/:id" element={<TicketDetails />} />
          <Route path="/settings/email" element={<ChangeEmail />} />
        </Route>

        <Route element={<ProtectedLayout allowedRoles={["customer"]} />}>
          <Route path="/create-ticket" element={<CreateTicket />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
