// === MODULE_BUILD ===
// id: fe_page_training_room
//   module_name: TrainingRoom
//   module_kind: ui_page
//   summary: multi-teacher distillation room — pick an agent, select TWO OR MORE teacher models (from the live inventory or custom ids), enter a batch of prompts (one per line), and run POST /api/instances/{id}/train so the a0(zfae) echo learns one distill step per (prompt × model); renders a live metrics ribbon + per-step results table
//   owner: Erin Spencer
//   public_surface: TrainingRoom
//   internal_surface: ModelChips
//   auth_boundary: cookie
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; remove /training route + nav item
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_page_training_room_boundaries
//   summary: drives multi-teacher distillation; reads inventory + instances; writes via /train
//   auth_boundary: cookie
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_training_room
//   summary: multi-teacher zfae distillation ui
//   exposes: TrainingRoom
//   boundaries: auth:cookie, storage:none, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { GraduationCap, Play, Plus, X, CheckCircle, XCircle } from "@phosphor-icons/react";
import { api } from "../lib/api";
import { Panel, Pill, Stat, AsciiLoader } from "../components/Panel";

function ModelChips({ inventory, loading, selected, onToggle, onAddCustom, onRemove }) {
  const [custom, setCustom] = useState("");
  const names = useMemo(
    () => Array.from(new Set((inventory || []).map(m => `${m.provider}:${m.id}`))),
    [inventory],
  );
  const customSelected = selected.filter(s => !names.includes(s));
  const add = () => { const v = custom.trim(); if (v) onAddCustom(v); setCustom(""); };
  return (
    <div className="space-y-2" data-testid="tr-models">
      <div className="flex flex-wrap gap-1.5">
        {names.map(n => (
          <button key={n} type="button" data-testid={`tr-model-${n}`}
            onClick={() => onToggle(n)}
            className={`px-2 py-1 border font-mono text-[0.65rem] flex items-center gap-1 transition-colors ${
              selected.includes(n) ? "border-violet-400/60 text-violet-200 bg-violet-400/10" : "border-white/10 text-neutral-400 hover:border-white/30"
            }`}>
            {n}{!selected.includes(n) && <Plus size={10} className="opacity-50" />}
          </button>
        ))}
        {names.length === 0 && loading && (
          <span className="text-[0.6rem] font-mono text-neutral-600">loading models…</span>
        )}
        {names.length === 0 && !loading && (
          <span className="text-[0.6rem] font-mono text-neutral-600">
            no models in inventory — type a model id below, or{" "}
            <Link to="/keys" className="text-accent-cyan underline" data-testid="tr-add-key-link">add a BYOK key</Link>
          </span>
        )}
      </div>
      {customSelected.length > 0 && (
        <div className="flex flex-wrap gap-1.5" data-testid="tr-models-custom">
          {customSelected.map(n => (
            <button key={n} type="button" data-testid={`tr-model-custom-${n}`} onClick={() => onRemove(n)}
              className="px-2 py-1 border border-violet-400/60 text-violet-200 bg-violet-400/10 font-mono text-[0.65rem] flex items-center gap-1">
              {n}<X size={10} />
            </button>
          ))}
        </div>
      )}
      <div className="flex items-center gap-2">
        <input data-testid="tr-model-custom-input" value={custom} onChange={e => setCustom(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); add(); } }}
          placeholder="provider:model (e.g. openai:gpt-4o)"
          className="flex-1 bg-bg-surface border border-white/10 px-2 py-1 font-mono text-[0.65rem] text-white" />
        <button type="button" data-testid="tr-model-custom-add" onClick={add}
          className="px-2 py-1 border border-white/10 font-mono text-[0.6rem] uppercase tracking-wider text-neutral-300 hover:bg-bg-surface">add</button>
      </div>
    </div>
  );
}

