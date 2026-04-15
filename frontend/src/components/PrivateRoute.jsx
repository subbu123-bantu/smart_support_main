import PropTypes from "prop-types";
import { Navigate } from "react-router-dom";

function PrivateRoute({ children }) {
  const token = localStorage.getItem("access");
  return token ? children : <Navigate to="/login" replace />;
}

PrivateRoute.propTypes = {
  children: PropTypes.node.isRequired,
};

export default PrivateRoute;