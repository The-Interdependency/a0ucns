import React from 'react';
import { CheckCircle2, ExternalLink, Globe, Loader2, Plus, ShieldCheck, Trash2, Wand2 } from 'lucide-react';

function statusTone(status) {
  if (status === 'verified' || status === 'verified_via_provider') return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300';
  if (status === 'missing_key') return 'border-amber-500/30 bg-amber-500/10 text-amber-200';
  if (status === 'auth_failed' || status === 'rate_limited') return 'border-orange-500/30 bg-orange-500/10 text-orange-200';
  return 'border-red-500/30 bg-red-500/10 text-red-200';
}

export function RegistryDeveloperCard({
  developer,
  verificationMap,
  busyKey,
  addingModel,
  newModel,
  setNewModel,
  setAddingModel,
  onAddModel,
  onRemoveModel,
  onInstantiateModel,
  onVerifyModel,
  onVerifyDeveloper,
  onRemoveDeveloper,
}) {
  const universalManaged = developer.auth_type === 'emergent';

  return (
    <article className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950/60">
      <div className="border-b border-zinc-800 px-4 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-semibold text-zinc-100">{developer.name}</h3>
              <span className="rounded-full border border-zinc-800 bg-zinc-900/70 px-2 py-1 text-[11px] text-zinc-400">{developer.auth_type}</span>
              {universalManaged && <span className="rounded-full border border-blue-500/30 bg-blue-500/10 px-2 py-1 text-[11px] text-blue-200">Universal key compatible</span>}
            </div>
            <div className="mt-2 space-y-1 text-xs text-zinc-500">
              <div>ID: <span className="text-zinc-300">{developer.developer_id}</span></div>
              {developer.base_url && <div>Base URL: <span className="text-zinc-300 break-all">{developer.base_url}</span></div>}
              {universalManaged && <div className="text-blue-200">This list is curated automatically to models that work with the universal key.</div>}
              {developer.website && (
                <a href={developer.website} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-blue-300 hover:text-blue-200">
                  <Globe size={12} /> Website <ExternalLink size={11} />
                </a>
              )}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => onVerifyDeveloper(developer.developer_id)}
              disabled={busyKey === `verify-dev-${developer.developer_id}`}
              className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 transition hover:border-zinc-700 hover:text-white disabled:opacity-60"
            >
              <span className="flex items-center gap-2">{busyKey === `verify-dev-${developer.developer_id}` ? <Loader2 size={13} className="animate-spin" /> : <ShieldCheck size={13} />} Verify developer</span>
            </button>
            {!universalManaged && (
              <button type="button" onClick={() => onRemoveDeveloper(developer.developer_id)} className="rounded-xl border border-zinc-800 p-2 text-zinc-500 transition hover:border-red-500/30 hover:text-red-300">
                <Trash2 size={13} />
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="space-y-2 p-3">
        {developer.models.map((model) => {
          const verifyKey = `${developer.developer_id}:${model.model_id}`;
          const verification = verificationMap[verifyKey];
          return (
            <div key={model.model_id} className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-3">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-sm text-zinc-100">{model.display_name || model.model_id}</div>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-zinc-500">
                    <span>{model.model_id}</span>
                    {universalManaged && <span className="rounded-full border border-blue-500/30 bg-blue-500/10 px-2 py-1 text-[10px] text-blue-200">Universal key</span>}
                  </div>
                  {verification && (
                    <div className={`mt-2 inline-flex max-w-full items-center gap-2 rounded-full border px-2 py-1 text-[11px] ${statusTone(verification.status)}`}>
                      <CheckCircle2 size={11} />
                      <span className="truncate">{verification.status}</span>
                    </div>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <button type="button" onClick={() => onInstantiateModel(developer, model)} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 transition hover:border-zinc-700 hover:text-white">
                    <span className="flex items-center gap-2"><Wand2 size={13} /> Instantiate</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => onVerifyModel(developer.developer_id, model.model_id)}
                    disabled={busyKey === `verify-model-${developer.developer_id}-${model.model_id}`}
                    className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 transition hover:border-zinc-700 hover:text-white disabled:opacity-60"
                  >
                    <span className="flex items-center gap-2">{busyKey === `verify-model-${developer.developer_id}-${model.model_id}` ? <Loader2 size={13} className="animate-spin" /> : <ShieldCheck size={13} />} Verify</span>
                  </button>
                  {!universalManaged && (
                    <button type="button" onClick={() => onRemoveModel(developer.developer_id, model.model_id)} className="rounded-xl border border-zinc-800 p-2 text-zinc-500 transition hover:border-red-500/30 hover:text-red-300">
                      <Trash2 size={13} />
                    </button>
                  )}
                </div>
              </div>
              {verification?.message && <div className="mt-2 text-xs text-zinc-500">{verification.message}</div>}
            </div>
          );
        })}

        {!universalManaged && addingModel === developer.developer_id ? (
          <div className="mt-3 flex flex-wrap items-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-3">
            <input
              value={newModel}
              onChange={(event) => setNewModel(event.target.value)}
              placeholder="model-id"
              className="min-w-[180px] flex-1 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-zinc-100 outline-none focus:border-emerald-500/50"
            />
            <button type="button" onClick={() => onAddModel(developer.developer_id)} className="rounded-xl bg-emerald-600 px-3 py-2 text-xs font-medium text-white hover:bg-emerald-500">Add model</button>
            <button type="button" onClick={() => setAddingModel('')} className="text-xs text-zinc-500 hover:text-zinc-300">Cancel</button>
          </div>
        ) : !universalManaged ? (
          <button type="button" onClick={() => setAddingModel(developer.developer_id)} className="mt-2 inline-flex items-center gap-2 px-1 text-xs text-zinc-500 hover:text-zinc-300">
            <Plus size={12} /> Add model
          </button>
        ) : null}
      </div>
    </article>
  );
}
