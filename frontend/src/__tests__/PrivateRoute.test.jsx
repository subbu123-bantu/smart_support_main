import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import PrivateRoute from "../components/PrivateRoute";

describe("PrivateRoute", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test("renders protected content when an access token is present", () => {
    localStorage.setItem("access", "token-123");

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route
            path="/dashboard"
            element={(
              <PrivateRoute>
                <div>Protected dashboard</div>
              </PrivateRoute>
            )}
          />
          <Route path="/login" element={<div>Login page</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Protected dashboard")).toBeInTheDocument();
  });

  test("redirects to login when no access token is present", () => {
    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route
            path="/dashboard"
            element={(
              <PrivateRoute>
                <div>Protected dashboard</div>
              </PrivateRoute>
            )}
          />
          <Route path="/login" element={<div>Login page</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Login page")).toBeInTheDocument();
  });
});
