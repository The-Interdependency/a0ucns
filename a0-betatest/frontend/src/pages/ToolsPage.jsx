// === MODULE_BUILD ===
// id: fe_page_tools
//   module_name: ToolsPage
//   module_kind: ui_page
//   summary: lists every native + user-webhook + MCP-relay tool the current user can invoke; allows registering new user-webhook tools and invoking any tool with arbitrary JSON params; surfaces sentinel halts as override prompts
//   owner: Erin Spencer
//   public_surface: ToolsPage
//   internal_surface: ToolRow, AddWebhookForm, InvokeModal
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
// id: fe_page_tools_boundaries
//   summary: tools CRUD + invocation ui
//   auth_boundary: bearer
//   storage_boundary: write
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_tools
//   summary: tools ui
//   exposes: ToolsPage
//   boundaries: auth:bearer, storage:write, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useEffect, useState } from "react";
import { Plus, Play, Trash, ArrowsClockwise, ShieldWarning } from "@phosphor-icons/react";
import { toolsApi } from "../lib/api_tools";

function ToolRow({ t, onInvoke, onDelete }) {
  const isUser = !!t.owner_user_id;
  return (
    <tr className="border-t border-white/5" data-testid={`tool-row-${t.name}`}>
      <td className="px-3 py-2 font-mono text-xs text-white">{t.name}</td>
      <td className="px-3 py-2 font-mono text-[0.6rem] text-neutral-400 uppercase tracking-wider">{t.kind}</td>
      <td className="px-3 py-2 font-mono text-[0.65rem] text-neutral-400 max-w-md truncate" title={t.description}>{t.description}</td>
      <td className="px-3 py-2 font-mono text-[0.6rem] text-accent-cyan/70">{t.source}</td>
      <td className="px-3 py-2 text-right space-x-1">
        <button onClick={() => onInvoke(t)} data-testid={`tool-invoke-${t.name}`}
                className="inline-flex items-center gap-1 px-2 py-1 border border-accent-cyan/40 text-accent-cyan text-[0.6rem] font-mono uppercase tracking-wider hover:bg-accent-cyan/10">
          <Play size={12} /> invoke
        </button>
        {isUser && (
          <button onClick={() => onDelete(t)} data-testid={`tool-delete-${t.name}`}
                  className="inline-flex items-center gap-1 px-2 py-1 border border-rose-500/40 text-rose-300 text-[0.6rem] font-mono uppercase tracking-wider hover:bg-rose-500/10">
            <Trash size={12} />
          </button>
        )}
      </td>
    </tr>
  );
}

