// === MODULE_BUILD ===
// id: fe_component_shell
//   module_name: Shell
//   module_kind: ui_component
//   summary: left-rail navigation shell with 9 routes (Workspace, Agents, Sentinels, Overrides, Inspector, Inventory, Key Vault, Env Vault, Drafts) and donation CTA
//   owner: Erin Spencer
//   public_surface: Shell
//   internal_surface: items
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: none
//   user_data_boundary: read
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; navigation disappears
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_component_shell_boundaries
//   summary: presentational navigation only
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: none
//   user_data_boundary: read
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_component_shell
//   summary: presentational navigation shell
//   exposes: Shell
//   boundaries: auth:none, storage:none, network:none, user_data:read
//   owner: Erin Spencer
// === END CAPABILITIES ===


import React, { useEffect, useState } from "react";
import { NavLink, Link, useLocation, useNavigate } from "react-router-dom";
import { Atom, KeyReturn, Brain, Cards, Vault, FileText, Pulse, Lightning, Coin, ShieldCheck, ShieldWarning, ScrollIcon as Scroll, SignOut, User as UserIcon, BookOpen, Wrench, Plug, Sparkle, GraduationCap, CirclesThree, Flask } from "@phosphor-icons/react";
import { useAuth } from "../lib/auth";
import { demoQuota } from "../lib/api";

const authedItems = [
  { to: "/workspace",  label: "Workspace",  icon: <Brain size={18} />, testid: "nav-workspace" },
  { to: "/agents",     label: "Agents",     icon: <Lightning size={18} />, testid: "nav-agents" },
  { to: "/training",   label: "Training",   icon: <GraduationCap size={18} />, testid: "nav-training" },
  { to: "/chat-training", label: "Chat Training", icon: <CirclesThree size={18} />, testid: "nav-chat-training" },
  { to: "/agent-lab",  label: "Agent Lab",  icon: <Flask size={18} />, testid: "nav-agent-lab" },
  { to: "/sentinels",  label: "Sentinels",  icon: <ShieldCheck size={18} />, testid: "nav-sentinels" },
  { to: "/overrides",  label: "Overrides",  icon: <ShieldWarning size={18} />, testid: "nav-overrides" },
  { to: "/tools",      label: "Tools",      icon: <Wrench size={18} />, testid: "nav-tools" },
  { to: "/mcp",        label: "MCP",        icon: <Plug size={18} />, testid: "nav-mcp" },
  { to: "/skills",     label: "Skills",     icon: <Sparkle size={18} />, testid: "nav-skills" },
  { to: "/inspector",  label: "Inspector",  icon: <Pulse size={18} />, testid: "nav-inspector" },
  { to: "/inventory",  label: "Inventory",  icon: <Cards size={18} />, testid: "nav-inventory" },
  { to: "/keys",       label: "Model Keys", icon: <KeyReturn size={18} />, testid: "nav-keys" },
  { to: "/custom-keys",label: "Dev Keys",   icon: <Vault size={18} />, testid: "nav-custom-keys" },
  { to: "/vault",      label: "Env Vault",  icon: <Vault size={18} />, testid: "nav-vault" },
  { to: "/drafts",     label: "Drafts",     icon: <FileText size={18} />, testid: "nav-drafts" },
  { to: "/spec",       label: "Living Spec",icon: <BookOpen size={18} />, testid: "nav-spec" },
];

const publicItems = [
  { to: "/",      label: "Home",        icon: <Atom size={18} />, testid: "nav-home" },
  { to: "/spec",  label: "Living Spec", icon: <BookOpen size={18} />, testid: "nav-spec" },
];

