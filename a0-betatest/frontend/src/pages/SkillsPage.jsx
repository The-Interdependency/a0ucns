// === MODULE_BUILD ===
// id: fe_page_skills
//   module_name: SkillsPage
//   module_kind: ui_page
//   summary: skill catalog browser + authoring form with live overlap warning before save (jaccard ≥0.6 over scope ∪ logic tokens against existing user+global skills); admin-style sync button pulls global skills from The-Interdependency/skill-lib
//   owner: Erin Spencer
//   public_surface: SkillsPage
//   internal_surface: SkillCard, ComposeForm, OverlapList
//   auth_boundary: bearer
//   storage_boundary: write
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_page_skills_boundaries
//   summary: skill CRUD ui with overlap detection
//   auth_boundary: bearer
//   storage_boundary: write
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_skills
//   summary: skills ui
//   exposes: SkillsPage
//   boundaries: auth:bearer, storage:write, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useEffect, useState } from "react";
import { Plus, Trash, ArrowsClockwise, WarningCircle, CheckCircle, BookOpen } from "@phosphor-icons/react";
import { skillsApi } from "../lib/api_tools";

function SkillCard({ s, onDelete, mine }) {
  return (
    <div className="border border-white/10 bg-bg-panel p-3 space-y-1" data-testid={`skill-card-${s.id}`}>
      <div className="flex items-center justify-between">
        <div className="font-mono text-sm text-white">{s.name}</div>
        <div className="flex items-center gap-2">
          <span className={`px-1.5 py-0.5 border text-[0.6rem] font-mono uppercase tracking-wider ${s.source === "skill-lib" ? "border-accent-cyan/40 text-accent-cyan" : "border-white/15 text-neutral-300"}`}>
            {s.source}
          </span>
          {mine && (
            <button onClick={() => onDelete(s)} data-testid={`skill-delete-${s.id}`}
                    className="text-rose-300 hover:text-rose-100"><Trash size={14} /></button>
          )}
        </div>
      </div>
      <div className="text-[0.7rem] font-mono text-neutral-400">{s.description}</div>
      <div className="flex flex-wrap gap-1 pt-1">
        {(s.scope_tokens || []).slice(0, 6).map(t => (
          <span key={"s-" + t} className="px-1.5 py-0.5 border border-emerald-500/30 text-emerald-300/80 text-[0.6rem] font-mono">{t}</span>
        ))}
        {(s.logic_set_tokens || []).slice(0, 6).map(t => (
          <span key={"l-" + t} className="px-1.5 py-0.5 border border-amber-400/30 text-amber-300/80 text-[0.6rem] font-mono">{t}</span>
        ))}
      </div>
      {s.tool_bindings?.length > 0 && (
        <div className="pt-1 text-[0.6rem] font-mono text-neutral-500">tools: {s.tool_bindings.join(", ")}</div>
      )}
    </div>
  );
}

