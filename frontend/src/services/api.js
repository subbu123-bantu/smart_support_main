import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api/",
});



//REQUEST INTERCEPTOR (attach token)
API.interceptors.request.use(
  (req) => {
    const token = localStorage.getItem("token");

    if (token) {
      req.headers.Authorization = `Bearer ${token}`;
    }

    return req;
  },
  (error) => Promise.reject(error)
);

API.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLoginRequest = error.config.url.includes("login");
    if (error.response && error.response.status === 401 && !isLoginRequest) {
      console.log("Unauthorized → Redirecting to login");

      localStorage.removeItem("token");

      window.location.href = "/login";
    }

    return Promise.reject(error);
  }
);


//AUTH
export const loginUser = (data) => API.post("login/", data);

export const registerUser = (data) => API.post("register/", data);


// DASHBOARD 
export const dashboardStats = () => API.get("dashboard-stats/");

export const getTicketStats = () => API.get("tickets/stats/");


// TICKETS 
export const getTickets = (page = 1,ticketStatus = "",priority = "",search = "") => {

  let url = `tickets/?page=${page}`;

  if (ticketStatus) url += `&status=${ticketStatus}`;
  if (priority && priority.toLowerCase() !== "all")
    url += `&priority=${priority}`;
  if (search) url += `&search=${search}`;

  console.log("CALLING URL:", url);

  return API.get(url);
};

export const createTicket = (data) => API.post("tickets/", data);

export const getTicketById = (id) => API.get(`tickets/${id}/`);

export const updateTicket = (id, data) =>
  API.patch(`tickets/${id}/`, data);

export const deleteTicket = (id) =>
  API.delete(`tickets/${id}/`);


// AI 
export const predictTicket = (data) =>
  API.post("predict/", data);


export default API;