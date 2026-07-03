// === MODULE_BUILD ===
// id: fe_component_character_sheet_form
//   module_name: CharacterSheetForm
//   module_kind: ui_component
//   summary: fully-editable character-sheet form for an Agent — name, mode (5-lattice), models, system_prompt, persona, live tools_allowed multi-select (fetched from /api/tools with a custom-name fallback), memory seeds (long/short term), teacher_context_template, tags, boundary declarations, native-readiness thresholds, gonal assignment; structural engine dicts (edcm/ring_n_override/heptagram_overrides/px_resolution) are intentionally NOT exposed (engine-owned); emits onSubmit(sheet)
//   owner: Erin Spencer
//   public_surface: CharacterSheetForm
//   internal_surface: Field, ChipToggle, useTools
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; agent creation requires raw POST
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_component_character_sheet_form_boundaries
//   summary: form ui; reads /api/tools to populate the tools allow-list; submit delegated via onSubmit prop
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_component_character_sheet_form
//   summary: fully-editable agent character sheet form
//   exposes: CharacterSheetForm
//   boundaries: auth:none, storage:none, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, X } from "@phosphor-icons/react";
import { MODE_OPTIONS, composeAgentName } from "../lib/sentinels";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";

const BOUNDARY_OPTIONS = {
  auth: ["none", "bearer", "admin"],
  storage: ["none", "read", "write"],
  network: ["none", "internal", "external"],
  user_data: ["none", "read", "write"],
  admin_only: ["false", "true"],
};

const Field = ({ label, hint, children, testid }) => (
  <label className="block space-y-1" data-testid={testid}>
    <span className="block text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">{label}</span>
    {children}
    {hint && <span className="block text-[0.6rem] font-mono text-neutral-600">{hint}</span>}
  </label>
);

const ChipToggle = ({ active, onClick, children, testid, removable, onRemove }) => (
  <button
    type="button"
    data-testid={testid}
    onClick={removable ? onRemove : onClick}
    className={`px-2 py-1 border font-mono text-[0.65rem] flex items-center gap-1 transition-colors ${
      active
        ? "border-violet-400/60 text-violet-200 bg-violet-400/10"
        : "border-white/10 text-neutral-400 hover:border-white/30"
    }`}
  >
    {children}
    {removable ? <X size={10} /> : (active ? null : <Plus size={10} className="opacity-50" />)}
  </button>
);

function useTools() {
  const [tools, setTools] = useState([]);
  const [err, setErr] = useState(false);
  useEffect(() => {
    let alive = true;
    api.listTools()
      .then(r => { if (alive) setTools(r.tools || []); })
      .catch(() => { if (alive) setErr(true); });
    return () => { alive = false; };
  }, []);
  return { tools, err };
}

const linesToList = (s) => (s || "").split("\n").map(x => x.trim()).filter(Boolean);
const listToLines = (l) => (l || []).join("\n");

function useInventory() {
  const [inv, setInv] = useState([]);
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    let alive = true;
    api.inventory()
      .then(r => { if (alive) setInv(r.models || []); })
      .catch(() => { if (alive) setInv([]); })
      .finally(() => { if (alive) setLoaded(true); });
    return () => { alive = false; };
  }, []);
  return { inv, loaded };
}

