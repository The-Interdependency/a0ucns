// === MODULE_BUILD ===
// id: fe_page_drafts
//   module_name: DraftsPage
//   module_kind: ui_page
//   summary: local prompt drafts — list / create / edit / delete; persists via /api/drafts
//   owner: Erin Spencer
//   public_surface: DraftsPage
//   internal_surface: none
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
// id: fe_page_drafts_boundaries
//   summary: CRUD over /api/drafts
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_drafts
//   summary: drafts CRUD ui
//   exposes: DraftsPage
//   boundaries: auth:none, storage:none, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===


import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Panel, Pill, AsciiLoader } from "../components/Panel";
import { Trash, FloppyDisk } from "@phosphor-icons/react";

export default function DraftsPage() {
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);

  async function load() {
    setLoading(true);
    const r = await api.listDrafts();
    setDrafts(r.drafts || []);
    setLoading(false);
  }
  useEffect(() => { load(); }, []);

  async function save(d) {
    await api.updateDraft(d.id, {
      user_id: "local",
      title: d.title || "",
      content: d.content || "",
      tags: d.tags || [],
    });
    setEditing(null);
    await load();
  }

  async function remove(id) {
    if (!window.confirm("delete draft?")) return;
    await api.deleteDraft(id); await load();
  }

  return (
    <div className="space-y-6" data-testid="page-drafts">
      <header>
        <h1 className="font-mono text-2xl tracking-tighter">Prompt Drafts</h1>
        <p className="text-neutral-400 text-sm mt-1 max-w-2xl">
          Every prompt in the Workspace is autosaved here while you write. Edit, tag, or carry them across sessions.
        </p>
      </header>

      <Panel title={`drafts · ${drafts.length}`}>
        <ul className="divide-y divide-white/5">
          {drafts.map(d => (
            <li key={d.id} className="p-4 space-y-2" data-testid={`draft-${d.id}`}>
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Pill tone="cyan">{(d.title || "untitled").slice(0, 60)}</Pill>
                  {(d.tags || []).map(t => <Pill key={t}>{t}</Pill>)}
                </div>
                <div className="flex items-center gap-1">
                  <button className="btn-ghost" onClick={() => setEditing(editing?.id === d.id ? null : { ...d })}
                    data-testid={`draft-edit-${d.id}`}>{editing?.id === d.id ? "close" : "edit"}</button>
                  <button className="btn-danger" onClick={() => remove(d.id)} data-testid={`draft-del-${d.id}`}>
                    <Trash size={14}/>
                  </button>
                </div>
              </div>
              {editing?.id === d.id ? (
                <div className="space-y-2">
                  <input className="input-term" value={editing.title || ""}
                    onChange={e => setEditing({ ...editing, title: e.target.value })}
                    data-testid={`draft-title-${d.id}`}/>
                  <textarea className="input-term min-h-[120px] resize-y" value={editing.content}
                    onChange={e => setEditing({ ...editing, content: e.target.value })}
                    data-testid={`draft-content-${d.id}`}/>
                  <button className="btn-primary" onClick={() => save(editing)} data-testid={`draft-save-${d.id}`}>
                    <FloppyDisk size={14}/> save
                  </button>
                </div>
              ) : (
                <pre className="text-xs text-neutral-300 whitespace-pre-wrap font-mono bg-bg-deep border border-white/5 p-3">{(d.content || "").slice(0, 280)}{(d.content || "").length > 280 ? "…" : ""}</pre>
              )}
              <div className="text-[0.65rem] text-neutral-500 font-mono">updated {d.updated_at?.slice(0, 16)?.replace("T"," ")}</div>
            </li>
          ))}
          {!drafts.length && !loading && (
            <li className="p-6 text-center text-xs text-neutral-500 font-mono">No drafts yet — start typing in Workspace.</li>
          )}
        </ul>
      </Panel>
      {loading && <AsciiLoader label="loading drafts"/>}
    </div>
  );
}
