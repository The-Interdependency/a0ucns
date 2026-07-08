// === MODULE_BUILD ===
// id: fe_page_agent_lab
//   module_name: AgentLabPage
//   module_kind: ui_page
//   summary: the Agent Creation Lab — compose ANY permutation of a0 agent-creation logic and run it. Loads the permutation catalogue (GET /api/agent-lab/permutations), lets the user pick the a0(<energy>)<auditor> mode from the 6-lattice with a live identity preview (POST /api/agent-lab/identity-preview), toggle the optional/plan-only stages (distill unlock, sentinel config, volatile sub-memory, and the cross-repo a0-canonical fork/absorb/converge), and compose a validated ordered plan (POST /api/agent-lab/plan) whose steps each show the real route/primitive they execute against — native stages badged executable, cross-repo stages badged plan-only. A "create" action actually mints the native agent (POST /api/instances) from the composed character sheet, and a sub-memory panel runs the real volatile MemoryCore spawn_sub/merge_sub primitive (POST /api/agent-lab/sub-memory). Surfaces the recompose-only / non-committable-checkpoint / no-theorem-transfer firewalls.
//   owner: Erin Spencer
//   public_surface: AgentLabPage
//   internal_surface: StageCard, PlanStep, KIND_TONE
//   auth_boundary: cookie
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: read
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; remove /agent-lab route + nav item
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_page_agent_lab_boundaries
//   summary: reads the permutation catalogue + plans recipes + previews identity + runs the volatile sub-memory demo; the create action drives the existing /api/instances route
//   auth_boundary: cookie
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: read
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_agent_lab
//   summary: agent-creation permutation composer + planner + native create + volatile sub-memory demo
//   exposes: AgentLabPage
//   boundaries: auth:cookie, storage:none, network:external, user_data:read
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useEffect, useMemo, useState } from "react";
import { Flask, GitFork, Play, Plus, Warning, CheckCircle, Lock, Cube } from "@phosphor-icons/react";
import { api } from "../lib/api";
import { Panel, Pill, Stat, AsciiLoader } from "../components/Panel";

// stage kind -> pill tone (only palette tones: cyan/amber/emerald/rose/default)
const KIND_TONE = { required: "cyan", optional: "emerald", derived: "amber",
  automatic: "default", plan_only: "rose" };
// Stages the user toggles; required/derived/automatic are always in the plan.
const TOGGLEABLE = new Set(["distill_unlock", "sentinel_config", "sub_memory", "cross_repo_merge"]);

// Mirror of the backend _NEEDS_BASE / _NEEDS_OUTER — which modes require a model.
function identityNeedsModel(mode, base, outer) {
  const needsBase = /<model>/.test(mode) && mode !== "a0(zfae)";
  const needsOuter = mode === "a0(<model>)<model>";
  return (needsBase && !(base || "").trim()) || (needsOuter && !(outer || "").trim());
}

function StageCard({ stage, checked, toggleable, onToggle }) {
  const tone = KIND_TONE[stage.kind] || "default";
  return (
    <div className={`border p-3 space-y-1.5 ${checked ? "border-white/25 bg-bg-surface" : "border-white/10"}`}
      data-testid={`al-stage-${stage.id}`}>
      <div className="flex items-center gap-2">
        {toggleable ? (
          <input type="checkbox" checked={checked} onChange={onToggle} data-testid={`al-toggle-${stage.id}`}
            className="accent-cyan-400" />
        ) : (
          <span className="w-3 h-3 rounded-full bg-white/20" title="always in the plan" />
        )}
        <span className="font-mono text-xs text-white flex-1">{stage.title}</span>
        <Pill tone={tone}>{stage.kind}</Pill>
        {stage.native ? <Pill tone="cyan">native</Pill> : <Pill tone="rose">cross-repo</Pill>}
      </div>
      <p className="font-mono text-[0.6rem] text-neutral-400 leading-snug">{stage.summary}</p>
      <div className="font-mono text-[0.55rem] text-neutral-600">→ {stage.executes_via || "not executable here (plan-only)"}</div>
      {(stage.firewalls || []).map((f, i) => (
        <div key={i} className="font-mono text-[0.55rem] text-amber-300/70 flex items-center gap-1">
          <Lock size={9} /> {f}
        </div>
      ))}
    </div>
  );
}

