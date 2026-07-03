// === MODULE_BUILD ===
// id: fe_lib_auth
//   module_name: auth
//   module_kind: ui_lib
//   summary: AuthContext + useAuth hook + ProtectedRoute — manages JWT-cookie session, exposes user/loading/login/register/logout/refresh, redirects unauthenticated traffic to /login while keeping the splash & login routes public
//   owner: Erin Spencer
//   public_surface: AuthProvider, useAuth, ProtectedRoute, formatApiErrorDetail
//   internal_surface: AuthCtx
//   auth_boundary: bearer
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; app becomes single-user demo again
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_lib_auth_boundaries
//   summary: client-side auth state container + axios wrapper
//   auth_boundary: bearer
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_lib_auth
//   summary: auth state + ProtectedRoute
//   exposes: AuthProvider, useAuth, ProtectedRoute, formatApiErrorDetail
//   boundaries: auth:bearer, storage:none, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import axios from "axios";

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const client = axios.create({ baseURL: `${BACKEND}/api`, withCredentials: true });

export function formatApiErrorDetail(detail) {
  if (detail == null) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map(e => e?.msg || JSON.stringify(e)).join(" · ");
  if (detail?.msg) return detail.msg;
  return String(detail);
}

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined); // undefined = checking, null = anon, obj = authed
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const { data } = await client.get("/auth/me");
      setUser(data.user || null);
    } catch (e) {
      setUser(null);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const register = useCallback(async ({ username, email, passphrase }) => {
    setError(null);
    try {
      const { data } = await client.post("/auth/register", { username, email, passphrase });
      setUser(data.user);
      return data.user;
    } catch (e) {
      const msg = formatApiErrorDetail(e.response?.data?.detail) || e.message;
      setError(msg);
      throw new Error(msg);
    }
  }, []);

  const login = useCallback(async ({ identifier, passphrase }) => {
    setError(null);
    try {
      const { data } = await client.post("/auth/login", { identifier, passphrase });
      setUser(data.user);
      return data.user;
    } catch (e) {
      const msg = formatApiErrorDetail(e.response?.data?.detail) || e.message;
      setError(msg);
      throw new Error(msg);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await client.post("/auth/logout");
    } catch (e) {
      // Non-fatal: clear local session even if the network call fails.
      console.debug("logout request failed; clearing local session anyway", e);
    }
    setUser(null);
  }, []);

  const googleSession = useCallback(async (session_id) => {
    const { data } = await client.post("/auth/oauth/google-session", { session_id });
    setUser(data.user);
    return data.user;
  }, []);

  const githubExchange = useCallback(async (code) => {
    const { data } = await client.post("/auth/oauth/github/callback", { code });
    setUser(data.user);
    return data.user;
  }, []);

  const value = { user, error, refresh, register, login, logout, googleSession, githubExchange };
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export function useAuth() {
  const v = useContext(AuthCtx);
  if (!v) throw new Error("useAuth must be inside <AuthProvider>");
  return v;
}

export function ProtectedRoute({ children, fallback = "/login" }) {
  const { user } = useAuth();
  const location = useLocation();
  if (user === undefined) {
    return (
      <div className="min-h-[40vh] grid place-items-center text-neutral-500 font-mono text-xs" data-testid="auth-checking">
        verifying session…
      </div>
    );
  }
  if (!user) {
    return <Navigate to={fallback} replace state={{ from: location }} />;
  }
  return children;
}