export default function TrainingRoom() {
  const [agents, setAgents] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [invLoaded, setInvLoaded] = useState(false);
  const [agentId, setAgentId] = useState("");
  const [models, setModels] = useState([]);
  const [prompts, setPrompts] = useState("Explain entropy in one sentence.\nWhat is the capital of France?");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api.listInstances().then(r => setAgents(r.agents || [])).catch(() => setAgents([]));
    api.inventory()
      .then(r => setInventory(r.models || []))
      .catch(() => setInventory([]))
      .finally(() => setInvLoaded(true));
  }, []);

  const promptList = prompts.split("\n").map(p => p.trim()).filter(Boolean);
  const ready = agentId && models.length >= 2 && promptList.length >= 1 && !running;

  const toggle = (n) => setModels(prev => prev.includes(n) ? prev.filter(x => x !== n) : [...prev, n]);
  const addCustom = (n) => setModels(prev => prev.includes(n) ? prev : [...prev, n]);

  async function run() {
    if (!ready) return;
    setRunning(true); setErr(null); setResult(null);
    try {
      const r = await api.trainInstance(agentId, { prompts: promptList, teacher_model_ids: models });
      setResult(r);
      // refresh agent metrics in the dropdown
      api.listInstances().then(x => setAgents(x.agents || [])).catch(() => {});
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message || String(e));
    } finally {
      setRunning(false);
    }
  }

  const okSteps = result?.steps?.filter(s => s.ok) || [];
  const lastSeeds = okSteps.length ? okSteps[okSteps.length - 1].total_seeds_touched : null;

  return (
    <div className="space-y-5" data-testid="page-training">
      <header className="flex items-center gap-3">
        <GraduationCap size={26} className="text-accent-cyan" />
        <div>
          <h1 className="text-lg font-mono text-white">Training Room</h1>
          <p className="text-xs font-mono text-neutral-500">distill the a0(zfae) echo from two or more teacher models</p>
        </div>
      </header>

      {err && (
        <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="tr-error">{String(err)}</div>
      )}

      <Panel title="configuration" testid="tr-config">
        <div className="p-4 space-y-4">
          <label className="block space-y-1">
            <span className="section-overline">agent (echo)</span>
            <select data-testid="tr-agent-select" value={agentId} onChange={e => setAgentId(e.target.value)}
              className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white">
              <option value="">— select an agent —</option>
              {agents.map(a => (
                <option key={a.id} value={a.id}>
                  {a.sheet.name} · step {a.zfae_metrics?.zfae_training_step ?? 0}
                </option>
              ))}
            </select>
          </label>

          <label className="block space-y-1">
            <span className="section-overline">teacher models (pick two or more)</span>
            <ModelChips inventory={inventory} loading={!invLoaded} selected={models} onToggle={toggle} onAddCustom={addCustom} onRemove={toggle} />
            {models.length < 2 && (
              <span className="text-[0.6rem] font-mono text-amber-300/80" data-testid="tr-models-hint">select at least two teacher models</span>
            )}
          </label>

          <label className="block space-y-1">
            <span className="section-overline">prompts (one per line)</span>
            <textarea data-testid="tr-prompts-textarea" rows={5} value={prompts} onChange={e => setPrompts(e.target.value)}
              className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
            <span className="text-[0.6rem] font-mono text-neutral-600">
              {promptList.length} prompt(s) × {models.length} model(s) = {promptList.length * models.length} distill step(s)
            </span>
          </label>

          <button data-testid="tr-run-btn" disabled={!ready} onClick={run}
            className="px-4 py-2 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10 disabled:opacity-40 flex items-center gap-2">
            <Play size={14} /> {running ? "training…" : "run training"}
          </button>
          {running && <AsciiLoader label="querying teachers + distilling" />}
        </div>
      </Panel>

      {result && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="tr-metrics">
            <Stat label="training step" value={result.metrics?.zfae_training_step ?? "—"} tone="cyan" />
            <Stat label="last loss" value={result.metrics?.zfae_last_loss != null ? Number(result.metrics.zfae_last_loss).toFixed(4) : "—"} tone="amber" />
            <Stat label="seeds touched" value={lastSeeds ?? "—"} tone="emerald" />
            <Stat label="teachers used" value={(result.teachers_used || []).length} tone="cyan" />
          </div>

          <Panel title={`distillation steps · ${result.ok_steps}/${result.steps?.length || 0} ok`} testid="tr-results">
            <div className="overflow-x-auto">
              <table className="w-full text-xs font-mono" data-testid="tr-results-table">
                <thead>
                  <tr className="border-b border-white/10 text-neutral-500">
                    <th className="text-left p-2">prompt</th>
                    <th className="text-left p-2">teacher</th>
                    <th className="text-left p-2">intent</th>
                    <th className="text-left p-2">core</th>
                    <th className="text-left p-2">loss</th>
                    <th className="text-left p-2">step</th>
                    <th className="text-left p-2">status</th>
                  </tr>
                </thead>
                <tbody>
                  {result.steps.map((s, i) => (
                    <tr key={i} className="border-b border-white/5 hover:bg-bg-surface" data-testid={`tr-step-${i}`}>
                      <td className="p-2 text-neutral-300 max-w-[18rem] truncate" title={s.prompt}>{s.prompt}</td>
                      <td className="p-2 text-white">{s.teacher_model_id}</td>
                      <td className="p-2">
                        {s.ok ? (s.intent_match
                          ? <CheckCircle size={14} className="text-accent-emerald" />
                          : <XCircle size={14} className="text-accent-amber" />) : "—"}
                      </td>
                      <td className="p-2 text-neutral-400">{s.ok ? s.core : "—"}</td>
                      <td className="p-2 text-neutral-400">{s.ok ? Number(s.loss).toFixed(4) : "—"}</td>
                      <td className="p-2 text-neutral-400">{s.ok ? s.training_step : "—"}</td>
                      <td className="p-2">
                        {s.ok
                          ? <Pill tone="emerald">ok</Pill>
                          : <span className="text-rose-300" title={s.error}>{(s.error || "error").slice(0, 40)}</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}
