describe("services, utils, and web vitals", () => {
  beforeEach(() => {
    jest.resetModules();
    localStorage.clear();
  });

  test("api helpers build params and register interceptors", async () => {
    const requestHandlers = {};
    const responseHandlers = {};
    const mockApi = {
      get: jest.fn(),
      post: jest.fn(),
      patch: jest.fn(),
      delete: jest.fn(),
      interceptors: {
        request: { use: (ok, bad) => Object.assign(requestHandlers, { ok, bad }) },
        response: { use: (ok, bad) => Object.assign(responseHandlers, { ok, bad }) },
      },
    };
    const errorSpy = jest.spyOn(console, "error").mockImplementation(() => undefined);
    jest.doMock("axios", () => ({ create: jest.fn(() => mockApi) }));
    const api = require("../services/api");

    localStorage.setItem("access", "abc");
    api.getTickets(2, "open", "high", "printer", "true", "4");

    expect(mockApi.get).toHaveBeenCalledWith("tickets/", { params: { page: 2, status: "open", priority: "high", search: "printer", assigned: "true", category: "4" } });

    api.getTicketStats();
    api.getTicketById(7);
    api.getAgents();
    api.getCategories();
    api.getTicketComments(2);
    api.getTicketPredictionFeedback(2);
    api.createTicket({ a: 1 });
    api.predictTicket({ text: "x" });
    api.loginUser({});
    api.registerUser({});
    api.requestPasswordReset({});
    api.resetPassword({});
    api.changeEmail({});
    api.updateTicket(7, { status: "closed" });
    api.assignTicket(7, 3);
    api.updateAgentProfile(3, { active: true });
    api.addTicketComment(2, { message: "hi" });

    expect(requestHandlers.ok({ url: "tickets/", headers: {} }).headers.Authorization).toBe("Bearer abc");
    expect(requestHandlers.ok({ url: "login/", headers: {} }).headers.Authorization).toBeUndefined();
    await expect(responseHandlers.bad({ config: { url: "tickets/" }, response: { status: 401 } })).rejects.toEqual({ config: { url: "tickets/" }, response: { status: 401 } });
    expect(localStorage.getItem("access")).toBeNull();

    errorSpy.mockRestore();
  });

  test("api base url respects env and clearAuthStorage removes keys", () => {
    process.env.REACT_APP_API_BASE_URL = "http://api.example.com";
    const mockApi = { interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } } };
    jest.doMock("axios", () => ({ create: jest.fn(() => mockApi) }));
    const axios = require("axios");
    const { clearAuthStorage } = require("../services/api");
    localStorage.setItem("access", "a");
    localStorage.setItem("role", "r");
    clearAuthStorage();
    expect(axios.create).toHaveBeenCalledWith({ baseURL: "http://api.example.com/" });
    expect(localStorage.getItem("access")).toBeNull();
    delete process.env.REACT_APP_API_BASE_URL;
  });

  test("logger writes expected levels in development", () => {
    const log = jest.spyOn(console, "log").mockImplementation(() => undefined);
    const warn = jest.spyOn(console, "warn").mockImplementation(() => undefined);
    const error = jest.spyOn(console, "error").mockImplementation(() => undefined);
    const debug = jest.spyOn(console, "debug").mockImplementation(() => undefined);
    const logger = require("../utils/logger").default;

    logger.info("hello", { a: 1 });
    logger.warn("careful");
    logger.error("bad");
    logger["debug"]("trace");

    expect(log).toHaveBeenCalled();
    expect(warn).toHaveBeenCalled();
    expect(error).toHaveBeenCalled();
    expect(debug).toHaveBeenCalled();
  });

  test("reportWebVitals calls all metric getters when callback exists", async () => {
    const getCLS = jest.fn(), getFID = jest.fn(), getFCP = jest.fn(), getLCP = jest.fn(), getTTFB = jest.fn();
    jest.doMock("web-vitals", () => ({ getCLS, getFID, getFCP, getLCP, getTTFB }));
    const reportWebVitals = require("../reportWebVitals").default;
    const cb = jest.fn();
    reportWebVitals(cb);
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(getCLS).toHaveBeenCalledWith(cb);
    expect(getFID).toHaveBeenCalledWith(cb);
    expect(getFCP).toHaveBeenCalledWith(cb);
    expect(getLCP).toHaveBeenCalledWith(cb);
    expect(getTTFB).toHaveBeenCalledWith(cb);
  });

  test("entry and barrel modules load", () => {
    const render = jest.fn();
    const createRoot = jest.fn(() => ({ render }));
    const reportWebVitals = jest.fn();

    document.body.innerHTML = '<div id="root"></div>';
    jest.doMock("react-dom/client", () => ({ __esModule: true, default: { createRoot }, createRoot }));
    jest.doMock("../App", () => ({ __esModule: true, default: () => null }));
    jest.doMock("../reportWebVitals", () => ({ __esModule: true, default: reportWebVitals }));

    require("../index");

    expect(createRoot).toHaveBeenCalledWith(document.getElementById("root"));
    expect(render).toHaveBeenCalled();
    expect(reportWebVitals).toHaveBeenCalled();
    expect(require("../components/dashboard").StatsCards).toBeDefined();
    expect(require("../constants").CATEGORY_META).toBeDefined();
  });
});