export default function ToolsPage() {
  const [tools, setTools] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [invokeTarget, setInvokeTarget] = useState(null);
  const [paramsJson, setParamsJson] = useState("{}");
  const [invokeResult, setInvokeResult] = useState(null);
  const [addOpen, setAddOpen] = useState(false);

  async function load() {
    setBusy(true);
    try { setTools((await toolsApi.list()).tools || []); setErr(null); }
    catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setBusy(false); }
  }
  useEffect(() => { load(); }, []);

  async function runInvoke(override_id) {
    let params = {};
    try { params = paramsJson.trim() ? JSON.parse(paramsJson) : {}; }
    catch (e) { setInvokeResult({ status: 0, data: { error: `invalid JSON: ${e.message}` } }); return; }
    setBusy(true);
    const r = await toolsApi.invoke(invokeTarget.name, { params, override_id });
    setInvokeResult(r);
    setBusy(false);
  }

  return (
    <div className="space-y-6" data-testid="page-tools">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-mono tracking-tight text-white">Tools</h1>
          <p className="text-xs text-neutral-400 mt-1 font-mono max-w-2xl">
            Native built-ins + your webhook tools + every tool relayed from your registered MCP servers.
            Every call is sentinel-gated — cliff markers can halt a tool just like a chat turn.
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setAddOpen(true)} data-testid="tools-add-webhook-btn"
                  className="inline-flex items-center gap-1.5 px-3 py-2 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10">
            <Plus size={14} /> webhook tool
          </button>
          <button onClick={load} disabled={busy} data-testid="tools-refresh-btn"
                  className="inline-flex items-center gap-1.5 px-3 py-2 border border-white/10 text-neutral-300 font-mono text-xs uppercase tracking-wider hover:bg-bg-surface disabled:opacity-40">
            <ArrowsClockwise size={14} /> refresh
          </button>
        </div>
      </header>

      {err && <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="tools-error">{String(err)}</div>}

      <div className="border border-white/10 overflow-x-auto" data-testid="tools-table">
        <table className="w-full text-left">
          <thead className="bg-bg-surface text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">
            <tr><th className="px-3 py-2">name</th><th className="px-3 py-2">kind</th><th className="px-3 py-2">description</th><th className="px-3 py-2">source</th><th className="px-3 py-2 text-right">actions</th></tr>
          </thead>
          <tbody>
            {tools.length === 0 && (
              <tr><td colSpan={5} className="px-3 py-6 text-neutral-500 text-xs font-mono" data-testid="tools-empty">loading…</td></tr>
            )}
            {tools.map(t => (
              <ToolRow key={t.name} t={t}
                       onInvoke={tt => { setInvokeTarget(tt); setParamsJson(JSON.stringify(_seedFromSchema(tt.input_schema), null, 2)); setInvokeResult(null); }}
                       onDelete={async tt => { if (window.confirm(`Delete tool ${tt.name}?`)) { await toolsApi.remove(tt.name); await load(); } }} />
            ))}
          </tbody>
        </table>
      </div>

      {addOpen && <AddWebhookForm onClose={() => setAddOpen(false)} onSaved={async () => { setAddOpen(false); await load(); }} />}

      {invokeTarget && (
        <div className="fixed inset-0 bg-black/70 grid place-items-center p-4 z-40" data-testid="tool-invoke-modal">
          <div className="w-full max-w-2xl border border-white/10 bg-bg-panel">
            <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
              <div className="font-mono text-sm text-white">invoke · {invokeTarget.name}</div>
              <button onClick={() => setInvokeTarget(null)} className="text-neutral-400 hover:text-white text-xs font-mono">close</button>
            </div>
            <div className="p-4 space-y-3">
              <label className="block text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">params (json)</label>
              <textarea data-testid="tool-params-input" rows={8} value={paramsJson} onChange={e => setParamsJson(e.target.value)}
                        className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
              {invokeResult && (
                <div className={`border ${invokeResult.status === 202 ? "border-rose-500/40" : "border-white/10"} bg-bg-surface px-2 py-1.5 text-[0.65rem] font-mono text-neutral-200 max-h-48 overflow-auto`} data-testid="tool-invoke-result">
                  {invokeResult.status === 202 && <div className="flex items-center gap-1 text-rose-300 mb-1"><ShieldWarning size={12}/> sentinel halt — override_id {invokeResult.data?.override_id}</div>}
                  <pre className="whitespace-pre-wrap">{JSON.stringify(invokeResult.data, null, 2)}</pre>
                </div>
              )}
              <div className="flex justify-end gap-2">
                {invokeResult?.data?.halt && invokeResult.data.override_id && (
                  <button data-testid="tool-invoke-resume-btn" onClick={() => runInvoke(invokeResult.data.override_id)}
                          className="px-3 py-1.5 border border-amber-400/40 text-amber-200 font-mono text-xs uppercase tracking-wider hover:bg-amber-400/10">
                    approve & resume (manage in /overrides first)
                  </button>
                )}
                <button data-testid="tool-invoke-run-btn" onClick={() => runInvoke()} disabled={busy}
                        className="px-3 py-1.5 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10 disabled:opacity-40">
                  {busy ? "calling…" : "run"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function _seedFromSchema(schema) {
  const out = {};
  for (const k of Object.keys(schema?.properties || {})) out[k] = "";
  for (const k of (schema?.required || [])) if (!(k in out)) out[k] = "";
  return out;
}

function AddWebhookForm({ onClose, onSaved }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [err, setErr] = useState(null);
  const ready = name.length >= 2 && webhookUrl.startsWith("http");
  async function submit(e) {
    e.preventDefault();
    setErr(null);
    try {
      await toolsApi.registerWebhook({ name, description, webhook_url: webhookUrl, webhook_secret: webhookSecret });
      onSaved();
    } catch (ex) {
      setErr(ex?.response?.data?.detail || ex.message);
    }
  }
  return (
    <div className="fixed inset-0 bg-black/70 grid place-items-center p-4 z-40" data-testid="tools-add-modal">
      <form onSubmit={submit} className="w-full max-w-lg border border-white/10 bg-bg-panel p-4 space-y-3">
        <div className="font-mono text-sm text-white">register a webhook tool</div>
        {err && <div className="border border-rose-500/40 bg-rose-500/10 px-2 py-1 text-rose-300 text-xs font-mono">{String(err)}</div>}
        <input data-testid="webhook-name-input" value={name} onChange={e => setName(e.target.value)} placeholder="name (unique)" className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
        <input data-testid="webhook-desc-input" value={description} onChange={e => setDescription(e.target.value)} placeholder="description" className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
        <input data-testid="webhook-url-input" value={webhookUrl} onChange={e => setWebhookUrl(e.target.value)} placeholder="https://your-server/your-tool" className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
        <input data-testid="webhook-secret-input" value={webhookSecret} onChange={e => setWebhookSecret(e.target.value)} placeholder="hmac shared secret (optional)" className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
        <div className="flex justify-end gap-2 pt-1">
          <button type="button" onClick={onClose} className="px-3 py-1.5 border border-white/10 text-neutral-300 font-mono text-xs uppercase tracking-wider hover:bg-bg-surface">cancel</button>
          <button type="submit" disabled={!ready} data-testid="webhook-submit-btn" className="px-3 py-1.5 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10 disabled:opacity-40">register</button>
        </div>
      </form>
    </div>
  );
}