function PlanStep({ step, idx }) {
  return (
    <div className="flex items-start gap-3 border-b border-white/5 py-2" data-testid={`al-planstep-${step.id}`}>
      <span className="font-mono text-[0.65rem] text-neutral-600 w-5 text-right">{idx + 1}</span>
      <div className="flex-1 space-y-0.5">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-white">{step.title}</span>
          {step.executable_here
            ? <Pill tone="emerald">executable</Pill>
            : <Pill tone="rose">plan-only</Pill>}
        </div>
        <div className="font-mono text-[0.55rem] text-neutral-500">{step.executes_via || step.source}</div>
      </div>
    </div>
  );
}

export default function AgentLabPage() {
  const [cat, setCat] = useState(null);
  const [catErr, setCatErr] = useState(null);

  // identity
  const [mode, setMode] = useState("a0(zfae)");
  const [baseModel, setBaseModel] = useState("");
  const [outerModel, setOuterModel] = useState("");
  const [username, setUsername] = useState("");
  const [identity, setIdentity] = useState(null);

  // recipe stages
  const [stages, setStages] = useState(() => new Set(["distill_unlock"]));
  const [plan, setPlan] = useState(null);
  const [planning, setPlanning] = useState(false);

  // create
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState(null);
  const [createErr, setCreateErr] = useState(null);

  // sub-memory demo
  const [subId, setSubId] = useState("probe");
  const [subItems, setSubItems] = useState("first thought\nsecond thought");
  const [subOut, setSubOut] = useState(null);

  useEffect(() => {
    api.labPermutations().then(setCat).catch(e => setCatErr(e?.response?.data?.detail || e.message));
  }, []);

  // live identity preview
  useEffect(() => {
    const t = setTimeout(() => {
      api.labIdentity({ mode, base_model: baseModel || null, outer_model: outerModel || null, username: username || null })
        .then(setIdentity).catch(() => setIdentity(null));
    }, 200);
    return () => clearTimeout(t);
  }, [mode, baseModel, outerModel, username]);

  // Drop a stale plan when the identity inputs change, so the create button under
  // a rendered plan can never mint a different agent than the plan describes.
  useEffect(() => { setPlan(null); setCreated(null); }, [mode, baseModel, outerModel]);

  const modes = cat?.modes || ["a0(zfae)"];
  const catalogue = cat?.stages || [];

  const toggle = (id) => setStages(prev => {
    const n = new Set(prev);
    n.has(id) ? n.delete(id) : n.add(id);
    return n;
  });

  async function compose() {
    setPlanning(true); setPlan(null);
    try {
      const r = await api.labPlan({
        identity: { mode, base_model: baseModel || null, outer_model: outerModel || null, username: username || null },
        stages: Array.from(stages),
      });
      setPlan(r);
    } finally { setPlanning(false); }
  }

  async function createAgent() {
    if (!plan) return;
    const id = plan.identity;
    if (identityNeedsModel(id.mode, id.base_model, id.outer_model)) return;
    setCreating(true); setCreateErr(null); setCreated(null);
    try {
      // Build from the COMPOSED plan snapshot (not live inputs), so the created
      // agent always matches the plan shown above the button. Blank name lets
      // AgentStore.create compose the owner-namespaced name from the authenticated
      // owner (the typed username is only a preview hint; the raw canonical name
      // would bypass owner namespacing).
      const sheet = { name: "", mode: id.mode,
        base_model: id.base_model || null, outer_model: id.outer_model || null };
      const r = await api.createInstance({ user_id: "local", sheet });
      setCreated(r);
    } catch (e) {
      setCreateErr(e?.response?.data?.detail || e.message || String(e));
    } finally { setCreating(false); }
  }

  async function runSubMemory() {
    const items = subItems.split("\n").map(s => s.trim()).filter(Boolean);
    const r = await api.labSubMemory({ items_by_sub: { [subId || "probe"]: items } });
    setSubOut(r);
  }

  const needsBase = /<model>/.test(mode) && mode !== "a0(zfae)";
  const createIncomplete = plan
    ? identityNeedsModel(plan.identity.mode, plan.identity.base_model, plan.identity.outer_model)
    : false;

  return (
    <div className="space-y-5" data-testid="page-agent-lab">
      <header className="flex items-center gap-3">
        <Flask size={26} className="text-accent-cyan" />
        <div>
          <h1 className="text-lg font-mono text-white">Agent Creation Lab</h1>
          <p className="text-xs font-mono text-neutral-500">
            compose any permutation of the a0 agent-creation ladder — identity · create · distill · gate · mode · sentinels · sub-memory · checkpoint
          </p>
        </div>
      </header>

      {catErr && <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="al-cat-err">{String(catErr)}</div>}

      <div className="flex flex-wrap gap-2" data-testid="al-firewalls">
        <Pill tone="emerald">recompose-only</Pill>
        <Pill tone="cyan">per-instance checkpoint non-committable</Pill>
        <Pill tone="rose">cross-repo strategies = plan-only (no theorem transfer)</Pill>
      </div>

      {/* identity */}
      <Panel title="1 · identity & mode (a0(<energy>)<auditor>)" testid="al-identity">
        <div className="p-4 grid md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <label className="block space-y-1">
              <span className="section-overline">mode (6-lattice)</span>
              <select value={mode} onChange={e => setMode(e.target.value)} data-testid="al-mode"
                className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white">
                {modes.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </label>
            <label className="block space-y-1">
              <span className="section-overline">base model {needsBase && <span className="text-amber-300">· required</span>}</span>
              <input value={baseModel} onChange={e => setBaseModel(e.target.value)} placeholder="provider:model (e.g. openai:gpt-4o)"
                data-testid="al-base" className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
            </label>
            <div className="grid grid-cols-2 gap-2">
              <label className="block space-y-1">
                <span className="section-overline">outer model</span>
                <input value={outerModel} onChange={e => setOuterModel(e.target.value)} placeholder="critic/auditor"
                  data-testid="al-outer" className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
              </label>
              <label className="block space-y-1">
                <span className="section-overline">username</span>
                <input value={username} onChange={e => setUsername(e.target.value)} placeholder="owner namespace"
                  data-testid="al-username" className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
              </label>
            </div>
          </div>
          <div className="border border-white/10 p-4 flex flex-col justify-center gap-2" data-testid="al-identity-preview">
            <span className="section-overline">composed identity</span>
            <div className="font-mono text-lg text-accent-cyan break-all">{identity?.canonical || "—"}</div>
            <div className="font-mono text-xs text-neutral-400 break-all">{identity?.agent_name || "—"}</div>
            {(identity?.warnings || []).map((w, i) => (
              <div key={i} className="font-mono text-[0.6rem] text-amber-300 flex items-center gap-1"><Warning size={11} /> {w}</div>
            ))}
          </div>
        </div>
      </Panel>

      {/* stages */}
      <Panel title="2 · pick the permutation (stages)" testid="al-stages">
        <div className="p-4 grid md:grid-cols-2 gap-3">
          {catalogue.map(s => (
            <StageCard key={s.id} stage={s} toggleable={TOGGLEABLE.has(s.id)}
              checked={TOGGLEABLE.has(s.id) ? stages.has(s.id) : true}
              onToggle={() => toggle(s.id)} />
          ))}
        </div>
        <div className="px-4 pb-4">
          <button onClick={compose} disabled={planning} data-testid="al-compose-btn"
            className="px-4 py-2 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10 disabled:opacity-40 flex items-center gap-2">
            <Play size={14} /> {planning ? "composing…" : "compose plan"}
          </button>
        </div>
      </Panel>

      {/* plan */}
      {plan && (
        <Panel title={`3 · execution plan · ${plan.executable_steps}/${plan.step_count} executable here`} testid="al-plan">
          <div className="p-4 space-y-3">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Stat label="identity" value={plan.identity?.canonical} tone="cyan" />
              <Stat label="steps" value={plan.step_count} tone="cyan" />
              <Stat label="executable" value={plan.executable_steps} tone="emerald" />
              <Stat label="plan-only" value={(plan.plan_only_steps || []).length} tone="rose" />
            </div>
            {(plan.warnings || []).map((w, i) => (
              <div key={i} className="font-mono text-[0.6rem] text-amber-300 flex items-center gap-1"><Warning size={11} /> {w}</div>
            ))}
            <div className="border border-white/10">
              {plan.steps.map((s, i) => <PlanStep key={s.id} step={s} idx={i} />)}
            </div>
            <div className="flex items-center gap-3 pt-1">
              <button onClick={createAgent} disabled={creating || createIncomplete} data-testid="al-create-btn"
                className="px-4 py-2 border border-accent-emerald/40 text-accent-emerald font-mono text-xs uppercase tracking-wider hover:bg-accent-emerald/10 disabled:opacity-40 flex items-center gap-2">
                <Plus size={14} /> {creating ? "creating…" : "create this native agent"}
              </button>
              <span className="font-mono text-[0.55rem] text-neutral-600">
                {createIncomplete
                  ? "this mode needs a base/outer model before it can be created"
                  : "runs the native create stage (POST /api/instances) + seeds a fresh ZFAE weight bank"}
              </span>
            </div>
            {creating && <AsciiLoader label="minting instance + weight bank" />}
            {createErr && <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="al-create-err">{String(createErr)}</div>}
            {created && (
              <div className="border border-emerald-500/30 bg-emerald-500/5 p-3 font-mono text-[0.65rem] text-emerald-200 flex items-center gap-2" data-testid="al-created">
                <CheckCircle size={14} /> created {created.sheet?.name || "agent"} · id {created.id}
                {created.zfae_metrics?.zfae_training_step != null && <span className="text-neutral-500">· step {created.zfae_metrics.zfae_training_step}</span>}
              </div>
            )}
          </div>
        </Panel>
      )}

      {/* sub-memory demo */}
      <Panel title="volatile sub-memory (MemoryCore.spawn_sub → merge_sub)" testid="al-submem"
        right={<Cube size={16} className="text-neutral-500" />}>
        <div className="p-4 space-y-3">
          <p className="font-mono text-[0.6rem] text-neutral-500">
            The a0p-native volatile sub primitive — spawn a scratch cache, push items, merge them into the short-term ring. Ephemeral: no persistence, no PCNA fork.
          </p>
          <div className="grid grid-cols-3 gap-2">
            <label className="block space-y-1">
              <span className="section-overline">sub id</span>
              <input value={subId} onChange={e => setSubId(e.target.value)} data-testid="al-subid"
                className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
            </label>
            <label className="block space-y-1 col-span-2">
              <span className="section-overline">items (one per line)</span>
              <textarea rows={2} value={subItems} onChange={e => setSubItems(e.target.value)} data-testid="al-subitems"
                className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
            </label>
          </div>
          <button onClick={runSubMemory} data-testid="al-submem-btn"
            className="px-4 py-2 border border-violet-400/40 text-violet-300 font-mono text-xs uppercase tracking-wider hover:bg-violet-400/10 flex items-center gap-2">
            <GitFork size={14} /> spawn → merge_sub
          </button>
          {subOut && (
            <div className="border border-white/10 p-3 font-mono text-[0.65rem] text-neutral-300 space-y-1" data-testid="al-submem-out">
              <div>merged <span className="text-violet-300">{subId}</span>: [{(subOut.merged?.[subId] || []).join(", ")}]</div>
              <div>short-term ring: [{(subOut.snapshot?.st || []).join(", ")}]</div>
              <div className="text-amber-300/70">{subOut.firewall}</div>
            </div>
          )}
        </div>
      </Panel>
    </div>
  );
}
