import axios from "axios";
const API = axios.create({
  baseURL: "http://localhost:8000/api/",
});

API.interceptors.request.use(
  (req) => {
    const publicRoutes = ["login/", "register/"];
    const isPublicRoute = publicRoutes.some((route) => req.url?.includes(route));

    if (!isPublicRoute) {
      const token = localStorage.getItem("access");
      if (token) {
        req.headers.Authorization = `Bearer ${token}`;
      }
    }

    return req;
  },
  (error) => Promise.reject(error)
);

API.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url || "";
    const isLoginRequest = url.includes("login/");

    if (error.response?.status === 401 && !isLoginRequest) {
      localStorage.removeItem("access");
      localStorage.removeItem("role");
      localStorage.removeItem("username");
      window.location.href = "login";
    }

    return Promise.reject(error);
  }
);

// AUTH
export const loginUser = (data) => API.post("login/", data);
export const registerUser = (data) => API.post("register/", data);

// TICKETS
export const getTicketStats = () => API.get("stats/");

export const getTickets = (
  page = 1,
  ticketStatus = "",
  priority = "",
  search = "",
  assigned = "",
  category = ""
) => {
  let url = `v1/tickets/?page=${page}`;

  if (ticketStatus) url += `&status=${ticketStatus}`;
  if (priority && priority !== "all") url += `&priority=${priority}`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  if (assigned !== "") url += `&assigned=${assigned}`;
  if (category) url += `&category=${category}`;

  return API.get(url);
};

export const createTicket = (data) => API.post("tickets/", data);
export const getTicketById = (id) => API.get(`tickets/${id}/`);
export const updateTicket = (id, data) => API.patch(`tickets/${id}/`, data);
export const deleteTicket = (id) => API.delete(`tickets/${id}/`);
export const predictTicket = (data) => API.post("predict/", data);

export const assignTicket = (ticketId, agentId) =>
  API.patch(`tickets/${ticketId}/assign/`, { agent_id: agentId });

export const getAgents = () => API.get("agents/");
export const getCategories = () => API.get("categories/");
export const getTicketComments = (ticketId) => API.get(`tickets/${ticketId}/comments/`);
export const addTicketComment = (ticketId, data) => API.post(`tickets/${ticketId}/comments/`, data);
export const getTicketPredictionFeedback = (ticketId) =>
  API.get(`tickets/${ticketId}/prediction-feedback/`);

export default API;