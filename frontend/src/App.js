import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Tickets from "./pages/Tickets";
import CreateTicket from "./pages/CreateTicket";
import TicketDetails from "./pages/TicketDetails";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import ChangeEmail from "./pages/ChangeEmail";
import PrivateRoute from "./components/PrivateRoute";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import Layout from "./components/Layout";

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
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="/login" element={<Login />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </PrivateRoute>
          }
        />

        <Route
          path="/create-ticket"
          element={
            <PrivateRoute>
              <CreateTicket />
            </PrivateRoute>
          }
        />

        <Route
          path="/tickets"
          element={
            <PrivateRoute>
              <Tickets />
            </PrivateRoute>
          }
        />

        <Route
          path="/tickets/:id"
          element={
            <PrivateRoute>
              <TicketDetails />
            </PrivateRoute>
          }
        />

        <Route
          path="/settings/email"
          element={
            <PrivateRoute>
              <Layout>
                <ChangeEmail />
              </Layout>
            </PrivateRoute>
          }
        />

        <Route path="/register" element={<Register />} />
      </Routes>
    </>
  );
}

export default AppWrapper;
