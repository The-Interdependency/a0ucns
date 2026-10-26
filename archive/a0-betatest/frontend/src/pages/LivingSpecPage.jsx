// === MODULE_BUILD ===
// id: fe_page_living_spec
//   module_name: LivingSpecPage
//   module_kind: ui_page
//   summary: renders every msdmd block parsed live from the repo — grouped by module_kind, searchable, expandable per module to show MODULE_BUILD / BOUNDARIES / CAPABILITIES / CONTRACTS / RATIOS in full
//   owner: Erin Spencer
//   public_surface: LivingSpecPage
//   internal_surface: ModuleCard, BlockTable
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: read
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; living spec view disappears
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_page_living_spec_boundaries
//   summary: read-only viewer for /api/spec/living
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: read
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_living_spec
//   summary: living spec viewer
//   exposes: LivingSpecPage
//   boundaries: auth:none, storage:none, network:external, user_data:read
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useEffect, useMemo, useState } from "react";
import { MagnifyingGlass, CaretDown, CaretRight, ArrowsClockwise } from "@phosphor-icons/react";
import { livingSpec } from "../lib/api";

const BLOCK_LABEL = {
  MODULE_BUILD: "module_build",
  BOUNDARIES: "boundaries",
  CAPABILITIES: "capabilities",
  CONTRACTS: "contracts",
  RATIOS: "ratios",
};

function BlockTable({ entries }) {
  if (!entries || entries.length === 0) return <div className="text-[0.6rem] font-mono text-neutral-600">— none —</div>;
  return (
    <div className="space-y-2">
      {entries.map((e, i) => (
        <div key={i} className="border border-white/5 bg-bg-surface px-2 py-1.5 text-[0.7rem] font-mono">
          {e.id && <div className="text-accent-cyan/80">{e.id}</div>}
          {Object.entries(e).filter(([k]) => k !== "id").map(([k, v]) => (
            <div key={k} className="grid grid-cols-[10rem_1fr] gap-2">
              <span className="text-neutral-500">{k}</span>
              <span className="text-neutral-300 break-words">{Array.isArray(v) ? v.join(", ") : String(v)}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function ModuleCard({ m, open, onToggle }) {
  return (
    <div className="border border-white/10 bg-bg-panel" data-testid={`spec-module-${m.id || m.path}`}>
      <button onClick={onToggle} className="w-full flex items-center gap-2 px-3 py-2 hover:bg-bg-surface text-left">
        {open ? <CaretDown size={14} /> : <CaretRight size={14} />}
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2 flex-wrap">
            <span className="font-mono text-sm text-white">{m.module_name || m.id || m.path}</span>
            <span className="text-[0.6rem] font-mono px-1.5 py-0.5 border border-accent-cyan/40 text-accent-cyan/80">{m.module_kind}</span>
            <span className="text-[0.6rem] font-mono text-neutral-600 truncate">{m.path}</span>
          </div>
          <div className="text-[0.7rem] font-mono text-neutral-400 mt-0.5 line-clamp-1">{m.summary}</div>
        </div>
      </button>
      {open && (
        <div className="border-t border-white/5 p-3 space-y-3 text-[0.7rem] font-mono">
          {Object.entries(BLOCK_LABEL).map(([key, label]) => (
            <div key={key}>
              <div className="text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-500 mb-1">{label}</div>
              <BlockTable entries={m.blocks?.[key]} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function LivingSpecPage() {
  const [spec, setSpec] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [q, setQ] = useState("");
  const [kind, setKind] = useState("");
  const [open, setOpen] = useState({});

  async function load() {
    setBusy(true);
    try { setSpec(await livingSpec.get()); setErr(null); }
    catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setBusy(false); }
  }
  useEffect(() => { load(); }, []);

  const modules = useMemo(() => {
    if (!spec?.modules) return [];
    const ql = q.toLowerCase().trim();
    return spec.modules.filter(m =>
      (!kind || m.module_kind === kind) &&
      (!ql ||
        (m.module_name || "").toLowerCase().includes(ql) ||
        (m.summary || "").toLowerCase().includes(ql) ||
        (m.path || "").toLowerCase().includes(ql) ||
        (m.id || "").toLowerCase().includes(ql))
    );
  }, [spec, q, kind]);

  const kinds = useMemo(() => Object.entries(spec?.by_kind || {}).sort(), [spec]);

  return (
    <div className="space-y-6" data-testid="page-living-spec">
      <header className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-mono tracking-tight text-white">Living Spec</h1>
          <p className="text-xs text-neutral-400 mt-1 font-mono">
            Every module's doc-as-code block, parsed live from the repo. Changes constant. Refinements welcome.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[0.65rem] font-mono text-neutral-500" data-testid="spec-count">
            {spec?.count ?? 0} modules
          </span>
          <button onClick={load} disabled={busy} data-testid="spec-refresh-btn"
                  className="inline-flex items-center gap-1.5 px-2 py-1.5 border border-white/10 text-neutral-300 font-mono text-[0.65rem] uppercase tracking-wider hover:bg-bg-surface disabled:opacity-40">
            <ArrowsClockwise size={12} /> refresh
          </button>
        </div>
      </header>

      <div className="flex flex-wrap items-center gap-3">
        <label className="relative flex-1 min-w-[16rem]">
          <MagnifyingGlass size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-neutral-500" />
          <input
            data-testid="spec-search-input"
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="search by name / summary / path / id…"
            className="w-full bg-bg-surface border border-white/10 pl-7 pr-2 py-1.5 font-mono text-xs text-white"
          />
        </label>
        <div className="flex items-center gap-1 flex-wrap" data-testid="spec-kind-filter">
          <button onClick={() => setKind("")} data-testid="spec-kind-all"
                  className={`px-1.5 py-1 border text-[0.6rem] font-mono uppercase tracking-wider ${kind === "" ? "border-accent-cyan text-accent-cyan" : "border-white/10 text-neutral-400 hover:bg-bg-surface"}`}>
            all
          </button>
          {kinds.map(([k, n]) => (
            <button key={k} onClick={() => setKind(k)} data-testid={`spec-kind-${k}`}
                    className={`px-1.5 py-1 border text-[0.6rem] font-mono uppercase tracking-wider ${kind === k ? "border-accent-cyan text-accent-cyan" : "border-white/10 text-neutral-400 hover:bg-bg-surface"}`}>
              {k} · {n}
            </button>
          ))}
        </div>
      </div>

      {err && (
        <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="spec-error">{String(err)}</div>
      )}

      <div className="space-y-2" data-testid="spec-module-list">
        {busy && !spec && <div className="text-neutral-500 text-xs font-mono">parsing repo…</div>}
        {modules.map(m => {
          const k = m.id || m.path;
          return (
            <ModuleCard key={k} m={m} open={!!open[k]} onToggle={() => setOpen(s => ({ ...s, [k]: !s[k] }))} />
          );
        })}
        {!busy && modules.length === 0 && (
          <div className="text-neutral-500 text-xs font-mono" data-testid="spec-empty">no modules match.</div>
        )}
      </div>
    </div>
  );
}
