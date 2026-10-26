// === MODULE_BUILD ===
// id: fe_page_login
//   module_name: LoginPage
//   module_kind: ui_page
//   summary: tabbed sign-in / sign-up screen — username or email + ≥16-char passphrase (show/hide toggle) + Emergent Google + GitHub OAuth; auto-resumes the user's intended route after auth
//   owner: Erin Spencer
//   public_surface: LoginPage
//   internal_surface: PassphraseField, SocialRow
//   auth_boundary: bearer
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; user cannot sign in via UI
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_page_login_boundaries
//   summary: sign-in / sign-up form
//   auth_boundary: bearer
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_login
//   summary: sign-in / sign-up form
//   exposes: LoginPage
//   boundaries: auth:bearer, storage:none, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useLocation, Link, useSearchParams } from "react-router-dom";
import axios from "axios";
import { Eye, EyeSlash, GoogleLogo, GithubLogo, ArrowRight } from "@phosphor-icons/react";
import { useAuth } from "../lib/auth";

const BACKEND = process.env.REACT_APP_BACKEND_URL;

function PassphraseField({ value, onChange, testid, label = "passphrase (≥16 chars)", hint }) {
  const [show, setShow] = useState(false);
  const minOk = value.length >= 16;
  return (
    <label className="block space-y-1" data-testid={`${testid}-wrap`}>
      <span className="block text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">{label}</span>
      <div className="relative">
        <input
          data-testid={testid}
          type={show ? "text" : "password"}
          value={value}
          onChange={e => onChange(e.target.value)}
          className="w-full bg-bg-surface border border-white/10 px-2 py-2 pr-9 font-mono text-sm text-white"
          autoComplete="current-password"
        />
        <button
          type="button"
          data-testid={`${testid}-toggle`}
          onClick={() => setShow(s => !s)}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-white"
          aria-label={show ? "hide" : "show"}
        >
          {show ? <EyeSlash size={16} /> : <Eye size={16} />}
        </button>
      </div>
      {hint && (
        <div className={`text-[0.6rem] font-mono ${minOk ? "text-emerald-400/70" : "text-amber-400/80"}`}>
          {minOk ? "✓ minimum length met" : `${value.length}/16 chars`}
        </div>
      )}
    </label>
  );
}

function SocialRow({ disabled, onGoogle, onGithub }) {
  return (
    <div className="grid grid-cols-2 gap-2 pt-2" data-testid="social-row">
      <button type="button" data-testid="social-google-btn"
              onClick={onGoogle} disabled={disabled}
              className="flex items-center justify-center gap-2 px-3 py-2 border border-white/15 text-white font-mono text-xs uppercase tracking-wider hover:bg-white/5 disabled:opacity-40">
        <GoogleLogo size={16} /> Google
      </button>
      <button type="button" data-testid="social-github-btn"
              onClick={onGithub} disabled={disabled}
              className="flex items-center justify-center gap-2 px-3 py-2 border border-white/15 text-white font-mono text-xs uppercase tracking-wider hover:bg-white/5 disabled:opacity-40">
        <GithubLogo size={16} /> GitHub
      </button>
    </div>
  );
}

