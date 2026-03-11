import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api"
});

// Automatically attach token to requests
API.interceptors.request.use((config) => {

  const token = localStorage.getItem("token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export const loginUser = (data) => API.post("/login/", data);

export const registerUser = (data) => API.post("/register/", data);

export const getTickets = () => API.get("/tickets/");

export const createTicket = (data) => API.post("/tickets/", data);

export const getTicketById = (id) => API.get(`/tickets/${id}/`);

export const updateTicket = (id, data) => API.put(`/tickets/${id}/`, data);

export default API;