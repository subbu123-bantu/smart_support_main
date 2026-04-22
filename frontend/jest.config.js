module.exports = {
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/src/setupTests.js"],
  transform: {
    "^.+\\.[jt]sx?$": "babel-jest",
  },
  moduleFileExtensions: ["js", "jsx", "json"],
  moduleNameMapper: {
    "\\.(css|less|sass|scss)$": "<rootDir>/test/styleMock.js",
    "\\.(gif|ttf|eot|svg|png|jpg|jpeg|webp)$": "<rootDir>/test/fileMock.js",
  },
};
