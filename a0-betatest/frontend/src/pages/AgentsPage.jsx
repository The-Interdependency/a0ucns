// === MODULE_BUILD ===
// id: fe_page_agents
//   module_name: AgentsPage
//   module_kind: ui_page
//   summary: agent CRUD — list every instance with zfae metrics, create via CharacterSheetForm, edit existing sheet, archive/delete
//   owner: Erin Spencer
//   public_surface: AgentsPage
//   internal_surface: Row, useAgents
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; agent CRUD requires curl
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_page_agents_boundaries
//   summary: page-level CRUD over /api/instances
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_agents
//   summary: page-level CRUD over /api/instances
//   exposes: AgentsPage
//   boundaries: auth:none, storage:none, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Pencil, Trash, Archive, ArrowRight } from "@phosphor-icons/react";
import { api } from "../lib/api";
import CharacterSheetForm from "../components/CharacterSheetForm";
import { MODE_LABELS } from "../lib/sentinels";

function fmtInt(n) { return typeof n === "number" ? n.toLocaleString() : "—"; }

function Row({ a, onEdit, onDelete, onArchive }) {
  const m = a.zfae_metrics || {};
  return (
    <tr className="border-t border-white/5" data-testid={`agent-row-${a.id}`}>
      <td className="px-3 py-2 font-mono text-xs text-white">{a.sheet?.name || "—"}</td>
      <td className="px-3 py-2 font-mono text-[0.65rem] text-neutral-400">{MODE_LABELS[a.sheet?.mode] || a.sheet?.mode}</td>
      <td className="px-3 py-2 font-mono text-[0.65rem] text-neutral-300">{fmtInt(m.zfae_weight_count_total ?? m.zfae_weight_count)}</td>
      <td className="px-3 py-2 font-mono text-[0.65rem] text-neutral-300">{fmtInt(m.zfae_training_step)}</td>
      <td className="px-3 py-2 font-mono text-[0.65rem] text-neutral-300">
        {m.zfae_total_seeds_touched ?? 0} / 471
      </td>
      <td className="px-3 py-2 font-mono text-[0.65rem] text-neutral-500">
        {m.zfae_last_loss == null ? "—" : Number(m.zfae_last_loss).toFixed(4)}
      </td>
      <td className="px-3 py-2 font-mono text-[0.65rem] text-neutral-600 truncate max-w-[12rem]" title={m.zfae_checkpoint_digest}>
        {m.zfae_checkpoint_digest ? m.zfae_checkpoint_digest.slice(0, 12) + "…" : "—"}
      </td>
      <td className="px-3 py-2 text-right space-x-1">
        <Link to={`/?agent=${a.id}`}
              data-testid={`agent-row-open-${a.id}`}
              className="inline-flex items-center gap-1 px-2 py-1 border border-accent-cyan/40 text-accent-cyan text-[0.6rem] font-mono uppercase tracking-wider hover:bg-accent-cyan/10">
          chat <ArrowRight size={12} />
        </Link>
        <button onClick={() => onEdit(a)} data-testid={`agent-row-edit-${a.id}`}
                className="inline-flex items-center gap-1 px-2 py-1 border border-white/10 text-neutral-300 text-[0.6rem] font-mono uppercase tracking-wider hover:bg-bg-surface">
          <Pencil size={12} /> edit
        </button>
        <button onClick={() => onArchive(a)} data-testid={`agent-row-archive-${a.id}`}
                className="inline-flex items-center gap-1 px-2 py-1 border border-white/10 text-neutral-400 text-[0.6rem] font-mono uppercase tracking-wider hover:bg-bg-surface">
          <Archive size={12} />
        </button>
        <button onClick={() => onDelete(a)} data-testid={`agent-row-delete-${a.id}`}
                className="inline-flex items-center gap-1 px-2 py-1 border border-rose-500/40 text-rose-300 text-[0.6rem] font-mono uppercase tracking-wider hover:bg-rose-500/10">
          <Trash size={12} />
        </button>
      </td>
    </tr>
  );
}

