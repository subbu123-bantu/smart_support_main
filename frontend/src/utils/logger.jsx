const isDev = process.env.NODE_ENV !== "production";

const createLogObject = (level, message, meta) => ({
  level,
  message,
  ...(meta ? { meta } : {}),
  time: new Date().toISOString(),
});

const logger = {
  info(message, meta) {
    if (isDev) {
      console.log(createLogObject("INFO", message, meta));
    }
  },

  warn(message, meta) {
    if (isDev) {
      console.warn(createLogObject("WARN", message, meta));
    }
  },

  error(message, meta) {
    console.error(createLogObject("ERROR", message, meta));
  },

  debug(message, meta) {
    if (isDev) {
      console.debug(createLogObject("DEBUG", message, meta));
    }
  },
};

export default logger;