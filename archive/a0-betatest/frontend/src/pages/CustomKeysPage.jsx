// === MODULE_BUILD ===
// id: fe_page_custom_keys
//   module_name: CustomKeysPage
//   module_kind: ui_page
//   summary: user-owned developer key vault — name + value (Fernet-encrypted at rest) + kind + label; supports rotation (PUT same name) and reveal (decrypt on demand); for GitHub PATs, GCP service accounts, AWS access keys, anything non-LLM
//   owner: Erin Spencer
//   public_surface: CustomKeysPage
//   internal_surface: Row, AddForm
//   auth_boundary: bearer
//   storage_boundary: write
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; custom keys vault unreachable from UI
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_page_custom_keys_boundaries
//   summary: CRUD over /api/custom-keys
//   auth_boundary: bearer
//   storage_boundary: write
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_custom_keys
//   summary: developer keys ui
//   exposes: CustomKeysPage
//   boundaries: auth:bearer, storage:write, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useCallback, useEffect, useState } from "react";
import { Plus, Eye, EyeSlash, Trash, ArrowsClockwise } from "@phosphor-icons/react";
import { customKeys } from "../lib/api";

const KINDS = ["github", "gcp", "aws", "azure", "huggingface", "stripe", "supabase", "vercel", "other"];

function Row({ k, onReveal, onDelete, revealed }) {
  return (
    <tr className="border-t border-white/5" data-testid={`custom-key-row-${k.name}`}>
      <td className="px-3 py-2 font-mono text-xs text-white">{k.name}</td>
      <td className="px-3 py-2 font-mono text-[0.65rem] text-neutral-400">{k.kind || "—"}</td>
      <td className="px-3 py-2 font-mono text-[0.65rem] text-neutral-400">{k.label || "—"}</td>
      <td className="px-3 py-2 font-mono text-[0.65rem] text-neutral-300 break-all">
        {revealed ? <span data-testid={`custom-key-revealed-${k.name}`}>{revealed}</span> : k.preview}
      </td>
      <td className="px-3 py-2 font-mono text-[0.65rem] text-neutral-500">{k.rotated_count}</td>
      <td className="px-3 py-2 text-right space-x-1">
        <button onClick={() => onReveal(k)} data-testid={`custom-key-reveal-${k.name}`}
                className="inline-flex items-center gap-1 px-2 py-1 border border-white/10 text-neutral-300 text-[0.6rem] font-mono uppercase tracking-wider hover:bg-bg-surface">
          {revealed ? <><EyeSlash size={12} /> hide</> : <><Eye size={12} /> reveal</>}
        </button>
        <button onClick={() => onDelete(k)} data-testid={`custom-key-delete-${k.name}`}
                className="inline-flex items-center gap-1 px-2 py-1 border border-rose-500/40 text-rose-300 text-[0.6rem] font-mono uppercase tracking-wider hover:bg-rose-500/10">
          <Trash size={12} />
        </button>
      </td>
    </tr>
  );
}

