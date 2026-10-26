// === MODULE_BUILD ===
// id: fe_page_inventory
//   module_name: InventoryPage
//   module_kind: ui_page
//   summary: discovered model inventory across providers (openai, anthropic, gemini, xai) — populated from /api/models/inventory; each row has a "create agent" action that instantiates a teacher-assisted a0(zfae) agent bound to that model and opens it in the workspace
//   owner: Erin Spencer
//   public_surface: InventoryPage
//   internal_surface: createAgentFor
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
// id: fe_page_inventory_boundaries
//   summary: inventory viewer + per-model "create agent" action
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_inventory
//   summary: model inventory ui + agent instantiation
//   exposes: InventoryPage
//   boundaries: auth:none, storage:none, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===


import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../lib/api";
import { Panel, Pill, AsciiLoader } from "../components/Panel";
import { ArrowsClockwise, Robot, KeyReturn } from "@phosphor-icons/react";

export default function InventoryPage() {
  const [data, setData] = useState({ models: [], errors: {}, count: 0 });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [creatingId, setCreatingId] = useState(null);
  const [err, setErr] = useState(null);
  const navigate = useNavigate();

  async function load() {
    setLoading(true);
    const r = await api.inventory();
    setData(r);
    setLoading(false);
  }
  useEffect(() => { load(); }, []);

  async function createAgentFor(m) {
    const modelId = `${m.provider}:${m.id}`;
    setCreatingId(modelId); setErr(null);
    try {
      const agent = await api.createInstance({
        sheet: {
          name: "",                  // blank → backend composes <user>(a0(zfae)<model>)
          mode: "a0(zfae)<model>",   // teacher-assisted: this model teaches the a0(zfae) core
          base_model: modelId,
        },
      });
      navigate(`/workspace?agent=${agent.id}`);
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message || String(e));
    } finally {
      setCreatingId(null);
    }
  }

  const filtered = useMemo(() => {
    let xs = data.models || [];
    if (filter !== "all") xs = xs.filter(m => m.provider === filter || m.via === filter);
    if (search) {
      const s = search.toLowerCase();
      xs = xs.filter(m => (m.id || "").toLowerCase().includes(s) || (m.label || "").toLowerCase().includes(s));
    }
    return xs;
  }, [data.models, filter, search]);

  const tabs = ["all", "emergent", "openai", "anthropic", "gemini", "xai"];

  return (
    <div className="space-y-6" data-testid="page-inventory">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-2xl tracking-tighter">Model Inventory</h1>
          <p className="text-neutral-400 text-sm mt-1 max-w-2xl">
            Live model catalog for each provider key you've registered, plus the Emergent universal namespace.
            Counts, context windows, modality, and cache support shown when the provider exposes them.
          </p>
        </div>
        <button className="btn-ghost" onClick={load} data-testid="inv-refresh">
          <ArrowsClockwise size={14} /> refresh
        </button>
      </header>

      {err && (
        <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="inv-error">{String(err)}</div>
      )}

      <Panel title={`catalog · ${data.count} models`}>
        <div className="flex flex-wrap gap-2 p-4 border-b border-white/10">
          {tabs.map(t => (
            <button
              key={t}
              className={"btn-ghost " + (filter === t ? "active" : "")}
              onClick={() => setFilter(t)}
              data-testid={`inv-tab-${t}`}
            >{t}</button>
          ))}
          <input
            className="input-term flex-1 min-w-[160px]"
            placeholder="search models (id, label)…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            data-testid="inv-search"
          />
        </div>

        {(data.models?.length ?? 0) === 0 && !loading && (
          <div className="p-6 text-xs text-neutral-400 font-sans space-y-3" data-testid="inv-empty-cta">
            <p>No models in the inventory yet. This build is BYOK — add an OpenAI / Anthropic / Google / xAI key and live models will appear here instantly.</p>
            <Link to="/keys" data-testid="inv-add-key-btn"
              className="inline-flex items-center gap-2 px-3 py-1.5 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10">
              <KeyReturn size={14} /> add a model key
            </Link>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono">
            <thead className="bg-bg-deep border-b border-white/10 text-neutral-500">
              <tr>
                <th className="text-left p-3">id</th>
                <th className="text-left p-3">label</th>
                <th className="text-left p-3">provider</th>
                <th className="text-left p-3">context</th>
                <th className="text-left p-3">modality</th>
                <th className="text-left p-3">action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((m, i) => (
                <tr key={(m.provider || "?") + ":" + (m.id || i)} className="border-b border-white/5 hover:bg-bg-surface">
                  <td className="p-3 text-white">{`${m.provider}:${m.id}`}</td>
                  <td className="p-3 text-neutral-300">{m.label || m.id}</td>
                  <td className="p-3">
                    <Pill tone="cyan">{m.provider}</Pill>
                  </td>
                  <td className="p-3 text-neutral-400">{m.context_window || "—"}</td>
                  <td className="p-3 text-neutral-400">{m.modality || "text"}</td>
                  <td className="p-3">
                    <button
                      className="btn-ghost"
                      data-testid={`inv-create-agent-${m.provider}-${m.id}`}
                      disabled={creatingId === `${m.provider}:${m.id}`}
                      onClick={() => createAgentFor(m)}
                      title={`Create a teacher-assisted a0(zfae) agent using ${m.provider}:${m.id}`}
                    >
                      <Robot size={13} /> {creatingId === `${m.provider}:${m.id}` ? "creating…" : "create agent"}
                    </button>
                  </td>
                </tr>
              ))}
              {!filtered.length && !loading && (
                <tr><td colSpan={6} className="p-6 text-center text-neutral-500">No models match the current filter.</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {Object.keys(data.errors || {}).length > 0 && (
          <div className="p-4 border-t border-white/10 text-[0.7rem] text-accent-rose font-mono">
            {Object.entries(data.errors).map(([k, v]) => (
              <div key={k}>· {k}: {String(v)}</div>
            ))}
          </div>
        )}
      </Panel>

      {loading && <AsciiLoader label="fetching inventory" />}
    </div>
  );
}