// Model picker: a dropdown of `provider:id` options from the live inventory,
// with a "+ custom…" escape hatch (and auto-custom when the inventory is empty,
// e.g. BYOK with no keys yet) so the field is always editable.
function ModelSelect({ value, onChange, inventory, inventoryLoaded, testid, placeholder }) {
  const opts = useMemo(
    () => Array.from(new Set((inventory || []).map(m => `${m.provider}:${m.id}`))),
    [inventory],
  );
  const [customMode, setCustomMode] = useState(false);
  useEffect(() => {
    if (value && opts.length && !opts.includes(value)) setCustomMode(true);
  }, [value, opts]);
  const showCustom = customMode || opts.length === 0;

  if (showCustom) {
    return (
      <div className="space-y-1">
        <div className="flex gap-2">
          <input
            data-testid={`${testid}-input`}
            value={value}
            onChange={e => onChange(e.target.value)}
            placeholder={placeholder}
            className="flex-1 bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
          />
          {opts.length > 0 && (
            <button type="button" data-testid={`${testid}-uselist`} onClick={() => setCustomMode(false)}
                    className="px-2 py-1 border border-white/10 font-mono text-[0.6rem] uppercase tracking-wider text-neutral-300 hover:bg-bg-surface">
              list
            </button>
          )}
        </div>
        {opts.length === 0 && inventoryLoaded && (
          <span className="block text-[0.6rem] font-mono text-neutral-600">
            inventory empty —{" "}
            <Link to="/keys" className="text-accent-cyan underline" data-testid={`${testid}-add-key-link`}>add a BYOK key</Link>{" "}
            to pick from a dropdown
          </span>
        )}
      </div>
    );
  }
  return (
    <select
      data-testid={`${testid}-select`}
      value={opts.includes(value) ? value : ""}
      onChange={e => {
        if (e.target.value === "__custom__") { setCustomMode(true); onChange(""); }
        else onChange(e.target.value);
      }}
      className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
    >
      <option value="">— select model —</option>
      {opts.map(o => <option key={o} value={o}>{o}</option>)}
      <option value="__custom__">+ custom…</option>
    </select>
  );
}

