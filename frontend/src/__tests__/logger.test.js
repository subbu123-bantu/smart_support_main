const loadLogger = () => require("../utils/logger").default;

describe("logger utility", () => {
  const originalEnv = process.env.NODE_ENV;

  beforeEach(() => {
    jest.resetModules();
    jest.clearAllMocks();
  });

  afterAll(() => {
    process.env.NODE_ENV = originalEnv;
  });

  test("logs info, warn, debug, and error in development", () => {
    process.env.NODE_ENV = "test";
    const infoSpy = jest.spyOn(console, "log").mockImplementation(() => {});
    const warnSpy = jest.spyOn(console, "warn").mockImplementation(() => {});
    const errorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    const debugSpy = jest.spyOn(console, "debug").mockImplementation(() => {});

    const logger = loadLogger();

    logger.info("Info message", { count: 1 });
    logger.warn("Warn message");
    logger.error("Error message", { issue: true });
    logger.debug("Debug message");

    expect(infoSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        level: "INFO",
        message: "Info message",
        meta: { count: 1 },
      }),
    );
    expect(warnSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        level: "WARN",
        message: "Warn message",
      }),
    );
    expect(errorSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        level: "ERROR",
        message: "Error message",
        meta: { issue: true },
      }),
    );
    expect(debugSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        level: "DEBUG",
        message: "Debug message",
      }),
    );
  });

  test("suppresses non-error logs in production", () => {
    process.env.NODE_ENV = "production";
    const infoSpy = jest.spyOn(console, "log").mockImplementation(() => {});
    const warnSpy = jest.spyOn(console, "warn").mockImplementation(() => {});
    const errorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    const debugSpy = jest.spyOn(console, "debug").mockImplementation(() => {});

    const logger = loadLogger();

    logger.info("Info message");
    logger.warn("Warn message");
    logger.error("Error message");
    logger.debug("Debug message");

    expect(infoSpy).not.toHaveBeenCalled();
    expect(warnSpy).not.toHaveBeenCalled();
    expect(debugSpy).not.toHaveBeenCalled();
    expect(errorSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        level: "ERROR",
        message: "Error message",
      }),
    );
  });
});
