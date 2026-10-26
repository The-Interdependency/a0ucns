import React from 'react';
import { CheckCircle2, Copy, Loader2, ShieldCheck, Trash2, Wand2 } from 'lucide-react';
import { toast } from 'sonner';
import { getModelDefaultPayload } from '../../lib/modelDefaults';

function statusTone(status) {
  if (status === 'verified' || status === 'verified_via_provider') return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300';
  if (status === 'missing_key') return 'border-amber-500/30 bg-amber-500/10 text-amber-200';
  if (status === 'auth_failed' || status === 'rate_limited') return 'border-orange-500/30 bg-orange-500/10 text-orange-200';
  return 'border-red-500/30 bg-red-500/10 text-red-200';
}

export function RegistryTreeNode({
  developer,
  keyStatus,
  defaultsNode,
  verificationMap,
  busyKey,
  onAddModel,
  onInstantiateModel,
  onVerifyModel,
  onVerifyDeveloper,
  onRemoveModel,
  onRemoveDeveloper,
}) {
  const universalManaged = developer.auth_type === 'emergent';

  const copyDefaultPayload = async (developerId, modelId) => {
    const payload = getModelDefaultPayload(developerId, modelId);
    try {
      await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
      toast.success('Copied model default JSON payload');
    } catch {
      toast.error('Unable to copy payload');
    }
  };

  return (
    <details className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950/60" data-testid={`registry-tree-node-${developer.developer_id}`}>
      <summary className="cursor-pointer list-none border-b border-zinc-800 px-4 py-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-semibold text-zinc-100">{developer.name}</h3>
              <span className="rounded-full border border-zinc-800 bg-zinc-900/70 px-2 py-1 text-[11px] text-zinc-400">{developer.developer_id}</span>
              <span className={`rounded-full border px-2 py-1 text-[11px] ${keyStatus?.status === 'configured' || keyStatus?.status === 'universal' ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300' : 'border-amber-500/30 bg-amber-500/10 text-amber-200'}`} data-testid={`registry-key-status-${developer.developer_id}`}>
                Key: {keyStatus?.status || 'missing'}
              </span>
              {universalManaged && <span className="rounded-full border border-blue-500/30 bg-blue-500/10 px-2 py-1 text-[11px] text-blue-200">Universal key compatible</span>}
            </div>
            <div className="mt-1 text-xs text-zinc-500">{developer.models.length} model{developer.models.length === 1 ? '' : 's'} available under this key.</div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={(event) => {
                event.preventDefault();
                onVerifyDeveloper(developer.developer_id);
              }}
              disabled={busyKey === `verify-dev-${developer.developer_id}`}
              className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 transition hover:border-zinc-700 hover:text-white disabled:opacity-60"
              data-testid={`registry-verify-developer-button-${developer.developer_id}`}
            >
              <span className="flex items-center gap-2">{busyKey === `verify-dev-${developer.developer_id}` ? <Loader2 size={13} className="animate-spin" /> : <ShieldCheck size={13} />} Verify key/models</span>
            </button>
            {!universalManaged && (
              <button
                type="button"
                onClick={(event) => {
                  event.preventDefault();
                  onAddModel(developer.developer_id);
                }}
                className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 transition hover:border-zinc-700 hover:text-white"
                data-testid={`registry-add-model-button-${developer.developer_id}`}
              >
                Add model
              </button>
            )}
            {!universalManaged && (
              <button
                type="button"
                onClick={(event) => {
                  event.preventDefault();
                  onRemoveDeveloper(developer.developer_id);
                }}
                className="rounded-xl border border-zinc-800 p-2 text-zinc-500 transition hover:border-red-500/30 hover:text-red-300"
                data-testid={`registry-remove-developer-button-${developer.developer_id}`}
              >
                <Trash2 size={13} />
              </button>
            )}
          </div>
        </div>
      </summary>

      <div className="space-y-2 p-3" data-testid={`registry-model-branch-${developer.developer_id}`}>
        {developer.models.map((model) => {
          const verifyKey = `${developer.developer_id}:${model.model_id}`;
          const verification = verificationMap[verifyKey];
          const modelPayload = defaultsNode?.models?.[model.model_id] || getModelDefaultPayload(developer.developer_id, model.model_id);

          return (
            <details key={model.model_id} className="rounded-2xl border border-zinc-800 bg-zinc-900/50" data-testid={`registry-model-node-${developer.developer_id}-${model.model_id}`}>
              <summary className="cursor-pointer list-none px-3 py-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-sm text-zinc-100">{model.display_name || model.model_id}</div>
                    <div className="mt-1 text-xs text-zinc-500">{model.model_id}</div>
                    {verification && (
                      <div className={`mt-2 inline-flex max-w-full items-center gap-2 rounded-full border px-2 py-1 text-[11px] ${statusTone(verification.status)}`}>
                        <CheckCircle2 size={11} />
                        <span className="truncate">{verification.status}</span>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <button type="button" onClick={(event) => { event.preventDefault(); onInstantiateModel(developer, model); }} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 transition hover:border-zinc-700 hover:text-white" data-testid={`registry-instantiate-button-${developer.developer_id}-${model.model_id}`}>
                      <span className="flex items-center gap-2"><Wand2 size={13} /> Instantiate</span>
                    </button>
                    <button
                      type="button"
                      onClick={(event) => { event.preventDefault(); onVerifyModel(developer.developer_id, model.model_id); }}
                      disabled={busyKey === `verify-model-${developer.developer_id}-${model.model_id}`}
                      className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 transition hover:border-zinc-700 hover:text-white disabled:opacity-60"
                      data-testid={`registry-verify-model-button-${developer.developer_id}-${model.model_id}`}
                    >
                      <span className="flex items-center gap-2">{busyKey === `verify-model-${developer.developer_id}-${model.model_id}` ? <Loader2 size={13} className="animate-spin" /> : <ShieldCheck size={13} />} Verify</span>
                    </button>
                    {!universalManaged && (
                      <button type="button" onClick={(event) => { event.preventDefault(); onRemoveModel(developer.developer_id, model.model_id); }} className="rounded-xl border border-zinc-800 p-2 text-zinc-500 transition hover:border-red-500/30 hover:text-red-300" data-testid={`registry-remove-model-button-${developer.developer_id}-${model.model_id}`}>
                        <Trash2 size={13} />
                      </button>
                    )}
                  </div>
                </div>
              </summary>
              <div className="border-t border-zinc-800 bg-zinc-950/70 p-3" data-testid={`registry-model-default-json-${developer.developer_id}-${model.model_id}`}>
                <div className="mb-2 flex items-center justify-between">
                  <div className="text-xs font-medium text-zinc-300">Default request JSON</div>
                  <button type="button" onClick={() => copyDefaultPayload(developer.developer_id, model.model_id)} className="rounded-xl border border-zinc-800 px-2 py-1 text-[11px] text-zinc-300 hover:text-white" data-testid={`registry-copy-default-json-button-${developer.developer_id}-${model.model_id}`}>
                    <span className="flex items-center gap-1"><Copy size={11} /> Copy</span>
                  </button>
                </div>
                <pre className="max-h-64 overflow-auto rounded-xl border border-zinc-800 bg-zinc-950 p-3 text-[11px] text-zinc-300">{JSON.stringify(modelPayload, null, 2)}</pre>
              </div>
            </details>
          );
        })}
      </div>
    </details>
  );
}
