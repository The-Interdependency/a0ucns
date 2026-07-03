// === MODULE_BUILD ===
// id: fe_page_sentinels
//   module_name: SentinelsPage
//   module_kind: ui_page
//   summary: view the 13-sentinel canon + edit per-agent sentinel modes (observe/flag/off) and weights for a selected agent
//   owner: Erin Spencer
//   public_surface: SentinelsPage
//   internal_surface: CanonTable, ModeRow, useSentinelState
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_page_sentinels_boundaries
//   summary: page-level CRUD over sentinel modes/weights for one agent
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_sentinels
//   summary: page-level CRUD over sentinel modes/weights for one agent
//   exposes: SentinelsPage
//   boundaries: auth:none, storage:none, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import { SENTINEL_CANON, SENTINEL_MODE_OPTIONS, modeBadgeClass } from "../lib/sentinels";

export default function SentinelsPage() {
  const [agents, setAgents] = useState([]);
  const [agentId, setAgentId] = useState("");
  const [modes, setModes] = useState({});
  const [weights, setWeights] = useState({});
  const [busy, setBusy] = useState(false);
  const [savedAt, setSavedAt] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api.listInstances().then(r => {
      setAgents(r.agents || []);
      if (!agentId && r.agents?.length) setAgentId(r.agents[0].id);
    }).catch(e => setErr(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadAgent = useCallback(async (id) => {
    if (!id) return;
    setBusy(true); setErr(null);
    try {
      const [m, w] = await Promise.all([api.getSentinelModes(id), api.getSentinelWeights(id)]);
      setModes(m.modes || {}); setWeights(w.weights || {});
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message);
    } finally { setBusy(false); }
  }, []);

  useEffect(() => { loadAgent(agentId); }, [agentId, loadAgent]);

  async function persistMode(name, value) {
    setBusy(true); setErr(null);
    try {
      await api.patchSentinelModes(agentId, { user_id: "local", modes: { [name]: value } });
      setModes(m => ({ ...m, [name]: value }));
      setSavedAt(new Date().toLocaleTimeString());
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message);
    } finally { setBusy(false); }
  }

  async function persistWeight(name, value) {
    setBusy(true); setErr(null);
    try {
      await api.patchSentinelWeights(agentId, { user_id: "local", weights: { [name]: value } });
      setWeights(w => ({ ...w, [name]: value }));
      setSavedAt(new Date().toLocaleTimeString());
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message);
    } finally { setBusy(false); }
  }

  async function bulkSet(mode) {
    if (!agentId) return;
    setBusy(true); setErr(null);
    try {
      const r = await api.bulkSentinelModes(agentId, { user_id: "local", mode });
      setModes(r.modes || {});
      setSavedAt(new Date().toLocaleTimeString());
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message);
    } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6" data-testid="page-sentinels">
      <header className="space-y-2">
        <h1 className="text-3xl font-mono tracking-tight text-white">Sentinels</h1>
        <p className="text-xs text-neutral-400 font-mono">
          13 named cuts. Each one has a mode (observe/flag/off) and an evaluation weight.
          A <strong>flag</strong>-mode sentinel that fires halts the next turn and requires explicit override.
        </p>
      </header>

      <div className="flex flex-wrap items-end gap-3">
        <label className="text-[0.65rem] font-mono uppercase tracking-ultra text-neutral-400">
          <span className="block mb-1">agent</span>
          <select
            data-testid="sentinels-agent-select"
            value={agentId}
            onChange={e => setAgentId(e.target.value)}
            className="bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white min-w-[16rem]"
          >
            <option value="">— select agent —</option>
            {agents.map(a => <option key={a.id} value={a.id}>{a.sheet?.name || a.id.slice(0, 8)}</option>)}
          </select>
        </label>
        <div className="flex gap-1">
          {["observe", "flag", "off"].map(m => (
            <button key={m} data-testid={`bulk-mode-${m}`} disabled={!agentId || busy}
                    onClick={() => bulkSet(m)}
                    className={`px-2 py-1.5 border font-mono text-[0.6rem] uppercase tracking-wider disabled:opacity-40 ${modeBadgeClass(m)}`}>
              bulk → {m}
            </button>
          ))}
        </div>
        {savedAt && <span className="text-[0.6rem] font-mono text-emerald-300/70" data-testid="sentinels-saved-at">saved · {savedAt}</span>}
      </div>

      {err && (
        <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="sentinels-error">
          {String(err)}
        </div>
      )}

      <div className="border border-white/10 overflow-x-auto" data-testid="sentinels-table">
        <table className="w-full text-left">
          <thead className="bg-bg-surface text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">
            <tr>
              <th className="px-3 py-2 w-12">#</th>
              <th className="px-3 py-2">title</th>
              <th className="px-3 py-2">cut</th>
              <th className="px-3 py-2 w-20">cliff</th>
              <th className="px-3 py-2 w-32">mode</th>
              <th className="px-3 py-2 w-32">weight</th>
            </tr>
          </thead>
          <tbody>
            {SENTINEL_CANON.map(s => {
              const mode = modes[s.name] || "observe";
              const weight = weights[s.name] ?? (s.cliff ? 1.0 : 0.5);
              return (
                <tr key={s.name} className="border-t border-white/5" data-testid={`sentinel-row-${s.name}`}>
                  <td className="px-3 py-2 font-mono text-xs text-white">{s.name}</td>
                  <td className="px-3 py-2 font-mono text-xs text-neutral-200">{s.title}</td>
                  <td className="px-3 py-2 font-mono text-[0.65rem] text-neutral-400">{s.cut}</td>
                  <td className="px-3 py-2">
                    {s.cliff ? <span className="px-1.5 py-0.5 border border-rose-500/40 text-rose-300 text-[0.6rem] font-mono uppercase tracking-wider">cliff</span>
                             : <span className="text-[0.6rem] text-neutral-500 font-mono">slope</span>}
                  </td>
                  <td className="px-3 py-2">
                    <select
                      data-testid={`mode-select-${s.name}`}
                      value={mode}
                      onChange={e => persistMode(s.name, e.target.value)}
                      disabled={!agentId || busy}
                      className={`w-full bg-bg-surface border px-2 py-1 font-mono text-[0.65rem] text-white ${modeBadgeClass(mode)} disabled:opacity-40`}
                    >
                      {SENTINEL_MODE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.value}</option>)}
                    </select>
                  </td>
                  <td className="px-3 py-2">
                    <input
                      data-testid={`weight-input-${s.name}`}
                      type="number" step="0.01" min="0" max="1"
                      value={weight}
                      onChange={e => persistWeight(s.name, parseFloat(e.target.value))}
                      disabled={!agentId || busy}
                      className="w-full bg-bg-surface border border-white/10 px-2 py-1 font-mono text-[0.65rem] text-white disabled:opacity-40"
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