function AddForm({ onSubmit, busy }) {
  const [name, setName] = useState("");
  const [kind, setKind] = useState("github");
  const [label, setLabel] = useState("");
  const [value, setValue] = useState("");
  const [show, setShow] = useState(false);
  const ready = name && value && /^[a-zA-Z0-9_.:\-]+$/.test(name);
  return (
    <form
      data-testid="custom-key-add-form"
      onSubmit={e => { e.preventDefault(); if (!ready || busy) return; onSubmit({ name, kind, label: label || null, value }).then(() => { setName(""); setLabel(""); setValue(""); }); }}
      className="border border-white/10 bg-bg-panel p-4 space-y-3"
    >
      <div className="grid md:grid-cols-3 gap-3">
        <label className="block space-y-1">
          <span className="block text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">name (unique)</span>
          <input data-testid="custom-key-name-input" value={name} onChange={e => setName(e.target.value)}
                 className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
                 placeholder="github_pat_main" />
        </label>
        <label className="block space-y-1">
          <span className="block text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">kind</span>
          <select data-testid="custom-key-kind-select" value={kind} onChange={e => setKind(e.target.value)}
                  className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white">
            {KINDS.map(k => <option key={k} value={k}>{k}</option>)}
          </select>
        </label>
        <label className="block space-y-1">
          <span className="block text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">label (optional)</span>
          <input data-testid="custom-key-label-input" value={label} onChange={e => setLabel(e.target.value)}
                 className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
                 placeholder="my dev workspace" />
        </label>
      </div>
      <label className="block space-y-1">
        <span className="block text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">value (encrypted at rest)</span>
        <div className="relative">
          <input data-testid="custom-key-value-input" type={show ? "text" : "password"} value={value} onChange={e => setValue(e.target.value)}
                 className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 pr-9 font-mono text-xs text-white"
                 placeholder="ghp_..." />
          <button type="button" data-testid="custom-key-value-show" onClick={() => setShow(s => !s)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-white">
            {show ? <EyeSlash size={14} /> : <Eye size={14} />}
          </button>
        </div>
      </label>
      <div className="flex items-center justify-end">
        <button type="submit" disabled={!ready || busy} data-testid="custom-key-submit-btn"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10 disabled:opacity-40">
          <Plus size={14} /> add / rotate key
        </button>
      </div>
    </form>
  );
}

export default function CustomKeysPage() {
  const [keys, setKeys] = useState([]);
  const [revealed, setRevealed] = useState({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const load = useCallback(async () => {
    setBusy(true);
    try { const r = await customKeys.list(); setKeys(r.keys || []); setErr(null); }
    catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setBusy(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function add(body) {
    setBusy(true); setErr(null);
    try { await customKeys.upsert(body); await load(); }
    catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setBusy(false); }
  }

  async function reveal(k) {
    if (revealed[k.id]) {
      setRevealed(r => { const c = { ...r }; delete c[k.id]; return c; });
      return;
    }
    try { const r = await customKeys.reveal(k.id); setRevealed(prev => ({ ...prev, [k.id]: r.value })); }
    catch (e) { setErr(e?.response?.data?.detail || e.message); }
  }

  async function remove(k) {
    if (!window.confirm(`Delete key "${k.name}"?`)) return;
    setBusy(true);
    try { await customKeys.remove(k.id); await load(); }
    catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setBusy(false); }
  }

  return (
    <div className="space-y-6" data-testid="page-custom-keys">
      <header className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-mono tracking-tight text-white">Developer Keys</h1>
          <p className="text-xs text-neutral-400 mt-1 font-mono max-w-2xl">
            Per-user vault for any non-LLM secret — GitHub PATs, GCP service accounts, AWS access keys, anything.
            Encrypted at rest with the server-side Fernet key. Re-PUT the same <code className="text-accent-cyan">name</code> to rotate.
            Your LLM keys live in <code className="text-accent-cyan">Model Keys</code> instead.
          </p>
        </div>
        <button onClick={load} data-testid="custom-keys-refresh-btn"
                className="inline-flex items-center gap-1.5 px-3 py-2 border border-white/10 text-neutral-300 font-mono text-xs uppercase tracking-wider hover:bg-bg-surface">
          <ArrowsClockwise size={14} /> refresh
        </button>
      </header>

      {err && (
        <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="custom-keys-error">
          {String(err)}
        </div>
      )}

      <AddForm onSubmit={add} busy={busy} />

      <div className="border border-white/10 overflow-x-auto" data-testid="custom-keys-table">
        <table className="w-full text-left">
          <thead className="bg-bg-surface text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">
            <tr>
              <th className="px-3 py-2">name</th>
              <th className="px-3 py-2">kind</th>
              <th className="px-3 py-2">label</th>
              <th className="px-3 py-2">value</th>
              <th className="px-3 py-2">rotations</th>
              <th className="px-3 py-2 text-right">actions</th>
            </tr>
          </thead>
          <tbody>
            {keys.length === 0 && (
              <tr><td colSpan={6} className="px-3 py-6 text-neutral-500 text-xs font-mono" data-testid="custom-keys-empty">
                no developer keys yet — add one above.
              </td></tr>
            )}
            {keys.map(k => (
              <Row key={k.id} k={k} onReveal={reveal} onDelete={remove} revealed={revealed[k.id]} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
