jest.mock("web-vitals", () => ({
  getCLS: jest.fn(),
  getFID: jest.fn(),
  getFCP: jest.fn(),
  getLCP: jest.fn(),
  getTTFB: jest.fn(),
}));

describe("reportWebVitals", () => {
  beforeEach(() => {
    jest.resetModules();
  });

  test("does nothing when onPerfEntry is not a function", () => {
    const reportWebVitals = require("../reportWebVitals").default;
    const metrics = require("web-vitals");

    reportWebVitals(undefined);

    expect(metrics.getCLS).not.toHaveBeenCalled();
    expect(metrics.getFID).not.toHaveBeenCalled();
    expect(metrics.getFCP).not.toHaveBeenCalled();
    expect(metrics.getLCP).not.toHaveBeenCalled();
    expect(metrics.getTTFB).not.toHaveBeenCalled();
  });
});
