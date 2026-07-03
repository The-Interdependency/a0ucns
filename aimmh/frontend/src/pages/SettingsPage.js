import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Key, Plus, Trash2, Shield, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function KeyManager() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editDev, setEditDev] = useState(null);
  const [editKey, setEditKey] = useState('');

  const fetchKeys = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/v1/keys`);
      setKeys(res.data || []);
    } catch (err) {
      console.error('Failed to fetch keys:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchKeys(); }, [fetchKeys]);

  const handleSave = async (developerId) => {
    try {
      await axios.post(`${API}/v1/keys`, { developer_id: developerId, api_key: editKey });
      setEditDev(null);
      setEditKey('');
      fetchKeys();
    } catch (err) {
      console.error('Failed to save key:', err);
    }
  };

  const handleRemove = async (developerId) => {
    try {
      await axios.delete(`${API}/v1/keys/${developerId}`);
      fetchKeys();
    } catch (err) {
      console.error('Failed to remove key:', err);
    }
  };

  if (loading) return <div className="text-zinc-500 text-sm">Loading keys...</div>;

  return (
    <div className="space-y-3" data-testid="key-manager">
      {keys.map(k => (
        <div key={k.developer_id} className="flex items-center justify-between p-3 rounded-lg border border-zinc-800 bg-zinc-900/40">
          <div className="flex items-center gap-3">
            <Key size={16} className="text-zinc-500" />
            <div>
              <div className="text-sm font-medium text-zinc-200">{k.developer_id}</div>
              <div className="flex items-center gap-1.5 mt-0.5">
                {k.status === 'configured' && (
                  <span className="flex items-center gap-1 text-xs text-emerald-400">
                    <CheckCircle size={10} /> {k.masked_key}
                  </span>
                )}
                {k.status === 'universal' && (
                  <span className="flex items-center gap-1 text-xs text-blue-400">
                    <Shield size={10} /> Universal Key
                  </span>
                )}
                {k.status === 'missing' && (
                  <span className="flex items-center gap-1 text-xs text-amber-400">
                    <AlertCircle size={10} /> Not configured
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {editDev === k.developer_id ? (
              <div className="flex items-center gap-2">
                <input
                  type="password"
                  value={editKey}
                  onChange={e => setEditKey(e.target.value)}
                  placeholder="API key"
                  className="rounded bg-zinc-800 border border-zinc-700 px-2 py-1 text-xs text-zinc-200 w-48 focus:outline-none focus:border-emerald-500/50"
                  data-testid={`key-input-${k.developer_id}`}
                />
                <button
                  onClick={() => handleSave(k.developer_id)}
                  className="px-2 py-1 rounded bg-emerald-600 text-xs text-white hover:bg-emerald-500"
                  data-testid={`save-key-${k.developer_id}`}
                >
                  Save
                </button>
                <button
                  onClick={() => { setEditDev(null); setEditKey(''); }}
                  className="text-xs text-zinc-500 hover:text-zinc-300"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setEditDev(k.developer_id)}
                  className="px-2 py-1 rounded text-xs border border-zinc-700 text-zinc-400 hover:text-zinc-200 hover:border-zinc-600"
                  data-testid={`edit-key-${k.developer_id}`}
                >
                  {k.status === 'missing' ? 'Add Key' : 'Change'}
                </button>
                {k.status === 'configured' && (
                  <button
                    onClick={() => handleRemove(k.developer_id)}
                    className="p-1 rounded text-zinc-500 hover:text-red-400"
                    data-testid={`remove-key-${k.developer_id}`}
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function RegistryManager() {
  const [registry, setRegistry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [addingDev, setAddingDev] = useState(false);
  const [newDev, setNewDev] = useState({ developer_id: '', name: '', base_url: '' });
  const [addingModel, setAddingModel] = useState(null);
  const [newModel, setNewModel] = useState('');

  const fetchRegistry = useCallback(async (showLoader = true) => {
    if (showLoader) setLoading(true);
    setError('');
    try {
      const res = await axios.get(`${API}/v1/registry`);
      setRegistry(res.data.developers || []);
    } catch (err) {
      console.error('Failed to fetch registry:', err);
      setRegistry([]);
      if (err.response?.status === 401) {
        setError('Your session expired while loading the registry. Please sign in again and retry.');
      } else {
        setError(err.response?.data?.detail || 'Could not load the model registry from the backend.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchRegistry(); }, [fetchRegistry]);

  const handleAddDev = async () => {
    if (!newDev.developer_id || !newDev.name || !newDev.base_url) return;
    try {
      await axios.post(`${API}/v1/registry/developer`, {
        developer_id: newDev.developer_id,
        name: newDev.name,
        auth_type: 'openai_compatible',
        base_url: newDev.base_url,
        models: [],
      });
      setAddingDev(false);
      setNewDev({ developer_id: '', name: '', base_url: '' });
      await fetchRegistry(false);
    } catch (err) {
      console.error('Failed to add developer:', err);
      setError(err.response?.data?.detail || 'Failed to add developer.');
    }
  };

  const handleAddModel = async (devId) => {
    if (!newModel.trim()) return;
    try {
      await axios.post(`${API}/v1/registry/developer/${devId}/model`, {
        model_id: newModel.trim(),
      });
      setAddingModel(null);
      setNewModel('');
      await fetchRegistry(false);
    } catch (err) {
      console.error('Failed to add model:', err);
      setError(err.response?.data?.detail || 'Failed to add model.');
    }
  };

  const handleRemoveModel = async (devId, modelId) => {
    try {
      await axios.delete(`${API}/v1/registry/developer/${devId}/model/${modelId}`);
      await fetchRegistry(false);
    } catch (err) {
      console.error('Failed to remove model:', err);
      setError(err.response?.data?.detail || 'Failed to remove model.');
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4 text-sm text-zinc-400" data-testid="registry-loading-state">
        <div className="flex items-center gap-2"><Loader2 size={14} className="animate-spin text-emerald-400" /> Loading registry...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="registry-manager">
      {error && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-200" data-testid="registry-error-state">
          <div className="flex items-start gap-2">
            <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
            <div className="space-y-2">
              <div className="font-medium">Registry load issue</div>
              <div className="text-xs text-amber-100/90">{error}</div>
              <button onClick={() => fetchRegistry()} className="rounded bg-amber-500/20 px-3 py-1.5 text-xs text-amber-100 hover:bg-amber-500/30" data-testid="retry-registry-btn">
                Retry registry load
              </button>
            </div>
          </div>
        </div>
      )}

      {registry && registry.length === 0 && !error && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4 text-sm text-zinc-400" data-testid="registry-empty-state">
          <div className="font-medium text-zinc-200">No developers in this registry yet</div>
          <div className="mt-1 text-xs text-zinc-500">The default registry should normally seed automatically. If this page was blank a moment ago, tap retry before adding developers manually.</div>
          <button onClick={() => fetchRegistry()} className="mt-3 rounded border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300 hover:border-zinc-600 hover:text-zinc-100" data-testid="retry-empty-registry-btn">
            Retry
          </button>
        </div>
      )}
      {registry && registry.map(dev => (
        <div key={dev.developer_id} className="rounded-lg border border-zinc-800 bg-zinc-900/40 overflow-hidden">
          <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-zinc-200">{dev.name}</div>
              <div className="text-xs text-zinc-500">{dev.auth_type} {dev.base_url ? `| ${dev.base_url}` : ''}</div>
            </div>
          </div>
          <div className="p-3 space-y-1">
            {dev.models.map(m => (
              <div key={m.model_id} className="flex items-center justify-between px-2 py-1 rounded hover:bg-zinc-800/40">
                <span className="text-sm text-zinc-300">{m.display_name || m.model_id}</span>
                <button
                  onClick={() => handleRemoveModel(dev.developer_id, m.model_id)}
                  className="text-zinc-600 hover:text-red-400"
                  data-testid={`remove-model-${m.model_id}`}
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
            {addingModel === dev.developer_id ? (
              <div className="flex items-center gap-2 mt-2">
                <input
                  value={newModel}
                  onChange={e => setNewModel(e.target.value)}
                  placeholder="model-id"
                  className="flex-1 rounded bg-zinc-800 border border-zinc-700 px-2 py-1 text-xs text-zinc-200 focus:outline-none focus:border-emerald-500/50"
                  data-testid={`new-model-input-${dev.developer_id}`}
                />
                <button
                  onClick={() => handleAddModel(dev.developer_id)}
                  className="px-2 py-1 rounded bg-emerald-600 text-xs text-white"
                >
                  Add
                </button>
                <button onClick={() => setAddingModel(null)} className="text-xs text-zinc-500">Cancel</button>
              </div>
            ) : (
              <button
                onClick={() => setAddingModel(dev.developer_id)}
                className="flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300 mt-1 px-2"
                data-testid={`add-model-btn-${dev.developer_id}`}
              >
                <Plus size={12} /> Add Model
              </button>
            )}
          </div>
        </div>
      ))}

      {addingDev ? (
        <div className="rounded-lg border border-zinc-800 p-4 space-y-3">
          <div className="text-sm font-medium text-zinc-200">Add Developer</div>
          <input
            value={newDev.developer_id}
            onChange={e => setNewDev(p => ({ ...p, developer_id: e.target.value }))}
            placeholder="developer-id (e.g., mistral)"
            className="w-full rounded bg-zinc-800 border border-zinc-700 px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-emerald-500/50"
          />
          <input
            value={newDev.name}
            onChange={e => setNewDev(p => ({ ...p, name: e.target.value }))}
            placeholder="Display Name (e.g., Mistral AI)"
            className="w-full rounded bg-zinc-800 border border-zinc-700 px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-emerald-500/50"
          />
          <input
            value={newDev.base_url}
            onChange={e => setNewDev(p => ({ ...p, base_url: e.target.value }))}
            placeholder="Base URL (e.g., https://api.mistral.ai/v1)"
            className="w-full rounded bg-zinc-800 border border-zinc-700 px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-emerald-500/50"
          />
          <div className="flex gap-2">
            <button onClick={handleAddDev} className="px-3 py-1.5 rounded bg-emerald-600 text-sm text-white hover:bg-emerald-500">Add</button>
            <button onClick={() => setAddingDev(false)} className="px-3 py-1.5 text-sm text-zinc-500 hover:text-zinc-300">Cancel</button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setAddingDev(true)}
          className="flex items-center gap-1.5 text-sm text-zinc-400 hover:text-zinc-200"
          data-testid="add-developer-btn"
        >
          <Plus size={14} /> Add Developer
        </button>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState('keys');

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-200" data-testid="settings-page">
      <header className="flex items-center gap-3 px-4 py-3 border-b border-zinc-800">
        <button onClick={() => navigate('/chat')} className="p-1.5 rounded hover:bg-zinc-800 text-zinc-400" data-testid="back-btn">
          <ArrowLeft size={18} />
        </button>
        <h1 className="text-base font-semibold">Settings</h1>
      </header>
      <div className="max-w-2xl mx-auto p-4 space-y-6">
        <div className="flex gap-1 border-b border-zinc-800 pb-1">
          <button
            onClick={() => setTab('keys')}
            className={`px-4 py-2 text-sm rounded-t transition-colors ${tab === 'keys' ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300'}`}
            data-testid="tab-keys"
          >
            API Keys
          </button>
          <button
            onClick={() => setTab('registry')}
            className={`px-4 py-2 text-sm rounded-t transition-colors ${tab === 'registry' ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300'}`}
            data-testid="tab-registry"
          >
            Model Registry
          </button>
        </div>

        {tab === 'keys' && (
          <div className="space-y-4">
            <div className="text-sm text-zinc-400">
              Emergent-supported models (OpenAI, Anthropic, Google) use the universal key by default.
              Add your own keys for custom providers (xAI, DeepSeek, Perplexity) or to override defaults.
            </div>
            <KeyManager />
          </div>
        )}

        {tab === 'registry' && (
          <div className="space-y-4">
            <div className="text-sm text-zinc-400">
              Manage available model developers and their models. Add any OpenAI-compatible API provider.
            </div>
            <RegistryManager />
          </div>
        )}
      </div>
    </div>
  );
}
