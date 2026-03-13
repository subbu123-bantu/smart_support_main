import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { loginUser } from "../services/api";

function Login() {

  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!username || !password) {
      toast.error("Please fill all fields");
      return;
    }

    try {

      setLoading(true);

      const response = await loginUser({
        username,
        password
      });

      const data = response.data;

      localStorage.setItem("token", data.access);

      toast.success("Login successful!");

      setTimeout(() => {
        navigate("/dashboard");
      }, 1000);

    } catch (error) {

      console.log(error.response?.data);

      toast.error("Invalid username or password");

    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>

      <div style={styles.card}>

        <h2 style={styles.title}>Smart Support Login</h2>

        <form onSubmit={handleSubmit}>

          <input
            style={styles.input}
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />

          <input
            style={styles.input}
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <button style={styles.button} disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>

        </form>

        <p style={styles.registerText}>
          Don't have an account? <a href="/register">Register</a>
        </p>

      </div>

    </div>
  );
}

const styles = {

  container: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    background: "#f4f6f8"
  },

  card: {
    background: "white",
    padding: "40px",
    borderRadius: "10px",
    width: "350px",
    boxShadow: "0 5px 15px rgba(0,0,0,0.1)"
  },

  title: {
    textAlign: "center",
    marginBottom: "20px"
  },

  input: {
    width: "100%",
    padding: "10px",
    marginBottom: "15px",
    border: "1px solid #ddd",
    borderRadius: "6px",
    fontSize: "14px"
  },

  button: {
    width: "100%",
    padding: "10px",
    background: "#1976d2",
    color: "white",
    border: "none",
    borderRadius: "6px",
    fontSize: "16px",
    cursor: "pointer"
  },

  registerText: {
    textAlign: "center",
    marginTop: "15px",
    fontSize: "14px"
  }
};

export default Login;