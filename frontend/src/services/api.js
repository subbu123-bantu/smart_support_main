import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api/",
});

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


export const loginUser = async (data) => {
  return API.post("login/", data);
};

export const registerUser = async (data) => {
  return API.post("register/", data);
};

export const getTickets = (page = 1, ticketStatus = "", priority = "", search = "") => {

  let url = `tickets/?page=${page}`;

  if (ticketStatus) {
    url += `&status=${ticketStatus}`;
  }

  if (priority && priority.toLowerCase() !== "all") {
    url += `&priority=${priority}`;
  }

  if (search) {
    url += `&search=${search}`;
  }
  console.log("CALLING URL:", url); 

  return API.get(url);
};


export const createTicket = (data) => {
  const token = localStorage.getItem("token"); // get token from login
  return API.post('tickets/', data, {
    headers: {
      Authorization: `Bearer ${token}`,  // MUST include token
      "Content-Type": "application/json",
    },
  });
};


export const getTicketById = async (id) => {
  return API.get(`tickets/${id}/`);
};


export const updateTicket = async (id, data) => {
  return API.patch(`tickets/${id}/`, data);
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

export const predictTicket = (data) => {
  return API.post("predict/", data);
};