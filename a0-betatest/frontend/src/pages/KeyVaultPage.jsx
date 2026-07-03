// === MODULE_BUILD ===
// id: fe_page_keyvault
//   module_name: KeyVaultPage
//   module_kind: ui_page
//   summary: BYOK key vault — list, upsert (Fernet-encrypted), delete BYOK provider keys (OpenAI/Anthropic/Gemini/XAI)
//   owner: Erin Spencer
//   public_surface: KeyVaultPage
//   internal_surface: none
//   auth_boundary: none
//   storage_boundary: write
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_page_keyvault_boundaries
//   summary: BYOK key crud
//   auth_boundary: none
//   storage_boundary: write
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_keyvault
//   summary: BYOK keys management ui
//   exposes: KeyVaultPage
//   boundaries: auth:none, storage:write, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===


import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Panel, Pill, AsciiLoader } from "../components/Panel";
import { Trash, ArrowsClockwise, Plus, Eye, EyeSlash } from "@phosphor-icons/react";

const PROVIDERS = [
  { id: "openai",    label: "OpenAI",    note: "GPT-5.x, GPT-4o, o3 family",        url: "https://platform.openai.com/api-keys" },
  { id: "anthropic", label: "Anthropic", note: "Claude Sonnet/Haiku/Opus 4.5+",    url: "https://console.anthropic.com/" },
  { id: "gemini",    label: "Google",    note: "Gemini 2.5/3 family",              url: "https://aistudio.google.com/app/apikey" },
  { id: "xai",       label: "xAI",       note: "Grok 4 Fast & beta",               url: "https://console.x.ai/" },
];

export default function KeyVaultPage() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [edits, setEdits] = useState({});
  const [reveal, setReveal] = useState({});
  const [busy, setBusy] = useState(false);

  async function refresh() {
    setLoading(true);
    const r = await api.listKeys();
    setKeys(r.keys || []);
    setLoading(false);
  }
  useEffect(() => { refresh(); }, []);

  async function save(provider) {
    const value = (edits[provider] || "").trim();
    if (!value) return;
    setBusy(true);
    try {
      await api.upsertKey({ user_id: "local", provider, api_key: value });
      setEdits(e => ({ ...e, [provider]: "" }));
      await refresh();
    } catch (e) {
      alert(`failed to save: ${e?.response?.data?.detail || e.message}`);
    } finally { setBusy(false); }
  }

  async function remove(id) {
    if (!window.confirm("Delete this key?")) return;
    setBusy(true);
    try { await api.deleteKey(id); await refresh(); } finally { setBusy(false); }
  }

  const byProvider = Object.fromEntries(keys.map(k => [k.provider, k]));

  return (
    <div className="space-y-6" data-testid="page-keys">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-2xl tracking-tighter">BYOK · Key Vault</h1>
          <p className="text-neutral-400 text-sm mt-1 max-w-2xl">
            Bring your own keys. Stored encrypted at rest (Fernet AES-128-CBC + HMAC). Used per-request against each provider — never exfiltrated.
          </p>
        </div>
        <button className="btn-ghost" onClick={refresh} data-testid="keys-refresh">
          <ArrowsClockwise size={14} /> refresh
        </button>
      </header>

      <div className="grid md:grid-cols-2 gap-4">
        {PROVIDERS.map(p => {
          const existing = byProvider[p.id];
          return (
            <Panel key={p.id} title={p.label} testid={`key-panel-${p.id}`}
              right={existing ? <Pill tone="emerald" testid={`key-status-${p.id}`}>active</Pill> : <Pill tone="rose" testid={`key-status-${p.id}`}>missing</Pill>}>
              <div className="p-4 space-y-3">
                <div className="text-xs text-neutral-400 font-mono">{p.note}</div>

                {existing ? (
                  <div className="flex items-center justify-between bg-bg-deep border border-white/10 p-3">
                    <div className="font-mono text-sm">
                      <span className="text-accent-cyan">key</span>
                      <span className="text-neutral-500"> :: </span>
                      <span>{existing.masked}</span>
                    </div>
                    <button className="btn-danger" onClick={() => remove(existing.id)} data-testid={`key-delete-${p.id}`}>
                      <Trash size={14} /> remove
                    </button>
                  </div>
                ) : (
                  <div className="text-xs text-neutral-500 font-mono">
                    No key set. <a href={p.url} target="_blank" rel="noreferrer" className="text-accent-cyan underline">Get one →</a>
                  </div>
                )}

                <div className="flex gap-2 items-stretch">
                  <input
                    type={reveal[p.id] ? "text" : "password"}
                    autoComplete="off"
                    className="input-term flex-1"
                    placeholder={existing ? `replace ${p.label} key…` : `paste ${p.label} key (sk-..., AIza..., xai-...)`}
                    value={edits[p.id] || ""}
                    onChange={e => setEdits(s => ({ ...s, [p.id]: e.target.value }))}
                    data-testid={`key-input-${p.id}`}
                  />
                  <button
                    className="btn-ghost px-3"
                    onClick={() => setReveal(s => ({ ...s, [p.id]: !s[p.id] }))}
                    title="show/hide"
                    type="button"
                    data-testid={`key-reveal-${p.id}`}
                  >
                    {reveal[p.id] ? <EyeSlash size={14} /> : <Eye size={14} />}
                  </button>
                  <button
                    className="btn-primary"
                    onClick={() => save(p.id)}
                    disabled={busy || !(edits[p.id] || "").trim()}
                    data-testid={`key-save-${p.id}`}
                  >
                    <Plus size={14} /> {existing ? "replace" : "save"}
                  </button>
                </div>
              </div>
            </Panel>
          );
        })}
      </div>

      <Panel title="BYOK · OpenAI / Anthropic / Google / xAI">
        <div className="p-4 text-xs text-neutral-400 leading-relaxed font-sans">
          This build is fully BYOK — your own provider keys, encrypted at rest, used per request.
          There is no platform fallback. Add a key above to populate the inventory and unlock that provider for chat.
        </div>
      </Panel>

      {loading && <AsciiLoader label="loading vault" />}
    </div>
  );
}
