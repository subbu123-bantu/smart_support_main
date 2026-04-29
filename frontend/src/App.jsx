import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import PrivateRoute from "./components/PrivateRoute";
import Layout from "./components/Layout";
import ChangeEmail from "./pages/ChangeEmail";
import CreateTicket from "./pages/CreateTicket";
import Dashboard from "./pages/Dashboard";
import ForgotPassword from "./pages/ForgotPassword";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ResetPassword from "./pages/ResetPassword";
import TicketDetails from "./pages/TicketDetails";
import Tickets from "./pages/Tickets";

function AppWrapper() {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <App />
    </BrowserRouter>
  );
}

function App() {
  return (
    <>
      <ToastContainer />

      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/register" element={<Register />} />

        <Route
          path="/dashboard"
          element={(
            <PrivateRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </PrivateRoute>
          )}
        />

        <Route
          path="/create-ticket"
          element={(
            <PrivateRoute allowedRoles={["customer"]}>
              <CreateTicket />
            </PrivateRoute>
          )}
        />

        <Route
          path="/tickets"
          element={(
            <PrivateRoute allowedRoles={["admin", "agent", "customer"]}>
              <Layout>
                <Tickets />
              </Layout>
            </PrivateRoute>
          )}
        />

        <Route
          path="/tickets/:id"
          element={(
            <PrivateRoute>
              <TicketDetails />
            </PrivateRoute>
          )}
        />

        <Route
          path="/settings/email"
          element={(
            <PrivateRoute>
              <Layout>
                <ChangeEmail />
              </Layout>
            </PrivateRoute>
          )}
        />
      </Routes>
    </>
  );
}

export default AppWrapper;
