// === MODULE_BUILD ===
// id: fe_component_panel
//   module_name: Panel
//   module_kind: ui_component
//   summary: shared presentational primitives — Panel section, Pill badge, Stat metric tile, AsciiLoader progress indicator
//   owner: Erin Spencer
//   public_surface: Panel, Pill, Stat, AsciiLoader
//   internal_surface: none
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: none
//   user_data_boundary: read
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; downstream pages lose Panel/Pill/Stat helpers
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_component_panel_boundaries
//   summary: presentational only
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: none
//   user_data_boundary: read
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_component_panel
//   summary: presentational primitives for shells
//   exposes: Panel, Pill, Stat, AsciiLoader
//   boundaries: auth:none, storage:none, network:none, user_data:read
//   owner: Erin Spencer
// === END CAPABILITIES ===


import React from "react";

export function Panel({ title, right, children, className = "", testid }) {
  return (
    <section
      data-testid={testid}
      className={`panel ${className}`}
    >
      {(title || right) && (
        <header className="flex items-center justify-between px-4 py-2 border-b border-white/10">
          <div className="section-overline">{title}</div>
          {right}
        </header>
      )}
      <div>{children}</div>
    </section>
  );
}

export function Pill({ tone = "default", children, testid }) {
  const cls = {
    default: "pill",
    cyan: "pill pill-cyan",
    amber: "pill pill-amber",
    emerald: "pill pill-emerald",
    rose: "pill pill-rose",
  }[tone] || "pill";
  return <span className={cls} data-testid={testid}>{children}</span>;
}

export function Stat({ label, value, tone = "cyan" }) {
  const color = {
    cyan: "text-accent-cyan",
    amber: "text-accent-amber",
    emerald: "text-accent-emerald",
    rose: "text-accent-rose",
  }[tone] || "text-white";
  return (
    <div className="flex flex-col p-3 border border-white/10 bg-bg-deep">
      <span className="section-overline">{label}</span>
      <span className={`font-mono text-lg ${color}`}>{value}</span>
    </div>
  );
}

export function AsciiLoader({ label = "computing" }) {
  return (
    <div className="font-mono text-xs text-neutral-400 flex items-center gap-2">
      <span className="ascii-loader"></span>
      <span>{label}<span className="caret">_</span></span>
    </div>
  );
}
