const mockApi = {
  interceptors: {
    request: { use: jest.fn() },
    response: { use: jest.fn() },
  },
  get: jest.fn(),
  post: jest.fn(),
  patch: jest.fn(),
  delete: jest.fn(),
};

jest.mock("axios", () => ({
  create: jest.fn(() => mockApi),
}));

describe("api service", () => {
  let requestFulfilled;
  let requestRejected;
  let responseFulfilled;
  let responseRejected;
  let apiModule;
  let originalLocation;

  beforeEach(() => {
    jest.resetModules();
    jest.clearAllMocks();
    localStorage.clear();

    mockApi.interceptors.request.use.mockImplementation((fulfilled, rejected) => {
      requestFulfilled = fulfilled;
      requestRejected = rejected;
    });

    mockApi.interceptors.response.use.mockImplementation((fulfilled, rejected) => {
      responseFulfilled = fulfilled;
      responseRejected = rejected;
    });

    originalLocation = globalThis.location;
    delete globalThis.location;
    globalThis.location = { href: "http://localhost/" };

    apiModule = require("../services/api");
  });

  afterEach(() => {
    globalThis.location = originalLocation;
  });

  test("adds bearer token for protected requests", () => {
    localStorage.setItem("access", "token-123");
    const request = { url: "tickets/", headers: {} };

    const result = requestFulfilled(request);

    expect(result.headers.Authorization).toBe("Bearer token-123");
  });

  test("does not attach bearer token for public routes", () => {
    localStorage.setItem("access", "token-123");
    const request = { url: "login/", headers: {} };

    const result = requestFulfilled(request);

    expect(result.headers.Authorization).toBeUndefined();
  });

  test("treats password reset routes as public", () => {
    localStorage.setItem("access", "token-123");

    const forgotRequest = { url: "forgot-password/", headers: {} };
    const resetRequest = { url: "reset-password/", headers: {} };

    expect(requestFulfilled(forgotRequest).headers.Authorization).toBeUndefined();
    expect(requestFulfilled(resetRequest).headers.Authorization).toBeUndefined();
  });

  test("leaves protected requests unchanged when no token is available", () => {
    const request = { url: "tickets/", headers: {} };

    const result = requestFulfilled(request);

    expect(result.headers.Authorization).toBeUndefined();
  });

  test("passes request interceptor errors through rejection", async () => {
    const error = new Error("request failed");

    await expect(requestRejected(error)).rejects.toThrow("request failed");
  });

  test("returns response unchanged in response success interceptor", () => {
    const response = { data: { ok: true } };

    expect(responseFulfilled(response)).toBe(response);
  });

  test("clears auth data and redirects on non-login 401 responses", async () => {
    localStorage.setItem("access", "token-123");
    localStorage.setItem("role", "admin");
    localStorage.setItem("username", "subbu");
    localStorage.setItem("email", "subbu@example.com");

    const error = {
      config: { url: "tickets/" },
      response: { status: 401 },
    };

    await expect(responseRejected(error)).rejects.toEqual(error);
    expect(localStorage.getItem("access")).toBeNull();
    expect(localStorage.getItem("role")).toBeNull();
    expect(localStorage.getItem("username")).toBeNull();
    expect(localStorage.getItem("email")).toBeNull();
    expect(globalThis.location.href).toBe("/login");
  });

  test("does not clear auth data for login 401 responses", async () => {
    localStorage.setItem("access", "token-123");

    const error = {
      config: { url: "login/" },
      response: { status: 401 },
    };

    await expect(responseRejected(error)).rejects.toEqual(error);
    expect(localStorage.getItem("access")).toBe("token-123");
  });

  test("does not redirect for non-401 responses", async () => {
    localStorage.setItem("access", "token-123");

    const error = {
      config: { url: "tickets/" },
      response: { status: 500 },
    };

    await expect(responseRejected(error)).rejects.toEqual(error);
    expect(localStorage.getItem("access")).toBe("token-123");
    expect(globalThis.location.href).toBe("http://localhost/");
  });

  test("redirects on 401 even when request url is missing", async () => {
    localStorage.setItem("access", "token-123");
    localStorage.setItem("role", "agent");

    const error = {
      config: {},
      response: { status: 401 },
    };

    await expect(responseRejected(error)).rejects.toEqual(error);
    expect(localStorage.getItem("access")).toBeNull();
    expect(localStorage.getItem("role")).toBeNull();
    expect(globalThis.location.href).toBe("/login");
  });

  test("loginUser posts to login endpoint", () => {
    const payload = { username: "subbu", password: "example" };

    apiModule.loginUser(payload);

    expect(mockApi.post).toHaveBeenCalledWith("login/", payload);
  });

  test("registerUser posts to register endpoint", () => {
    const payload = { username: "new-user" };

    apiModule.registerUser(payload);

    expect(mockApi.post).toHaveBeenCalledWith("register/", payload);
  });

  test("password reset helpers call the expected endpoints", () => {
    const forgotPayload = { email: "user@example.com" };
    const resetPayload = {
      uid: "uid-1",
      token: "token-1",
      password: "pass123",
      confirm_password: "pass123",
    };
    const changeEmailPayload = {
      email: "updated@example.com",
      current_password: "secret",
    };

    apiModule.requestPasswordReset(forgotPayload);
    apiModule.resetPassword(resetPayload);
    apiModule.changeEmail(changeEmailPayload);

    expect(mockApi.post).toHaveBeenCalledWith("forgot-password/", forgotPayload);
    expect(mockApi.post).toHaveBeenCalledWith("reset-password/", resetPayload);
    expect(mockApi.patch).toHaveBeenCalledWith("change-email/", changeEmailPayload);
  });

  test("getTicketStats fetches stats endpoint", () => {
    apiModule.getTicketStats();

    expect(mockApi.get).toHaveBeenCalledWith("stats/");
  });

  test("getTickets builds query params from provided filters", () => {
    apiModule.getTickets(2, "open", "high", "router", "true", "network");

    expect(mockApi.get).toHaveBeenCalledWith("tickets/", {
      params: {
        page: 2,
        status: "open",
        priority: "high",
        search: "router",
        assigned: "true",
        category: "network",
      },
    });
  });

  test("getTickets omits optional params when filters are empty or all", () => {
    apiModule.getTickets();
    apiModule.getTickets(1, "", "all", "", "", "");

    expect(mockApi.get).toHaveBeenNthCalledWith(1, "tickets/", {
      params: { page: 1 },
    });
    expect(mockApi.get).toHaveBeenNthCalledWith(2, "tickets/", {
      params: { page: 1 },
    });
  });

  test("ticket mutation helpers call the expected endpoints", () => {
    const payload = { title: "Printer issue" };

    apiModule.createTicket(payload);
    apiModule.getTicketById(7);
    apiModule.updateTicket(7, { status: "closed" });
    apiModule.deleteTicket(7);
    apiModule.predictTicket({ text: "Printer issue" });
    apiModule.assignTicket(7, 3);

    expect(mockApi.post).toHaveBeenCalledWith("tickets/", payload);
    expect(mockApi.get).toHaveBeenCalledWith("tickets/7/");
    expect(mockApi.patch).toHaveBeenCalledWith("tickets/7/", { status: "closed" });
    expect(mockApi.delete).toHaveBeenCalledWith("tickets/7/");
    expect(mockApi.post).toHaveBeenCalledWith("predict/", { text: "Printer issue" });
    expect(mockApi.patch).toHaveBeenCalledWith("tickets/7/assign/", { agent_id: 3 });
  });

  test("auxiliary fetch helpers call the expected endpoints", () => {
    apiModule.getAgents();
    apiModule.updateAgentProfile(3, { categories: [1, 2] });
    apiModule.getCategories();
    apiModule.getTicketComments(4);
    apiModule.addTicketComment(4, { message: "Hello" });
    apiModule.getTicketPredictionFeedback(4);

    expect(mockApi.get).toHaveBeenCalledWith("agents/");
    expect(mockApi.patch).toHaveBeenCalledWith("agents/3/", { categories: [1, 2] });
    expect(mockApi.get).toHaveBeenCalledWith("categories/");
    expect(mockApi.get).toHaveBeenCalledWith("tickets/4/comments/");
    expect(mockApi.post).toHaveBeenCalledWith("tickets/4/comments/", { message: "Hello" });
    expect(mockApi.get).toHaveBeenCalledWith("tickets/4/prediction-feedback/");
  });
});
