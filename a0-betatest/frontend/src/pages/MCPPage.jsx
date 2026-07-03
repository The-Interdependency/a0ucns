// === MODULE_BUILD ===
// id: fe_page_mcp
//   module_name: MCPPage
//   module_kind: ui_page
//   summary: Model Context Protocol surface — (a) inbound: shows the user's publish token + URL so external Claude Desktop / Cursor / etc. can connect to a0p as an MCP server; (b) outbound: lets the user register external MCP servers (GitHub MCP, Slack MCP, Postgres MCP, ...) and refreshes their tool catalogs into the user's tool registry
//   owner: Erin Spencer
//   public_surface: MCPPage
//   internal_surface: ServerRow, AddServerForm, PublishCard
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
// id: fe_page_mcp_boundaries
//   summary: MCP server + client management ui
//   auth_boundary: bearer
//   storage_boundary: write
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_mcp
//   summary: MCP server + client ui
//   exposes: MCPPage
//   boundaries: auth:bearer, storage:write, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useEffect, useState } from "react";
import { Plus, ArrowsClockwise, Trash, Copy, Key, ArrowUpRight } from "@phosphor-icons/react";
import { mcpClientApi, mcpPublishApi } from "../lib/api_tools";

function PublishCard() {
  const [tok, setTok] = useState(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => { mcpPublishApi.getToken().then(setTok).catch(() => {}); }, []);
  const publicUrl = `${process.env.REACT_APP_BACKEND_URL}/api/mcp`;
  const headerExample = `Authorization: Bearer ${tok?.token || "<your-token>"}`;
  async function rotate() {
    if (!window.confirm("Rotate the publish token? Any external client using the old token will lose access.")) return;
    setBusy(true);
    try { const r = await mcpPublishApi.rotate(); setTok({ ...tok, token: r.token }); }
    finally { setBusy(false); }
  }
  return (
    <div className="border border-accent-cyan/30 bg-accent-cyan/5 p-4 space-y-3" data-testid="mcp-publish-card">
      <div className="flex items-center gap-2">
        <Key size={16} className="text-accent-cyan" />
        <div className="font-mono text-sm text-white">a0p as MCP server</div>
        <span className="ml-auto text-[0.6rem] font-mono text-neutral-500 uppercase tracking-ultra">inbound</span>
      </div>
      <p className="text-[0.7rem] font-mono text-neutral-400">
        Point any MCP-aware client (Claude Desktop, Cursor, …) at this URL with your bearer token.
        Your agents, tools, vault metadata, and the living spec become first-class resources.
      </p>
      <pre className="bg-bg-surface border border-white/10 px-2 py-1.5 text-[0.65rem] font-mono text-neutral-200 overflow-x-auto" data-testid="mcp-publish-url">{publicUrl}</pre>
      <pre className="bg-bg-surface border border-white/10 px-2 py-1.5 text-[0.65rem] font-mono text-neutral-200 overflow-x-auto" data-testid="mcp-publish-header">{headerExample}</pre>
      <div className="flex gap-2">
        <button onClick={() => navigator.clipboard.writeText(tok?.token || "")} data-testid="mcp-publish-copy"
                className="inline-flex items-center gap-1 px-2 py-1.5 border border-white/10 text-neutral-300 font-mono text-[0.65rem] uppercase tracking-wider hover:bg-bg-surface">
          <Copy size={12} /> copy token
        </button>
        <button onClick={rotate} disabled={busy} data-testid="mcp-publish-rotate"
                className="inline-flex items-center gap-1 px-2 py-1.5 border border-amber-400/40 text-amber-300 font-mono text-[0.65rem] uppercase tracking-wider hover:bg-amber-400/10 disabled:opacity-40">
          rotate
        </button>
      </div>
    </div>
  );
}

function ServerRow({ s, onRefresh, onDelete }) {
  return (
    <tr className="border-t border-white/5" data-testid={`mcp-server-row-${s.name}`}>
      <td className="px-3 py-2 font-mono text-xs text-white">{s.name}</td>
      <td className="px-3 py-2 font-mono text-[0.65rem] text-neutral-400 break-all">{s.url}</td>
      <td className="px-3 py-2 font-mono text-[0.65rem] text-neutral-300">{s.tools_count}</td>
      <td className="px-3 py-2 font-mono text-[0.6rem] text-neutral-500">{s.last_refresh_ms ? new Date(s.last_refresh_ms).toLocaleString() : "—"}</td>
      <td className="px-3 py-2 text-right space-x-1">
        <button onClick={() => onRefresh(s)} data-testid={`mcp-server-refresh-${s.name}`}
                className="inline-flex items-center gap-1 px-2 py-1 border border-white/10 text-neutral-300 text-[0.6rem] font-mono uppercase tracking-wider hover:bg-bg-surface">
          <ArrowsClockwise size={12} /> refresh
        </button>
        <button onClick={() => onDelete(s)} data-testid={`mcp-server-delete-${s.name}`}
                className="inline-flex items-center gap-1 px-2 py-1 border border-rose-500/40 text-rose-300 text-[0.6rem] font-mono uppercase tracking-wider hover:bg-rose-500/10">
          <Trash size={12} />
        </button>
      </td>
    </tr>
  );
}