export default function LoginPage({ mode: initialMode = "login" }) {
  const [mode, setMode] = useState(initialMode);
  const [identifier, setIdentifier] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [passphrase, setPassphrase] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const { user, login, register, googleSession, githubExchange } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const [params, setParams] = useSearchParams();

  const goNext = useMemo(() => loc.state?.from?.pathname || "/workspace", [loc.state]);

  useEffect(() => {
    if (user) nav(goNext, { replace: true });
  }, [user, goNext, nav]);

  // ---- Emergent Google session redirect handler ----
  useEffect(() => {
    // Emergent redirects with #session_id=... in the URL hash.
    const hash = window.location.hash || "";
    const m = hash.match(/session_id=([^&]+)/);
    if (m) {
      (async () => {
        setBusy(true); setErr(null);
        try {
          await googleSession(decodeURIComponent(m[1]));
          window.history.replaceState({}, "", window.location.pathname);
          nav(goNext, { replace: true });
        } catch (e) {
          setErr(e.message);
        } finally { setBusy(false); }
      })();
    }
    // ---- GitHub callback (?code=) ----
    const code = params.get("code");
    if (code && params.get("github_callback")) {
      (async () => {
        setBusy(true); setErr(null);
        try {
          await githubExchange(code);
          params.delete("code"); params.delete("github_callback"); params.delete("state");
          setParams(params, { replace: true });
          nav(goNext, { replace: true });
        } catch (e) {
          setErr(e.message);
        } finally { setBusy(false); }
      })();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      if (mode === "login") {
        await login({ identifier, passphrase });
      } else {
        await register({ username, email, passphrase });
      }
      // useEffect navigates on user change.
    } catch (ex) {
      setErr(ex.message);
    } finally { setBusy(false); }
  }

  function goGoogle() {
    // Emergent's hosted OAuth widget — redirects back with #session_id=...
    const redirect = encodeURIComponent(`${window.location.origin}/login`);
    window.location.href = `https://auth.emergentagent.com/?redirect=${redirect}`;
  }

  async function goGithub() {
    setBusy(true);
    try {
      const { data } = await axios.get(`${BACKEND}/api/auth/oauth/github/start`, { withCredentials: true });
      if (data?.url) window.location.href = data.url;
    } catch (e) {
      setErr("github oauth not configured — set GITHUB_CLIENT_ID + SECRET on the server");
    } finally { setBusy(false); }
  }

  const canRegister = username.length >= 3 && email.includes("@") && passphrase.length >= 16;
  const canLogin = identifier.length >= 3 && passphrase.length >= 1;

  return (
    <div className="min-h-[70vh] flex items-center justify-center" data-testid="page-login">
      <div className="w-full max-w-md space-y-6">
        <div className="space-y-2">
          <Link to="/" className="text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-500 hover:text-accent-cyan" data-testid="login-home-link">
            ← interdependent way
          </Link>
          <h1 className="text-3xl font-mono text-white" data-testid="login-title">
            {mode === "login" ? "sign in" : "create account"}
          </h1>
          <div className="flex gap-2 text-[0.7rem] font-mono uppercase tracking-wider" data-testid="login-tabs">
            <button data-testid="tab-login" onClick={() => setMode("login")}
                    className={`px-2 py-1 border ${mode === "login" ? "border-accent-cyan text-accent-cyan" : "border-white/10 text-neutral-400"}`}>
              sign in
            </button>
            <button data-testid="tab-register" onClick={() => setMode("register")}
                    className={`px-2 py-1 border ${mode === "register" ? "border-accent-cyan text-accent-cyan" : "border-white/10 text-neutral-400"}`}>
              create account
            </button>
          </div>
        </div>

        {err && (
          <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="login-error">
            {err}
          </div>
        )}

        <form onSubmit={submit} className="space-y-4" data-testid="login-form">
          {mode === "login" ? (
            <label className="block space-y-1">
              <span className="block text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">username or email</span>
              <input
                data-testid="login-identifier-input"
                value={identifier} onChange={e => setIdentifier(e.target.value)}
                className="w-full bg-bg-surface border border-white/10 px-2 py-2 font-mono text-sm text-white"
                placeholder="alice or alice@example.com"
                autoComplete="username"
              />
            </label>
          ) : (
            <>
              <label className="block space-y-1">
                <span className="block text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">username</span>
                <input
                  data-testid="register-username-input"
                  value={username} onChange={e => setUsername(e.target.value.toLowerCase())}
                  className="w-full bg-bg-surface border border-white/10 px-2 py-2 font-mono text-sm text-white"
                  placeholder="alice"
                />
                <span className="block text-[0.6rem] font-mono text-neutral-600">3–32 chars, [a-z0-9_-]</span>
              </label>
              <label className="block space-y-1">
                <span className="block text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">email (required)</span>
                <input
                  data-testid="register-email-input"
                  type="email"
                  value={email} onChange={e => setEmail(e.target.value)}
                  className="w-full bg-bg-surface border border-white/10 px-2 py-2 font-mono text-sm text-white"
                  placeholder="you@example.com"
                />
              </label>
            </>
          )}

          <PassphraseField
            value={passphrase}
            onChange={setPassphrase}
            testid={mode === "login" ? "login-passphrase-input" : "register-passphrase-input"}
            hint={mode === "register"}
            label={mode === "register" ? "passphrase (≥16 chars; show with eye)" : "passphrase"}
          />

          <button
            type="submit"
            disabled={busy || (mode === "login" ? !canLogin : !canRegister)}
            data-testid={mode === "login" ? "login-submit-btn" : "register-submit-btn"}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 border border-accent-cyan/60 text-accent-cyan font-mono text-sm uppercase tracking-wider hover:bg-accent-cyan/10 disabled:opacity-40"
          >
            {busy ? "working…" : (mode === "login" ? "sign in" : "create account")} <ArrowRight size={14} />
          </button>
        </form>

        <div className="flex items-center gap-3 text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-600">
          <span className="flex-1 h-px bg-white/10" /> or <span className="flex-1 h-px bg-white/10" />
        </div>

        <SocialRow disabled={busy} onGoogle={goGoogle} onGithub={goGithub} />

        <p className="text-[0.65rem] font-mono text-neutral-500 text-center pt-2">
          by signing in you accept the canon and accept that the canon may halt.
        </p>
      </div>
    </div>
  );
}
