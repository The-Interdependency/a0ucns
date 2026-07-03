import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, Loader2, Plus, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import { hubApi } from '../../lib/hubApi';
import { generateInstanceName } from '../../lib/nameFactory';
import { registryApi } from '../../lib/registryApi';
import { RegistryTreeNode } from './RegistryTreeNode';

function mergeVerificationResults(results) {
  return (results || []).reduce((acc, item) => {
    if (item.model_id) acc[`${item.developer_id}:${item.model_id}`] = item;
    return acc;
  }, {});
}

export function RegistryManager({ onInventoryChanged = async () => {} }) {
  const [registry, setRegistry] = useState([]);
  const [keyMap, setKeyMap] = useState({});
  const [defaultsMap, setDefaultsMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyKey, setBusyKey] = useState('');
  const [addingDev, setAddingDev] = useState(false);
  const [newDev, setNewDev] = useState({ developer_id: '', name: '', base_url: '', website: '' });
  const [verificationMap, setVerificationMap] = useState({});

  const mapKeysByDeveloper = (items) => (items || []).reduce((acc, item) => {
    acc[item.developer_id] = item;
    return acc;
  }, {});

  const fetchRegistry = async (showLoader = true) => {
    if (showLoader) setLoading(true);
    setError('');
    try {
      const [registryResponse, keysResponse] = await Promise.all([
        registryApi.getRegistry(),
        registryApi.getKeys(),
      ]);
      setRegistry(registryResponse?.developers || []);
      setKeyMap(mapKeysByDeveloper(keysResponse || []));
      const defaultsResponse = await registryApi.getDefaults();
      setDefaultsMap(defaultsResponse?.defaults || {});
    } catch (err) {
      setRegistry([]);
      setKeyMap({});
      setDefaultsMap({});
      setError(err.message || 'Could not load the model registry from the backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRegistry();
  }, []);

  const verificationSummary = useMemo(() => {
    const values = Object.values(verificationMap);
    const verified = values.filter((item) => ['verified', 'verified_via_provider'].includes(item.status)).length;
    return { verified, total: values.length };
  }, [verificationMap]);

  const refreshAll = async () => {
    await fetchRegistry(false);
    await onInventoryChanged();
  };

  const addDeveloper = async () => {
    if (!newDev.developer_id || !newDev.name || !newDev.base_url) return;
    try {
      setBusyKey('add-developer');
      await registryApi.addDeveloper({
        developer_id: newDev.developer_id,
        name: newDev.name,
        auth_type: 'openai_compatible',
        base_url: newDev.base_url,
        website: newDev.website || null,
        models: [],
      });
      toast.success(`Added developer ${newDev.name}`);
      setAddingDev(false);
      setNewDev({ developer_id: '', name: '', base_url: '', website: '' });
      await refreshAll();
    } catch (err) {
      toast.error(err.message || 'Failed to add developer');
    } finally {
      setBusyKey('');
    }
  };

  const removeModel = async (developerId, modelId) => {
    try {
      setBusyKey(`remove-model-${developerId}-${modelId}`);
      await registryApi.removeModel(developerId, modelId);
      toast.success(`Removed ${modelId}`);
      await refreshAll();
    } catch (err) {
      toast.error(err.message || 'Failed to remove model');
    } finally {
      setBusyKey('');
    }
  };

  const addModelPrompt = async (developerId) => {
    const modelId = window.prompt('Enter model ID');
    if (!modelId || !modelId.trim()) return;
    try {
      setBusyKey(`add-model-${developerId}`);
      await registryApi.addModel(developerId, { model_id: modelId.trim() });
      toast.success(`Added model ${modelId.trim()}`);
      await refreshAll();
    } catch (err) {
      toast.error(err.message || 'Failed to add model');
    } finally {
      setBusyKey('');
    }
  };

  const removeDeveloper = async (developerId) => {
    try {
      setBusyKey(`remove-dev-${developerId}`);
      await registryApi.removeDeveloper(developerId);
      toast.success(`Removed developer ${developerId}`);
      await refreshAll();
    } catch (err) {
      toast.error(err.message || 'Failed to remove developer');
    } finally {
      setBusyKey('');
    }
  };

  const instantiateModel = async (developer, model) => {
    try {
      setBusyKey(`instantiate-${developer.developer_id}-${model.model_id}`);
      const name = generateInstanceName();
      await hubApi.createInstance({
        name,
        model_id: model.model_id,
        role_preset: null,
        history_window_messages: 12,
        instance_prompt: null,
        context: { role: null, system_message: null, prompt_modifier: null },
        metadata: {
          source: 'registry_instantiate',
          developer_id: developer.developer_id,
          developer_name: developer.name,
          developer_website: developer.website || null,
        },
      });
      toast.success(`Instantiated ${model.model_id} as ${name}`);
      await onInventoryChanged();
    } catch (err) {
      toast.error(err.message || 'Failed to instantiate model');
    } finally {
      setBusyKey('');
    }
  };

  const verifyModel = async (developerId, modelId) => {
    try {
      setBusyKey(`verify-model-${developerId}-${modelId}`);
      const response = await registryApi.verifyModel(developerId, modelId);
      setVerificationMap((prev) => ({ ...prev, ...mergeVerificationResults(response.results) }));
      toast.success(`Verified ${modelId}`);
    } catch (err) {
      toast.error(err.message || 'Model verification failed');
    } finally {
      setBusyKey('');
    }
  };

  const verifyDeveloper = async (developerId) => {
    try {
      setBusyKey(`verify-dev-${developerId}`);
      const response = await registryApi.verifyDeveloper(developerId);
      setVerificationMap((prev) => ({ ...prev, ...mergeVerificationResults(response.results) }));
      toast.success(`Developer verification complete (${response.verified_count}/${response.total_count})`);
    } catch (err) {
      toast.error(err.message || 'Developer verification failed');
    } finally {
      setBusyKey('');
    }
  };

  const verifyAll = async () => {
    try {
      setBusyKey('verify-all');
      const response = await registryApi.verifyAll();
      setVerificationMap(mergeVerificationResults(response.results));
      toast.success(`Registry verification complete (${response.verified_count}/${response.total_count})`);
    } catch (err) {
      toast.error(err.message || 'Registry verification failed');
    } finally {
      setBusyKey('');
    }
  };

  if (loading) {
    return (
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-4 text-sm text-zinc-400">
        <div className="flex items-center gap-2"><Loader2 size={14} className="animate-spin text-emerald-400" /> Loading registry…</div>
      </div>
    );
  }

  return (
    <section className="space-y-4" data-testid="registry-manager">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-zinc-100">Registry tree</h2>
            <p className="mt-1 text-xs text-zinc-500">Provider key nodes with collapsible model branches, validation, instantiation, and default request JSON.</p>
          </div>
          <button onClick={verifyAll} disabled={busyKey === 'verify-all'} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 hover:border-zinc-700 hover:text-white disabled:opacity-60">
            <span className="flex items-center gap-2">{busyKey === 'verify-all' ? <Loader2 size={13} className="animate-spin" /> : <ShieldCheck size={13} />} Verify entire registry</span>
          </button>
        </div>
        <div className="mt-3 rounded-2xl border border-zinc-800 bg-zinc-950/70 p-3 text-xs text-zinc-400">
          Free-tier safe mode is enabled by default: single-model verification uses a strict tiny probe, while developer/full-registry checks prefer low-cost listing/provider checks when available.
          <div className="mt-2 text-blue-200">OpenAI, Anthropic, and Google are now curated to only show models confirmed to work with the universal key.</div>
          {verificationSummary.total > 0 && <div className="mt-2 text-zinc-300">Verified {verificationSummary.verified} / {verificationSummary.total} tracked models.</div>}
        </div>
        {error && (
          <div className="mt-3 rounded-2xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">
            <div className="flex items-start gap-2"><AlertCircle size={14} className="mt-0.5" /> <span>{error}</span></div>
            <button onClick={() => fetchRegistry()} className="mt-2 rounded bg-amber-500/20 px-3 py-1.5 text-xs text-amber-100 hover:bg-amber-500/30">Retry registry load</button>
          </div>
        )}
      </div>

      <div className="space-y-4">
        {registry.map((developer) => (
          <RegistryTreeNode
            key={developer.developer_id}
            developer={developer}
            keyStatus={keyMap[developer.developer_id]}
            defaultsNode={defaultsMap[developer.developer_id]}
            verificationMap={verificationMap}
            busyKey={busyKey}
            onAddModel={addModelPrompt}
            onRemoveModel={removeModel}
            onInstantiateModel={instantiateModel}
            onVerifyModel={verifyModel}
            onVerifyDeveloper={verifyDeveloper}
            onRemoveDeveloper={removeDeveloper}
          />
        ))}
      </div>

      {addingDev ? (
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
          <div className="text-sm font-medium text-zinc-200">Add developer</div>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <input value={newDev.developer_id} onChange={(event) => setNewDev((prev) => ({ ...prev, developer_id: event.target.value }))} placeholder="developer-id"
              className="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50" />
            <input value={newDev.name} onChange={(event) => setNewDev((prev) => ({ ...prev, name: event.target.value }))} placeholder="Display name"
              className="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50" />
            <input value={newDev.base_url} onChange={(event) => setNewDev((prev) => ({ ...prev, base_url: event.target.value }))} placeholder="Base URL"
              className="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50 md:col-span-2" />
            <input value={newDev.website} onChange={(event) => setNewDev((prev) => ({ ...prev, website: event.target.value }))} placeholder="Website (optional)"
              className="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50 md:col-span-2" />
          </div>
          <div className="mt-3 flex gap-2">
            <button onClick={addDeveloper} disabled={busyKey === 'add-developer'} className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-60">Add developer</button>
            <button onClick={() => setAddingDev(false)} className="text-sm text-zinc-500 hover:text-zinc-300">Cancel</button>
          </div>
        </div>
      ) : (
        <button onClick={() => setAddingDev(true)} className="inline-flex items-center gap-2 rounded-xl border border-zinc-800 px-4 py-2 text-sm text-zinc-300 hover:border-zinc-700 hover:text-white">
          <Plus size={14} /> Add developer
        </button>
      )}
    </section>
  );
}
