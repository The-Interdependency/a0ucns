import React, { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle, Key, Shield, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { registryApi } from '../../lib/registryApi';

function statusMeta(status) {
  if (status === 'configured') return { label: 'Configured', className: 'text-emerald-400', icon: CheckCircle };
  if (status === 'universal') return { label: 'Universal Key', className: 'text-blue-400', icon: Shield };
  return { label: 'Missing', className: 'text-amber-400', icon: AlertCircle };
}

export function KeyManager({ compact = false }) {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editDev, setEditDev] = useState('');
  const [editKey, setEditKey] = useState('');

  const fetchKeys = async () => {
    try {
      setLoading(true);
      const data = await registryApi.getKeys();
      setKeys(data || []);
    } catch (error) {
      toast.error(error.message || 'Failed to load key statuses');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const saveKey = async (developerId) => {
    if (!editKey.trim()) return;
    try {
      await registryApi.setKey({ developer_id: developerId, api_key: editKey.trim() });
      toast.success(`Saved key for ${developerId}`);
      setEditDev('');
      setEditKey('');
      await fetchKeys();
    } catch (error) {
      toast.error(error.message || 'Failed to save key');
    }
  };

  const removeKey = async (developerId) => {
    try {
      await registryApi.removeKey(developerId);
      toast.success(`Removed key for ${developerId}`);
      await fetchKeys();
    } catch (error) {
      toast.error(error.message || 'Failed to remove key');
    }
  };

  if (loading) {
    return <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-4 text-sm text-zinc-500">Loading API key statuses…</div>;
  }

  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4" data-testid="key-manager">
      <div className="mb-3">
        <h2 className="text-base font-semibold text-zinc-100">API keys</h2>
        <p className="text-xs text-zinc-500">Provider credentials and universal-key fallback status.</p>
      </div>
      <div className="space-y-3">
        {keys.map((item) => {
          const meta = statusMeta(item.status);
          const Icon = meta.icon;
          return (
            <article key={item.developer_id} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-3">
              <div className={`flex flex-wrap items-center justify-between gap-3 ${compact ? '' : 'sm:flex-nowrap'}`}>
                <div className="flex min-w-0 items-start gap-3">
                  <Key size={16} className="mt-0.5 text-zinc-500" />
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-zinc-200">{item.developer_id}</div>
                    <div className={`mt-1 flex items-center gap-1 text-xs ${meta.className}`}>
                      <Icon size={11} /> {item.masked_key || meta.label}
                    </div>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {editDev === item.developer_id ? (
                    <>
                      <input
                        type="password"
                        value={editKey}
                        onChange={(event) => setEditKey(event.target.value)}
                        placeholder="Provider key"
                        className="w-44 rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-100 outline-none focus:border-emerald-500/50"
                      />
                      <button onClick={() => saveKey(item.developer_id)} className="rounded-xl bg-emerald-600 px-3 py-2 text-xs font-medium text-white hover:bg-emerald-500">Save</button>
                      <button onClick={() => { setEditDev(''); setEditKey(''); }} className="text-xs text-zinc-500 hover:text-zinc-300">Cancel</button>
                    </>
                  ) : (
                    <>
                      <button onClick={() => setEditDev(item.developer_id)} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 hover:border-zinc-700 hover:text-white">
                        {item.status === 'missing' ? 'Add key' : 'Change key'}
                      </button>
                      {item.status === 'configured' && (
                        <button onClick={() => removeKey(item.developer_id)} className="rounded-xl border border-zinc-800 p-2 text-zinc-500 hover:border-red-500/30 hover:text-red-300">
                          <Trash2 size={13} />
                        </button>
                      )}
                    </>
                  )}
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