export default function CharacterSheetForm({ initial, onSubmit, onCancel, submitLabel = "Create agent", busy }) {
  const { user } = useAuth();
  const username = user?.username || "agent";
  const [name, setName] = useState(initial?.name ?? "");
  const [nameDirty, setNameDirty] = useState(Boolean(initial?.name));
  const [mode, setMode] = useState(initial?.mode ?? "a0(zfae)");
  const [baseModel, setBaseModel] = useState(initial?.base_model ?? "");
  const [outerModel, setOuterModel] = useState(initial?.outer_model ?? "");
  const [systemPrompt, setSystemPrompt] = useState(initial?.system_prompt ?? "");
  const [persona, setPersona] = useState(initial?.persona ?? "");
  const [selectedTools, setSelectedTools] = useState(initial?.tools_allowed ?? []);
  const [customTool, setCustomTool] = useState("");
  const [longTerm, setLongTerm] = useState(listToLines(initial?.memory_seed?.long_term));
  const [shortTerm, setShortTerm] = useState(listToLines(initial?.memory_seed?.short_term));
  const [teacherTemplate, setTeacherTemplate] = useState(initial?.teacher_context_template ?? "");
  const [tags, setTags] = useState((initial?.tags ?? []).join(", "));
  const [boundaries, setBoundaries] = useState({
    auth: "none", storage: "write", network: "external", user_data: "write", admin_only: "false",
    ...(initial?.boundaries || {}),
  });
  const [minSteps, setMinSteps] = useState(initial?.min_steps_for_native ?? 16);
  const [maxLoss, setMaxLoss] = useState(initial?.max_loss_for_native ?? 0.1);
  const [liftedPathTrace, setLiftedPathTrace] = useState(Boolean(initial?.lifted_path_trace));
  const [phi, setPhi] = useState(initial?.gonal_assignment?.phi ?? "default");
  const [psi, setPsi] = useState(initial?.gonal_assignment?.psi ?? "mirror");
  const [omega, setOmega] = useState(initial?.gonal_assignment?.omega ?? "private");
  const [privateSpecPath, setPrivateSpecPath] = useState(initial?.private_gonal_spec_path ?? "");

  const { tools: availableTools, err: toolsErr } = useTools();
  const { inv: inventory, loaded: invLoaded } = useInventory();

  // Canonical owner-namespaced name a0(<energy>)<auditor>. Prefills the name
  // field (editable free-text) until the user manually overrides it.
  const suggestedName = useMemo(
    () => composeAgentName(username, mode, baseModel, outerModel),
    [username, mode, baseModel, outerModel],
  );
  useEffect(() => {
    if (!nameDirty) setName(suggestedName);
  }, [suggestedName, nameDirty]);

  const needsBase = useMemo(() => /<model>/.test(mode), [mode]);
  const needsOuter = useMemo(() => /a0\(<model>\)<model>|a0\(zfae\)<model>/.test(mode), [mode]);
  const ready = name.trim().length >= 2 && (!needsBase || baseModel.trim().length > 0);

  const availableNames = availableTools.map(t => t.name);
  const customSelected = selectedTools.filter(t => !availableNames.includes(t));

  const toggleTool = (n) =>
    setSelectedTools(prev => prev.includes(n) ? prev.filter(x => x !== n) : [...prev, n]);
  const addCustomTool = () => {
    const v = customTool.trim();
    if (v && !selectedTools.includes(v)) setSelectedTools(prev => [...prev, v]);
    setCustomTool("");
  };
  const setBoundary = (k, v) => setBoundaries(prev => ({ ...prev, [k]: v }));

  return (
    <form
      data-testid="character-sheet-form"
      onSubmit={e => {
        e.preventDefault();
        if (!ready || busy) return;
        onSubmit?.({
          name: name.trim(),
          mode,
          base_model: baseModel.trim() || null,
          outer_model: outerModel.trim() || null,
          system_prompt: systemPrompt,
          persona: persona,
          tools_allowed: selectedTools,
          memory_seed: { long_term: linesToList(longTerm), short_term: linesToList(shortTerm) },
          teacher_context_template: teacherTemplate.trim() || null,
          tags: tags.split(",").map(s => s.trim()).filter(Boolean),
          boundaries,
          min_steps_for_native: Number(minSteps),
          max_loss_for_native: Number(maxLoss),
          lifted_path_trace: liftedPathTrace,
          gonal_assignment: { phi, psi, omega },
          private_gonal_spec_path: privateSpecPath.trim() || null,
        });
      }}
      className="space-y-4"
    >
      <div className="grid md:grid-cols-2 gap-4">
        <Field label="agent name" hint={`nomenclature: <user>(a0(<energy>)<auditor>) — auto: ${suggestedName}`} testid="csf-name">
          <div className="flex gap-2">
            <input
              data-testid="csf-name-input"
              value={name}
              onChange={e => { setName(e.target.value); setNameDirty(true); }}
              className="flex-1 bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-sm text-white"
              placeholder={suggestedName}
            />
            {nameDirty && name !== suggestedName && (
              <button type="button" data-testid="csf-name-auto"
                      onClick={() => { setName(suggestedName); setNameDirty(false); }}
                      className="px-2 py-1 border border-white/10 font-mono text-[0.6rem] uppercase tracking-wider text-neutral-300 hover:bg-bg-surface whitespace-nowrap">
                auto
              </button>
            )}
          </div>
        </Field>
        <Field label="lattice mode" hint="The 6-mode lattice — controls who teaches and who answers." testid="csf-mode">
          <select
            data-testid="csf-mode-select"
            value={mode}
            onChange={e => setMode(e.target.value)}
            className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
          >
            {MODE_OPTIONS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
          </select>
        </Field>

        {needsBase && (
          <Field label="base model (inner <model>)" hint="from your model inventory — add a BYOK key to populate, or type a custom id" testid="csf-base">
            <ModelSelect value={baseModel} onChange={setBaseModel} inventory={inventory} inventoryLoaded={invLoaded}
                         testid="csf-base" placeholder="openai:gpt-4o" />
          </Field>
        )}
        {needsOuter && (
          <Field label="outer model" hint="critic / second teacher" testid="csf-outer">
            <ModelSelect value={outerModel} onChange={setOuterModel} inventory={inventory} inventoryLoaded={invLoaded}
                         testid="csf-outer" placeholder="anthropic:claude-sonnet-4-5" />
          </Field>
        )}
      </div>

      <Field label="system prompt" testid="csf-system">
        <textarea
          data-testid="csf-system-textarea"
          value={systemPrompt}
          onChange={e => setSystemPrompt(e.target.value)}
          rows={3}
          className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
        />
      </Field>

      <Field label="persona" testid="csf-persona">
        <textarea
          data-testid="csf-persona-textarea"
          value={persona}
          onChange={e => setPersona(e.target.value)}
          rows={2}
          className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
        />
      </Field>

      {/* ── Tools allow-list (live, sentinel-gated when invoked) ── */}
      <Field
        label="tools allowed"
        hint="Tools this agent may invoke mid-thought (teacher loop) or natively. Sentinel-gated on every call."
        testid="csf-tools"
      >
        <div className="space-y-2" data-testid="csf-tools-picker">
          {toolsErr && (
            <div className="text-[0.6rem] font-mono text-amber-300/80" data-testid="csf-tools-error">
              couldn't load /api/tools — use the custom field below
            </div>
          )}
          <div className="flex flex-wrap gap-1.5">
            {availableTools.map(t => (
              <ChipToggle
                key={t.name}
                testid={`csf-tool-${t.name}`}
                active={selectedTools.includes(t.name)}
                onClick={() => toggleTool(t.name)}
              >
                <span title={t.description || t.name}>{t.name}</span>
                <span className="text-neutral-600">·{t.kind}</span>
              </ChipToggle>
            ))}
            {availableTools.length === 0 && !toolsErr && (
              <span className="text-[0.6rem] font-mono text-neutral-600">loading tools…</span>
            )}
          </div>
          {customSelected.length > 0 && (
            <div className="flex flex-wrap gap-1.5" data-testid="csf-tools-custom-selected">
              {customSelected.map(n => (
                <ChipToggle key={n} testid={`csf-tool-custom-${n}`} active removable
                            onRemove={() => toggleTool(n)}>
                  {n}
                </ChipToggle>
              ))}
            </div>
          )}
          <div className="flex items-center gap-2">
            <input
              data-testid="csf-tools-custom-input"
              value={customTool}
              onChange={e => setCustomTool(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); addCustomTool(); } }}
              placeholder="add custom tool name (e.g. an MCP / webhook tool)"
              className="flex-1 bg-bg-surface border border-white/10 px-2 py-1 font-mono text-[0.65rem] text-white"
            />
            <button type="button" data-testid="csf-tools-custom-add" onClick={addCustomTool}
                    className="px-2 py-1 border border-white/10 font-mono text-[0.6rem] uppercase tracking-wider text-neutral-300 hover:bg-bg-surface">
              add
            </button>
          </div>
        </div>
      </Field>

      {/* ── Memory seeds ── */}
      <div className="grid md:grid-cols-2 gap-4">
        <Field label="long-term memory seeds" hint="one per line — folded into MemL at creation" testid="csf-mem-long">
          <textarea
            data-testid="csf-mem-long-textarea"
            value={longTerm}
            onChange={e => setLongTerm(e.target.value)}
            rows={3}
            className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
          />
        </Field>
        <Field label="short-term memory seeds" hint="one per line — folded into MemS at creation" testid="csf-mem-short">
          <textarea
            data-testid="csf-mem-short-textarea"
            value={shortTerm}
            onChange={e => setShortTerm(e.target.value)}
            rows={3}
            className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
          />
        </Field>
      </div>

      <Field label="teacher context template" hint="free-form; jinja-style {{placeholders}} allowed. blank = default composition" testid="csf-teacher-template">
        <textarea
          data-testid="csf-teacher-template-textarea"
          value={teacherTemplate}
          onChange={e => setTeacherTemplate(e.target.value)}
          rows={2}
          className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
        />
      </Field>

      <Field label="tags (comma sep)" testid="csf-tags">
        <input
          data-testid="csf-tags-input"
          value={tags}
          onChange={e => setTags(e.target.value)}
          className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
          placeholder="research, math, scratch"
        />
      </Field>

      {/* ── Lifted-path traversal toggle ── */}
      <label
        className="flex items-center gap-2 border border-white/10 p-3 cursor-pointer"
        data-testid="csf-lifted-path-toggle"
      >
        <input
          type="checkbox"
          data-testid="csf-lifted-path-checkbox"
          checked={liftedPathTrace}
          onChange={e => setLiftedPathTrace(e.target.checked)}
          className="accent-accent"
        />
        <span className="text-[0.65rem] font-mono">
          <span className="block text-white">lifted-path traversal trace</span>
          <span className="block text-neutral-500">
            native replies also compute their lossless lifted path over the 157-gonal carrier
            (seam events + revolutions) — text unchanged; visible in the decode trace
          </span>
        </span>
      </label>

      {/* ── Boundary declarations ── */}
      <div className="border border-white/10 p-3 space-y-2" data-testid="csf-boundaries">
        <div className="text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">boundary declarations</div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {Object.keys(BOUNDARY_OPTIONS).map(k => (
            <label key={k} className="block text-[0.65rem] font-mono">
              <span className="block text-neutral-500 mb-1">{k}</span>
              <select
                data-testid={`csf-boundary-${k}`}
                value={boundaries[k] ?? BOUNDARY_OPTIONS[k][0]}
                onChange={e => setBoundary(k, e.target.value)}
                className="w-full bg-bg-surface border border-white/10 px-2 py-1 text-xs text-white"
              >
                {BOUNDARY_OPTIONS[k].map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </label>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Field label="min steps for native" testid="csf-minsteps">
          <input
            data-testid="csf-minsteps-input" type="number" min={1}
            value={minSteps} onChange={e => setMinSteps(e.target.value)}
            className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
          />
        </Field>
        <Field label="max loss for native" testid="csf-maxloss">
          <input
            data-testid="csf-maxloss-input" type="number" step="0.01" min={0} max={1}
            value={maxLoss} onChange={e => setMaxLoss(e.target.value)}
            className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
          />
        </Field>
      </div>

      <div className="border border-white/10 p-3 space-y-2">
        <div className="text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">three-core gonal binding</div>
        <div className="grid grid-cols-3 gap-3">
          {[
            { core: "Φ phi (default)", v: phi, set: setPhi, tid: "csf-gonal-phi" },
            { core: "Ψ psi (mirror)",  v: psi, set: setPsi, tid: "csf-gonal-psi" },
            { core: "Ω omega (private)", v: omega, set: setOmega, tid: "csf-gonal-omega" },
          ].map(({ core, v, set, tid }) => (
            <label key={core} className="block text-[0.7rem] font-mono">
              <span className="block text-neutral-500 mb-1">{core}</span>
              <select
                data-testid={tid}
                value={v} onChange={e => set(e.target.value)}
                className="w-full bg-bg-surface border border-white/10 px-2 py-1 text-xs text-white"
              >
                <option value="default">default</option>
                <option value="mirror">mirror</option>
                <option value="private">private</option>
              </select>
            </label>
          ))}
        </div>
        <Field label="private gonal spec path (optional)" testid="csf-private-spec">
          <input
            data-testid="csf-private-spec-input"
            value={privateSpecPath}
            onChange={e => setPrivateSpecPath(e.target.value)}
            className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
            placeholder="/app/storage/private_gonals/agent-x.yaml"
          />
        </Field>
      </div>

      <div className="flex items-center justify-end gap-2 pt-2">
        {onCancel && (
          <button type="button" onClick={onCancel} data-testid="csf-cancel-btn"
                  className="px-3 py-1.5 border border-white/10 font-mono text-xs uppercase tracking-wider text-neutral-300 hover:bg-bg-surface">
            cancel
          </button>
        )}
        <button type="submit" data-testid="csf-submit-btn" disabled={!ready || busy}
                className="px-3 py-1.5 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10 disabled:opacity-40">
          {busy ? "saving…" : submitLabel}
        </button>
      </div>
    </form>
  );
}
