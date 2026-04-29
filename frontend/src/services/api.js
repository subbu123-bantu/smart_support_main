/* global globalThis */
import axios from "axios";

const DEFAULT_API_BASE_URL = "http://localhost:8000/api/";

const getApiBaseUrl = () => {
  const configuredBaseUrl = process.env.REACT_APP_API_BASE_URL?.trim();
  if (!configuredBaseUrl) {
    return DEFAULT_API_BASE_URL;
  }

  return configuredBaseUrl.endsWith("/")
    ? configuredBaseUrl
    : `${configuredBaseUrl}/`;
};

const clearAuthStorage = () => {
  localStorage.removeItem("access");
  localStorage.removeItem("role");
  localStorage.removeItem("username");
  localStorage.removeItem("email");
};

const API = axios.create({
  baseURL: getApiBaseUrl(),
});

API.interceptors.request.use(
  (request) => {
    const publicRoutes = ["login/", "register/", "forgot-password/", "reset-password/"];
    const isPublicRoute = publicRoutes.some((route) =>
      request.url?.includes(route)
    );

    if (!isPublicRoute) {
      const token = localStorage.getItem("access");

      if (token) {
        request.headers.Authorization = `Bearer ${token}`;
      }
    }

    return request;
  },
  (error) => Promise.reject(error)
);

API.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl = error.config?.url || "";
    const isLoginRequest = requestUrl.includes("login/");

    if (error.response?.status === 401 && !isLoginRequest) {
      clearAuthStorage();
      globalThis.location.href = "/login";
    }

    return Promise.reject(error);
  }
);

// AUTH
export const loginUser = (data) => API.post("login/", data);
export const registerUser = (data) => API.post("register/", data);
export const requestPasswordReset = (data) => API.post("forgot-password/", data);
export const resetPassword = (data) => API.post("reset-password/", data);
export const changeEmail = (data) => API.patch("change-email/", data);

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
  const params = { page };

  if (ticketStatus) params.status = ticketStatus;
  if (priority && priority !== "all") params.priority = priority;
  if (search) params.search = search;
  if (assigned !== "") params.assigned = assigned;
  if (category) params.category = category;

  return API.get("tickets/", { params });
};

export const createTicket = (data) => API.post("tickets/", data);
export const getTicketById = (id) => API.get(`tickets/${id}/`);
export const updateTicket = (id, data) => API.patch(`tickets/${id}/`, data);
export const deleteTicket = (id) => API.delete(`tickets/${id}/`);
export const predictTicket = (data) => API.post("predict/", data);

export const assignTicket = (ticketId, agentId) =>
  API.patch(`tickets/${ticketId}/assign/`, { agent_id: agentId });

export const getAgents = () => API.get("agents/");
export const updateAgentProfile = (agentId, data) => API.patch(`agents/${agentId}/`, data);
export const getCategories = () => API.get("categories/");
export const getTicketComments = (ticketId) =>
  API.get(`tickets/${ticketId}/comments/`);
export const addTicketComment = (ticketId, data) =>
  API.post(`tickets/${ticketId}/comments/`, data);
export const getTicketPredictionFeedback = (ticketId) =>
  API.get(`tickets/${ticketId}/prediction-feedback/`);

export { clearAuthStorage };
export default API;
