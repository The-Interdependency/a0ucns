// === MODULE_BUILD ===
// id: fe_page_vault
//   module_name: VaultPage
//   module_kind: ui_page
//   summary: per-site multi-account env vault — list, reveal (decrypts on demand), upsert, delete
//   owner: Erin Spencer
//   public_surface: VaultPage
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
// id: fe_page_vault_boundaries
//   summary: env vault CRUD ui
//   auth_boundary: none
//   storage_boundary: write
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_vault
//   summary: env vault ui
//   exposes: VaultPage
//   boundaries: auth:none, storage:write, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===


import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Panel, Pill, AsciiLoader } from "../components/Panel";
import { Plus, Trash, Eye, EyeSlash, Vault } from "@phosphor-icons/react";

export default function VaultPage() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);

  // new entry form
  const [site, setSite] = useState("");
  const [label, setLabel] = useState("");
  const [kv, setKv] = useState([{ k: "", v: "" }]);
  const [busy, setBusy] = useState(false);
  const [revealed, setRevealed] = useState({}); // { [id]: { [k]: v } }

  async function load() {
    setLoading(true);
    const r = await api.listVault();
    setAccounts(r.accounts || []);
    setLoading(false);
  }
  useEffect(() => { load(); }, []);

  async function save() {
    if (!site.trim() || !label.trim()) { alert("site + account_label required"); return; }
    const env = {};
    for (const row of kv) {
      const k = (row.k || "").trim();
      if (k) env[k] = row.v || "";
    }
    setBusy(true);
    try {
      await api.upsertVault({ user_id: "local", site: site.trim(), account_label: label.trim(), env });
      setSite(""); setLabel(""); setKv([{ k: "", v: "" }]);
      await load();
    } catch (e) {
      alert("save failed: " + (e?.response?.data?.detail || e.message));
    } finally { setBusy(false); }
  }

  async function remove(id) {
    if (!window.confirm("Remove this site account?")) return;
    await api.deleteVault(id); await load();
  }

  async function reveal(id, keys) {
    const r = await api.revealVault({ user_id: "local", id, keys });
    setRevealed(s => ({ ...s, [id]: r.values || {} }));
  }
  function hide(id) {
    setRevealed(s => { const n = { ...s }; delete n[id]; return n; });
  }

  return (
    <div className="space-y-6" data-testid="page-vault">
      <header>
        <h1 className="font-mono text-2xl tracking-tighter flex items-center gap-2">
          <Vault size={22} className="text-accent-cyan"/> Env Vault · per-site multi-account
        </h1>
        <p className="text-neutral-400 text-sm mt-1 max-w-2xl">
          Hold .env values for multiple accounts on the same site (e.g. GitHub personal + work, Gmail
          home + research). Values are encrypted at rest. Reveal on demand only.
        </p>
      </header>

      <Panel title="new account">
        <div className="p-4 space-y-3">
          <div className="grid md:grid-cols-2 gap-2">
            <div>
              <label className="section-overline">site</label>
              <input className="input-term" placeholder="github.com, gmail.com, …"
                value={site} onChange={e => setSite(e.target.value)}
                data-testid="vault-site"/>
            </div>
            <div>
              <label className="section-overline">account label</label>
              <input className="input-term" placeholder="personal · work · research…"
                value={label} onChange={e => setLabel(e.target.value)}
                data-testid="vault-label"/>
            </div>
          </div>
          <div className="border border-white/10">
            <div className="px-3 py-2 border-b border-white/10 flex items-center justify-between">
              <span className="section-overline">env entries</span>
              <button className="btn-ghost py-1 px-2 text-[0.65rem]"
                onClick={() => setKv(rows => [...rows, { k: "", v: "" }])}
                data-testid="vault-add-row">
                <Plus size={12}/> row
              </button>
            </div>
            <div className="p-3 space-y-2">
              {kv.map((row, i) => (
                <div key={i} className="grid grid-cols-[1fr_2fr_auto] gap-2">
                  <input className="input-term" placeholder="KEY_NAME"
                    value={row.k}
                    onChange={e => setKv(rows => rows.map((r, ix) => ix === i ? { ...r, k: e.target.value } : r))}
                    data-testid={`vault-key-${i}`}/>
                  <input className="input-term" placeholder="value (encrypted at rest)"
                    value={row.v}
                    onChange={e => setKv(rows => rows.map((r, ix) => ix === i ? { ...r, v: e.target.value } : r))}
                    data-testid={`vault-val-${i}`}/>
                  <button className="btn-ghost"
                    onClick={() => setKv(rows => rows.filter((_, ix) => ix !== i))}
                    data-testid={`vault-row-rm-${i}`}>
                    <Trash size={14}/>
                  </button>
                </div>
              ))}
            </div>
          </div>
          <div>
            <button className="btn-primary" onClick={save} disabled={busy} data-testid="vault-save">
              <Plus size={14}/> save
            </button>
          </div>
        </div>
      </Panel>

      <Panel title={`accounts · ${accounts.length}`}>
        <ul className="divide-y divide-white/5">
          {accounts.map(a => (
            <li key={a.id} className="p-4 flex flex-col md:flex-row md:items-start md:justify-between gap-3" data-testid={`vault-row-${a.id}`}>
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-2">
                  <Pill tone="cyan">{a.site}</Pill>
                  <Pill tone="amber">{a.account_label}</Pill>
                  <span className="text-[0.65rem] text-neutral-500 font-mono">{a.env_keys.length} entries</span>
                </div>
                <div className="font-mono text-xs space-y-1">
                  {a.env_keys.map(k => (
                    <div key={k} className="flex items-center gap-3">
                      <span className="text-accent-cyan w-48">{k}</span>
                      <span className="text-neutral-300 truncate">
                        {revealed[a.id]?.[k] ?? "•••••••••"}
                      </span>
                    </div>
                  ))}
                  {!a.env_keys.length && <div className="text-neutral-500">no entries</div>}
                </div>
              </div>
              <div className="flex flex-col gap-2 items-stretch md:items-end">
                {!revealed[a.id] ? (
                  <button className="btn-ghost" onClick={() => reveal(a.id, a.env_keys)} data-testid={`vault-reveal-${a.id}`}>
                    <Eye size={14}/> reveal
                  </button>
                ) : (
                  <button className="btn-ghost" onClick={() => hide(a.id)} data-testid={`vault-hide-${a.id}`}>
                    <EyeSlash size={14}/> hide
                  </button>
                )}
                <button className="btn-danger" onClick={() => remove(a.id)} data-testid={`vault-del-${a.id}`}>
                  <Trash size={14}/> delete
                </button>
              </div>
            </li>
          ))}
          {!accounts.length && !loading && (
            <li className="p-6 text-center text-xs text-neutral-500 font-mono">No site accounts saved yet.</li>
          )}
        </ul>
      </Panel>
      {loading && <AsciiLoader label="loading vault"/>}
    </div>
  );
}
