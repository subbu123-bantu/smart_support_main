import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000/api/",
});

API.interceptors.request.use(
  (req) => {
    const isAuthRequest =
      req.url?.includes("v2/login/") || req.url?.includes("v2/register/");

    if (!isAuthRequest) {
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
    const isLoginRequest = url.includes("v2/login/");

    if (error.response?.status === 401 && !isLoginRequest) {
      localStorage.removeItem("access");
      localStorage.removeItem("role");
      localStorage.removeItem("username");
      window.location.href = "/login";
    }

    return Promise.reject(error);
  }
);

// AUTH
export const loginUser = (data) => API.post("v2/login/", data);
export const registerUser = (data) => API.post("v2/register/", data);

// TICKETS
export const getTicketStats = () => API.get("v1/stats/");

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

export const createTicket = (data) => API.post("v1/tickets/", data);
export const getTicketById = (id) => API.get(`v1/tickets/${id}/`);
export const updateTicket = (id, data) => API.patch(`v1/tickets/${id}/`, data);
export const deleteTicket = (id) => API.delete(`v1/tickets/${id}/`);
export const predictTicket = (data) => API.post("v1/predict/", data);

export const assignTicket = (ticketId, agentId) =>
  API.patch(`v1/tickets/${ticketId}/assign/`, { agent_id: agentId });

export const getAgents = () => API.get("v2/agents/");
export const getCategories = () => API.get("v1/categories/");
export const getTicketComments = (ticketId) => API.get(`v1/tickets/${ticketId}/comments/`);
export const addTicketComment = (ticketId, data) => API.post(`v1/tickets/${ticketId}/comments/`, data);
export const getTicketPredictionFeedback = (ticketId) =>
  API.get(`v1/tickets/${ticketId}/prediction-feedback/`);

export default API;