function QuotaBar() {
  const [q, setQ] = useState(null);
  useEffect(() => {
    let mounted = true;
    demoQuota.get().then(d => { if (mounted) setQ(d); }).catch(() => {});
    return () => { mounted = false; };
  }, []);
  if (!q) return null;
  const pct = q.budget > 0 ? Math.min(100, Math.round((q.used / q.budget) * 100)) : 0;
  const tone = q.remaining < q.budget * 0.1 ? "rose" : q.remaining < q.budget * 0.3 ? "amber" : "cyan";
  const ring = { cyan: "border-accent-cyan/40 text-accent-cyan", amber: "border-amber-400/40 text-amber-300", rose: "border-rose-500/40 text-rose-300" }[tone];
  return (
    <div className={`p-3 border ${ring}`} data-testid="quota-bar">
      <div className="flex items-center justify-between text-[0.6rem] font-mono uppercase tracking-ultra mb-1">
        <span>emergent demo · {q.day}</span>
        <span>{q.remaining.toLocaleString()} / {q.budget.toLocaleString()}</span>
      </div>
      <div className="h-1 bg-white/10">
        <div className={`h-1 ${tone === "rose" ? "bg-rose-400" : tone === "amber" ? "bg-amber-400" : "bg-accent-cyan"}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="text-[0.6rem] font-mono text-neutral-500 mt-1">tokens used today · resets 00:00 utc</div>
    </div>
  );
}

export default function Shell({ children }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const nav = useNavigate();
  // Hide shell chrome on the splash so the marketing page reads as a fresh canvas.
  const isSplash = location.pathname === "/";
  const items = user ? authedItems : publicItems;

  return (
    <div className="min-h-screen w-full flex flex-col md:flex-row">
      {!isSplash && (
        <aside className="md:w-64 md:min-h-screen border-b md:border-b-0 md:border-r border-white/10 bg-bg-panel flex flex-col">
          <Link to={user ? "/workspace" : "/"} className="px-4 py-5 border-b border-white/10 flex items-center gap-3 hover:bg-bg-surface transition-colors" data-testid="brand-home">
            <Atom size={26} weight="duotone" className="text-accent-cyan" />
            <div>
              <div className="font-mono text-base tracking-tight text-white">a0p</div>
              <div className="text-[0.65rem] tracking-ultra uppercase text-neutral-500">research instrument</div>
            </div>
          </Link>

          <nav className="flex md:flex-col flex-row overflow-x-auto md:overflow-visible py-2 md:py-3">
            {items.map(it => (
              <NavLink
                key={it.to}
                to={it.to}
                end={it.to === "/"}
                data-testid={it.testid}
                className={({ isActive }) =>
                  "flex items-center gap-3 px-4 py-2.5 font-mono text-xs uppercase tracking-ultra border-l-2 transition-colors " +
                  (isActive
                    ? "text-accent-cyan border-accent-cyan bg-bg-surface"
                    : "text-neutral-400 border-transparent hover:text-white hover:bg-bg-surface")
                }
              >
                {it.icon} <span>{it.label}</span>
              </NavLink>
            ))}
          </nav>

          <div className="mt-auto p-4 border-t border-white/10 space-y-3">
            {user ? (
              <>
                <QuotaBar />
                <div className="flex items-center gap-2 p-2 border border-white/10" data-testid="user-pill">
                  <div className="w-8 h-8 border border-white/10 grid place-items-center text-accent-cyan">
                    <UserIcon size={16} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-mono text-xs text-white truncate" data-testid="user-username">{user.username}</div>
                    <div className="font-mono text-[0.6rem] text-neutral-500 truncate">{user.email}</div>
                  </div>
                  <button data-testid="user-signout-btn" onClick={async () => { await logout(); nav("/"); }}
                          className="text-neutral-400 hover:text-rose-300" title="sign out">
                    <SignOut size={14} />
                  </button>
                </div>
              </>
            ) : (
              <Link to="/login" data-testid="shell-signin-btn"
                    className="block text-center px-3 py-2 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10">
                sign in
              </Link>
            )}
            <div className="text-[0.6rem] font-mono text-neutral-600 tracking-wider">
              v0.1 · interdependent-lib
            </div>
          </div>
        </aside>
      )}

      <main className={`flex-1 ${isSplash ? "px-6 md:px-12" : "p-4 md:p-8"} max-w-[1600px] mx-auto w-full`}>
        {children}
      </main>
    </div>
  );
}
