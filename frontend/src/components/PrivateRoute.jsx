import PropTypes from "prop-types";
import { jwtDecode } from "jwt-decode";
import { Navigate } from "react-router-dom";
import { clearAuthStorage } from "../services/api";

function isTokenExpired(token) {
  try {
    const { exp } = jwtDecode(token);
    return typeof exp === "number" && Date.now() >= exp * 1000;
  } catch {
    return true;
  }
}

function PrivateRoute({ children, allowedRoles = [] }) {
  const token = localStorage.getItem("access");
  const role = (localStorage.getItem("role") || "").toLowerCase();

  if (!token || isTokenExpired(token)) {
    clearAuthStorage();
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

PrivateRoute.propTypes = {
  allowedRoles: PropTypes.arrayOf(PropTypes.string),
  children: PropTypes.node.isRequired,
};

export default PrivateRoute;