function AddServerForm({ onClose, onSaved }) {
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [token, setToken] = useState("");
  const [err, setErr] = useState(null);
  async function submit(e) {
    e.preventDefault(); setErr(null);
    try { await mcpClientApi.add({ name, url, token: token || null }); onSaved(); }
    catch (ex) { setErr(ex?.response?.data?.detail || ex.message); }
  }
  return (
    <div className="fixed inset-0 bg-black/70 grid place-items-center p-4 z-40" data-testid="mcp-add-modal">
      <form onSubmit={submit} className="w-full max-w-lg border border-white/10 bg-bg-panel p-4 space-y-3">
        <div className="font-mono text-sm text-white">add external MCP server</div>
        {err && <div className="border border-rose-500/40 bg-rose-500/10 px-2 py-1 text-rose-300 text-xs font-mono">{String(err)}</div>}
        <input data-testid="mcp-name-input" value={name} onChange={e => setName(e.target.value)} placeholder="name (e.g. github-mcp)" className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
        <input data-testid="mcp-url-input" value={url} onChange={e => setUrl(e.target.value)} placeholder="https://your-mcp-server/rpc" className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
        <input data-testid="mcp-token-input" value={token} onChange={e => setToken(e.target.value)} placeholder="bearer token (optional)" className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white" />
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="px-3 py-1.5 border border-white/10 text-neutral-300 font-mono text-xs uppercase tracking-wider hover:bg-bg-surface">cancel</button>
          <button type="submit" data-testid="mcp-add-submit-btn" className="px-3 py-1.5 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10">add & probe</button>
        </div>
      </form>
    </div>
  );
}

export default function MCPPage() {
  const [servers, setServers] = useState([]);
  const [addOpen, setAddOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  async function load() {
    setBusy(true);
    try { setServers((await mcpClientApi.list()).servers || []); setErr(null); }
    catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setBusy(false); }
  }
  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-6" data-testid="page-mcp">
      <header className="space-y-1">
        <h1 className="text-3xl font-mono tracking-tight text-white">MCP</h1>
        <p className="text-xs text-neutral-400 font-mono">
          Model Context Protocol — bidirectional. a0p exposes itself as an MCP server (top card),
          and consumes tools from external MCP servers you register here (table below).
        </p>
      </header>

      <PublishCard />

      <section className="space-y-3" data-testid="mcp-client-section">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="font-mono text-sm text-white">your external MCP servers</div>
            <div className="text-[0.65rem] font-mono text-neutral-500">outbound · tools from these appear as <code className="text-accent-cyan">mcp:&lt;server&gt;:&lt;tool&gt;</code> in /tools</div>
          </div>
          <button onClick={() => setAddOpen(true)} data-testid="mcp-add-btn"
                  className="inline-flex items-center gap-1.5 px-3 py-2 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10">
            <Plus size={14} /> add server
          </button>
        </div>

        {err && <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="mcp-error">{String(err)}</div>}

        <div className="border border-white/10 overflow-x-auto" data-testid="mcp-server-table">
          <table className="w-full text-left">
            <thead className="bg-bg-surface text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-400">
              <tr><th className="px-3 py-2">name</th><th className="px-3 py-2">url</th><th className="px-3 py-2">tools</th><th className="px-3 py-2">last refresh</th><th className="px-3 py-2 text-right">actions</th></tr>
            </thead>
            <tbody>
              {servers.length === 0 && (
                <tr><td colSpan={5} className="px-3 py-4 text-neutral-500 text-xs font-mono" data-testid="mcp-empty">no external MCP servers registered yet.</td></tr>
              )}
              {servers.map(s => (
                <ServerRow key={s.id} s={s}
                  onRefresh={async ss => { setBusy(true); await mcpClientApi.refresh(ss.id); await load(); setBusy(false); }}
                  onDelete={async ss => { if (window.confirm(`Delete MCP server ${ss.name}? Its tools will be removed.`)) { await mcpClientApi.remove(ss.id); await load(); } }} />
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {addOpen && <AddServerForm onClose={() => setAddOpen(false)} onSaved={async () => { setAddOpen(false); await load(); }} />}
    </div>
  );
}