export default function AgentsPage() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const load = useCallback(async () => {
    setLoading(true); setErr(null);
    try {
      const r = await api.listInstances();
      setAgents(r.agents || []);
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message || String(e));
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(sheet) {
    setBusy(true); setErr(null);
    try {
      await api.createInstance({ sheet });
      setCreating(false);
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message || String(e));
    } finally { setBusy(false); }
  }

  async function handleEdit(sheet) {
    if (!editing) return;
    setBusy(true); setErr(null);
    try {
      await api.patchInstance(editing.id, { sheet });
      setEditing(null);
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message || String(e));
    } finally { setBusy(false); }
  }

  async function handleDelete(a) {
    if (!window.confirm(`Delete agent ${a.sheet?.name || a.id}? This removes the safetensors checkpoint.`)) return;
    setBusy(true);
    try { await api.deleteInstance(a.id); await load(); }
    catch (e) { setErr(e?.response?.data?.detail || e.message || String(e)); }
    finally { setBusy(false); }
  }

  async function handleArchive(a) {
    setBusy(true);
    try { await api.archiveInstance(a.id, { user_id: "local", archived: !a.archived }); await load(); }
    catch (e) { setErr(e?.response?.data?.detail || e.message || String(e)); }
    finally { setBusy(false); }
  }

  return (
    <div className="space-y-6" data-testid="page-agents">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-mono tracking-tight text-white">Agents</h1>
          <p className="text-xs text-neutral-400 mt-1 font-mono">
            Each agent is a persistent character sheet + a 1,223,187-scalar three-core ZFAE weight bank.
          </p>
        </div>
        <button
          data-testid="agents-create-btn"
          onClick={() => setCreating(true)}
          className="inline-flex items-center gap-1.5 px-3 py-2 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10"
        >
          <Plus size={14} /> new agent
        </button>
      </header>

      {err && (
        <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="agents-error">
          {String(err)}
        </div>
      )}

      <div className="border border-white/10 overflow-x-auto" data-testid="agents-table">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-bg-surface text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">
              <th className="px-3 py-2">name</th>
              <th className="px-3 py-2">mode</th>
              <th className="px-3 py-2">scalars</th>
              <th className="px-3 py-2">steps</th>
              <th className="px-3 py-2">seeds</th>
              <th className="px-3 py-2">last loss</th>
              <th className="px-3 py-2">digest</th>
              <th className="px-3 py-2 text-right">actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && (<tr><td colSpan={8} className="px-3 py-4 text-neutral-500 text-xs font-mono">loading…</td></tr>)}
            {!loading && agents.length === 0 && (
              <tr><td colSpan={8} className="px-3 py-6 text-neutral-500 text-xs font-mono" data-testid="agents-empty">
                No agents yet. Click <strong>new agent</strong> to create one.
              </td></tr>
            )}
            {agents.map(a => (
              <Row key={a.id} a={a} onEdit={setEditing} onDelete={handleDelete} onArchive={handleArchive} />
            ))}
          </tbody>
        </table>
      </div>

      {(creating || editing) && (
        <div className="fixed inset-0 z-40 bg-black/70 flex items-start justify-center p-4 overflow-y-auto" data-testid="agent-form-modal">
          <div className="w-full max-w-3xl border border-white/10 bg-bg-panel p-5 my-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-mono text-lg text-white">{creating ? "Create agent" : `Edit ${editing.sheet?.name}`}</h2>
              <button data-testid="agent-form-close" onClick={() => { setCreating(false); setEditing(null); }}
                      className="text-neutral-500 hover:text-white font-mono text-xs">close</button>
            </div>
            <CharacterSheetForm
              initial={editing?.sheet}
              busy={busy}
              submitLabel={creating ? "Create agent" : "Save changes"}
              onSubmit={creating ? handleCreate : handleEdit}
              onCancel={() => { setCreating(false); setEditing(null); }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
