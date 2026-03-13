import axios from "axios";

/* ===============================
   AXIOS INSTANCE
================================ */

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api/",
});

/* ===============================
   REQUEST INTERCEPTOR
   (ADD TOKEN AUTOMATICALLY)
================================ */

API.interceptors.request.use(
  (req) => {

    const token = localStorage.getItem("token");

    if (token) {
      req.headers.Authorization = `Bearer ${token}`;
    }

    return req;
  },
  (error) => {
    return Promise.reject(error);
  }
);


/* ===============================
   AUTH APIs
================================ */

export const loginUser = async (data) => {
  return API.post("login/", data);
};

export const registerUser = async (data) => {
  return API.post("register/", data);
};


/* ===============================
   TICKET APIs
================================ */

export const getTickets = async (
  page = 1,
  priority = "all",
  search = ""
) => {

  let url = `tickets/?page=${page}`;

  if (priority !== "all") {
    url += `&priority=${priority}`;
  }

  if (search.trim() !== "") {
    url += `&search=${encodeURIComponent(search)}`;
  }

  return API.get(url);
};


export const createTicket = async (data) => {
  return API.post("tickets/", data);
};


export const getTicketById = async (id) => {
  return API.get(`tickets/${id}/`);
};


export const updateTicket = async (id, data) => {
  return API.put(`tickets/${id}/`, data);
};


export const deleteTicket = async (id) => {
  return API.delete(`tickets/${id}/`);
};


/* ===============================
   DASHBOARD STATS
================================ */

export const getTicketStats = async () => {
  return API.get("tickets/stats/");
};


export default API;