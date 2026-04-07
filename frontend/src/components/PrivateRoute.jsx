import { Navigate } from "react-router-dom";

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem("access");  // ✅ must be "access"
  return token ? children : <Navigate to="/login" />;
};

export default PrivateRoute;