function OverlapList({ items }) {
  if (!items || !items.length) return null;
  return (
    <div className="border border-amber-400/40 bg-amber-400/5 px-3 py-2" data-testid="overlap-list">
      <div className="flex items-center gap-1.5 text-amber-200 font-mono text-xs">
        <WarningCircle size={14} />
        existing skill{items.length > 1 ? "s" : ""} with overlapping logic+scope:
      </div>
      <ul className="mt-1 space-y-0.5 text-[0.7rem] font-mono">
        {items.map(m => (
          <li key={m.id} className="text-amber-100">
            <span className="text-amber-200">{m.score}</span> · <span className="text-white">{m.name}</span> ({m.source}) — {m.description}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ComposeForm({ onSaved }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [prompt, setPrompt] = useState("");
  const [tools, setTools] = useState("");
  const [matches, setMatches] = useState([]);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  async function checkNow() {
    if (!name && !description) return;
    setBusy(true);
    try {
      const r = await skillsApi.checkOverlap({ name, description });
      setMatches(r.matches || []);
    } catch (e) { setErr(e.message); }
    finally { setBusy(false); }
  }

  async function submit(e, force = false) {
    e?.preventDefault?.();
    setBusy(true); setErr(null);
    const r = await skillsApi.register({
      name, description, prompt_template: prompt,
      tool_bindings: tools.split(",").map(s => s.trim()).filter(Boolean),
      force,
    });
    setBusy(false);
    if (r.status === 200 || r.status === 201) {
      setName(""); setDescription(""); setPrompt(""); setTools(""); setMatches([]);
      onSaved?.();
    } else if (r.status === 409) {
      setMatches(r.data?.similar || []);
      setErr(r.data?.error || "overlap detected");
    } else {
      setErr(r.data?.detail || r.data?.error || "error");
    }
  }

  return (
    <form onSubmit={e => submit(e, false)} className="border border-white/10 bg-bg-panel p-4 space-y-3" data-testid="skill-compose-form">
      <div className="grid md:grid-cols-2 gap-3">
        <input data-testid="skill-name-input" value={name} onChange={e => { setName(e.target.value); }} placeholder="skill name" className="bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
        <input data-testid="skill-tools-input" value={tools} onChange={e => setTools(e.target.value)} placeholder="tool bindings (csv): web_search, living_spec_lookup" className="bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
      </div>
      <textarea data-testid="skill-desc-input" rows={2} value={description} onChange={e => setDescription(e.target.value)} placeholder="what does this skill do? (used for scope+logic tokens)" className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
      <textarea data-testid="skill-prompt-input" rows={4} value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="prompt template (use {{vars}} for substitution)" className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />

      <OverlapList items={matches} />
      {err && <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="skill-error">{String(err)}</div>}

      <div className="flex items-center justify-end gap-2">
        <button type="button" onClick={checkNow} data-testid="skill-check-overlap-btn" disabled={busy}
                className="px-3 py-1.5 border border-white/10 text-neutral-300 font-mono text-xs uppercase tracking-wider hover:bg-bg-surface disabled:opacity-40">
          check overlap
        </button>
        <button type="submit" data-testid="skill-submit-btn" disabled={busy || name.length < 2}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10 disabled:opacity-40">
          <Plus size={14} /> publish skill
        </button>
        {matches.length > 0 && (
          <button type="button" onClick={e => submit(e, true)} data-testid="skill-force-submit-btn" disabled={busy}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-amber-400/40 text-amber-200 font-mono text-xs uppercase tracking-wider hover:bg-amber-400/10 disabled:opacity-40">
            <CheckCircle size={14} /> publish anyway
          </button>
        )}
      </div>
    </form>
  );
}

export default function SkillsPage() {
  const [skills, setSkills] = useState([]);
  const [err, setErr] = useState(null);
  const [syncStatus, setSyncStatus] = useState(null);

  async function load() {
    try { setSkills((await skillsApi.list()).skills || []); setErr(null); }
    catch (e) { setErr(e?.response?.data?.detail || e.message); }
  }
  useEffect(() => { load(); }, []);

  async function sync() {
    setSyncStatus("…");
    try { const r = await skillsApi.sync(); setSyncStatus(JSON.stringify(r)); await load(); }
    catch (e) { setSyncStatus(`error: ${e.message}`); }
  }

  return (
    <div className="space-y-6" data-testid="page-skills">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-mono tracking-tight text-white">Skills</h1>
          <p className="text-xs text-neutral-400 mt-1 font-mono max-w-2xl">
            A skill is a named prompt template + tool bindings + sentinel-mode overrides.
            New skills are checked against the catalog by scope ∪ logic-set tokens — duplicates surface a warning.
          </p>
        </div>
        <button onClick={sync} data-testid="skills-sync-btn"
                className="inline-flex items-center gap-1.5 px-3 py-2 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10">
          <ArrowsClockwise size={14} /> sync from skill-lib
        </button>
      </header>

      {syncStatus && <div className="border border-white/10 bg-bg-surface px-3 py-2 font-mono text-[0.65rem] text-neutral-300 overflow-x-auto" data-testid="skills-sync-status">{syncStatus}</div>}
      {err && <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono">{String(err)}</div>}

      <ComposeForm onSaved={load} />

      <section className="space-y-2">
        <div className="flex items-center gap-2 text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-500">
          <BookOpen size={12} /> catalog · {skills.length}
        </div>
        {skills.length === 0 && (
          <div className="border border-white/10 px-3 py-4 text-neutral-500 text-xs font-mono" data-testid="skills-empty">
            no skills yet. publish one above, or click <strong>sync from skill-lib</strong> to pull canon.
          </div>
        )}
        <div className="grid md:grid-cols-2 gap-3" data-testid="skills-grid">
          {skills.map(s => (
            <SkillCard key={s.id} s={s} mine={!!s.owner_user_id}
                       onDelete={async ss => { if (window.confirm(`Delete skill ${ss.name}?`)) { await skillsApi.remove(ss.id); await load(); } }} />
          ))}
        </div>
      </section>
    </div>
  );
}
