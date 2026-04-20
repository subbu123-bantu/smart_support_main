import "@testing-library/jest-dom";
import { CATEGORY_META, PRIORITY_META, STATUS_META } from "../constants";
import logger from "../utils/logger";
import {
  AgentWorkloadTable,
  ChartsSection,
  RecentTicketsSection,
  StatsCards,
} from "../components/dashboard";

jest.mock("../App", () => () => <div data-testid="app-root">App</div>);
jest.mock("react-dom/client", () => ({
  createRoot: jest.fn(() => ({
    render: jest.fn(),
  })),
}));

describe("foundation modules", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("exports constants and dashboard barrel members", async () => {
    expect(PRIORITY_META.high.label).toBe("High");
    expect(STATUS_META.closed.label).toBe("Closed");
    expect(CATEGORY_META.other.label).toBe("Other");
    expect(AgentWorkloadTable).toBeDefined();
    expect(ChartsSection).toBeDefined();
    expect(RecentTicketsSection).toBeDefined();
    expect(StatsCards).toBeDefined();

    jest.doMock("../reportWebVitals", () => jest.fn());
    await import("../index");
    const ReactDOM = await import("react-dom/client");
    const mockedReportWebVitals = (await import("../reportWebVitals")).default;
    expect(ReactDOM.createRoot).toHaveBeenCalled();
    expect(mockedReportWebVitals).toHaveBeenCalled();
  });

  test("loads web vitals only when callback is a function", async () => {
    jest.resetModules();
    jest.dontMock("../reportWebVitals");
    const getCLS = jest.fn();
    const getFID = jest.fn();
    const getFCP = jest.fn();
    const getLCP = jest.fn();
    const getTTFB = jest.fn();

    jest.doMock("web-vitals", () => ({
      getCLS,
      getFID,
      getFCP,
      getLCP,
      getTTFB,
    }));

    const perfCallback = jest.fn();
    const dynamicReportWebVitals = require("../reportWebVitals").default;
    dynamicReportWebVitals(perfCallback);
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(getCLS).toHaveBeenCalledWith(perfCallback);
    expect(getFID).toHaveBeenCalledWith(perfCallback);
    expect(getFCP).toHaveBeenCalledWith(perfCallback);
    expect(getLCP).toHaveBeenCalledWith(perfCallback);
    expect(getTTFB).toHaveBeenCalledWith(perfCallback);
  });

  test("logger writes messages to console helpers", () => {
    const infoSpy = jest.spyOn(console, "log").mockImplementation(() => {});
    const warnSpy = jest.spyOn(console, "warn").mockImplementation(() => {});
    const errorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    const debugSpy = jest.spyOn(console, "debug").mockImplementation(() => {});

    logger.info("loaded", { page: "dashboard" });
    logger.warn("slow", { ms: 100 });
    logger.error("failed", { code: 500 });
    logger.debug("trace", { value: 1 });

    expect(infoSpy).toHaveBeenCalled();
    expect(warnSpy).toHaveBeenCalled();
    expect(errorSpy).toHaveBeenCalled();
    expect(debugSpy).toHaveBeenCalled();

    infoSpy.mockRestore();
    warnSpy.mockRestore();
    errorSpy.mockRestore();
    debugSpy.mockRestore();
  });
});
