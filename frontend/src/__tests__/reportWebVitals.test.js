describe("reportWebVitals", () => {
  afterEach(() => {
    jest.resetModules();
    jest.clearAllMocks();
  });

  test("does nothing when callback is not a function", () => {
    const reportWebVitals = require("../reportWebVitals").default;
    expect(() => reportWebVitals()).not.toThrow();
    expect(() => reportWebVitals("not-a-function")).not.toThrow();
  });

  test("subscribes to all web-vitals metrics when callback is provided", async () => {
    const onPerfEntry = jest.fn();
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

    const reportWebVitals = require("../reportWebVitals").default;
    reportWebVitals(onPerfEntry);

    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(getCLS).toHaveBeenCalledWith(onPerfEntry);
    expect(getFID).toHaveBeenCalledWith(onPerfEntry);
    expect(getFCP).toHaveBeenCalledWith(onPerfEntry);
    expect(getLCP).toHaveBeenCalledWith(onPerfEntry);
    expect(getTTFB).toHaveBeenCalledWith(onPerfEntry);
  });
});
