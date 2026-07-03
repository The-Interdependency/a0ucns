import React, { useMemo, useState } from 'react';
import { Archive, CheckCheck, Clock3, Edit3, Plus, RotateCcw, ScrollText, Trash2 } from 'lucide-react';
import { ROLE_PRESET_OPTIONS } from './hubConfig';

const emptyForm = {
  name: '',
  model_id: '',
  role_preset: '',
  role: '',
  system_message: '',
  prompt_modifier: '',
  instance_prompt: '',
  history_window_messages: 12,
};

function normalizePayload(form) {
  return {
    name: form.name.trim(),
    model_id: form.model_id,
    role_preset: form.role_preset || null,
    history_window_messages: Number(form.history_window_messages) || 0,
    instance_prompt: form.instance_prompt || null,
    context: {
      role: form.role || null,
      system_message: form.system_message || null,
      prompt_modifier: form.prompt_modifier || null,
    },
  };
}

export function HubInstancesPanel({
  modelOptions,
  instances,
  includeArchived,
  setIncludeArchived,
  onCreate,
  onUpdate,
  onToggleArchive,
  onDeleteArchived,
  onArchiveMany,
  onRestoreMany,
  onDeleteMany,
  onFetchHistory,
  busyKey,
}) {
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState('');
  const [historyMap, setHistoryMap] = useState({});
  const [selectedInstanceIds, setSelectedInstanceIds] = useState([]);

  const activeInstances = useMemo(() => instances, [instances]);
  const allVisibleSelected = activeInstances.length > 0 && selectedInstanceIds.length === activeInstances.length;
  const selectedActiveIds = selectedInstanceIds.filter((instanceId) => {
    const instance = activeInstances.find((item) => item.instance_id === instanceId);
    return instance && !instance.archived;
  });
  const selectedArchivedIds = selectedInstanceIds.filter((instanceId) => {
    const instance = activeInstances.find((item) => item.instance_id === instanceId);
    return instance?.archived;
  });

  const submit = async (event) => {
    event.preventDefault();
    const payload = normalizePayload(form);
    if (!payload.name || !payload.model_id) return;
    if (editingId) await onUpdate(editingId, payload);
    else await onCreate(payload);
    setForm(emptyForm);
    setEditingId('');
  };

  const startEdit = (instance) => {
    setEditingId(instance.instance_id);
    setForm({
      name: instance.name || '',
      model_id: instance.model_id || '',
      role_preset: instance.role_preset || '',
      role: instance.context?.role || '',
      system_message: instance.context?.system_message || '',
      prompt_modifier: instance.context?.prompt_modifier || '',
      instance_prompt: instance.instance_prompt || '',
      history_window_messages: instance.history_window_messages ?? 12,
    });
  };

  const loadHistory = async (instanceId) => {
    const history = await onFetchHistory(instanceId);
    setHistoryMap((prev) => ({ ...prev, [instanceId]: history }));
  };

  React.useEffect(() => {
    setSelectedInstanceIds((prev) => prev.filter((instanceId) => activeInstances.some((item) => item.instance_id === instanceId)));
  }, [activeInstances]);

  const toggleInstanceSelected = (instanceId) => {
    setSelectedInstanceIds((prev) => prev.includes(instanceId)
      ? prev.filter((item) => item !== instanceId)
      : [...prev, instanceId]);
  };

  const toggleSelectAllVisible = () => {
    setSelectedInstanceIds(allVisibleSelected ? [] : activeInstances.map((instance) => instance.instance_id));
  };

  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-925/60 bg-zinc-900/60 p-4 shadow-[0_0_0_1px_rgba(255,255,255,0.02)]" data-testid="hub-instances-panel">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-zinc-100">Instances</h2>
          <p className="text-xs text-zinc-500">Single model, many isolated personas. Each instance keeps its own thread, prompt, and archive state.</p>
        </div>
        <label className="flex items-center gap-2 text-xs text-zinc-400">
          <input type="checkbox" checked={includeArchived} onChange={(e) => setIncludeArchived(e.target.checked)} data-testid="show-archived-instances-checkbox" /> Show archived
        </label>
        <button
          type="button"
          onClick={toggleSelectAllVisible}
          className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 transition hover:border-zinc-700 hover:text-white"
          data-testid="instances-select-all-button"
        >
          <span className="flex items-center gap-2"><CheckCheck size={13} /> {allVisibleSelected ? 'Clear selected' : 'Select all instances'}</span>
        </button>
      </div>

      {selectedInstanceIds.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-950/70 p-3 text-xs text-zinc-300" data-testid="instances-bulk-actions">
          <span data-testid="instances-selected-count">{selectedInstanceIds.length} selected</span>
          <button
            type="button"
            onClick={() => onArchiveMany(selectedActiveIds)}
            disabled={selectedActiveIds.length === 0}
            className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 disabled:opacity-40"
            data-testid="instances-bulk-archive-button"
          >
            Archive selected
          </button>
          <button
            type="button"
            onClick={() => onRestoreMany(selectedArchivedIds)}
            disabled={selectedArchivedIds.length === 0}
            className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 disabled:opacity-40"
            data-testid="instances-bulk-restore-button"
          >
            Undo archive selected
          </button>
          <button
            type="button"
            onClick={() => onDeleteMany(selectedArchivedIds)}
            disabled={selectedArchivedIds.length === 0}
            className="rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-200 disabled:opacity-40"
            data-testid="instances-bulk-delete-button"
          >
            Delete archived selected
          </button>
        </div>
      )}

      <form onSubmit={submit} className="mt-4 space-y-3 rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4" data-testid="instance-form">
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-sm font-medium text-zinc-200">{editingId ? 'Edit instance' : 'Create instance'}</h3>
          {editingId && (
            <button type="button" onClick={() => { setEditingId(''); setForm(emptyForm); }} className="text-xs text-zinc-500 hover:text-zinc-300" data-testid="cancel-instance-edit-button">
              Cancel edit
            </button>
          )}
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <input value={form.name} onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))} placeholder="Instance name"
            data-testid="instance-name-input"
            className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50" />
          <select value={form.model_id} onChange={(e) => setForm((prev) => ({ ...prev, model_id: e.target.value }))}
            data-testid="instance-model-select"
            className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50">
            <option value="">Choose model</option>
            {modelOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
          <input list="hub-role-presets" value={form.role_preset} onChange={(e) => setForm((prev) => ({ ...prev, role_preset: e.target.value }))}
            placeholder="Role preset (optional)"
            className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50" />
          <input value={form.role} onChange={(e) => setForm((prev) => ({ ...prev, role: e.target.value }))} placeholder="Private role"
            className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50" />
          <input value={form.system_message} onChange={(e) => setForm((prev) => ({ ...prev, system_message: e.target.value }))} placeholder="System message"
            className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50 sm:col-span-2" />
          <input value={form.prompt_modifier} onChange={(e) => setForm((prev) => ({ ...prev, prompt_modifier: e.target.value }))} placeholder="Prompt modifier"
            className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50 sm:col-span-2" />
          <textarea value={form.instance_prompt} onChange={(e) => setForm((prev) => ({ ...prev, instance_prompt: e.target.value }))} rows={3} placeholder="Persistent instance prompt"
            className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50 sm:col-span-2" />
          <input type="number" min={0} max={100} value={form.history_window_messages} onChange={(e) => setForm((prev) => ({ ...prev, history_window_messages: e.target.value }))}
            placeholder="History window"
            className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50" />
        </div>
        <datalist id="hub-role-presets">
          {ROLE_PRESET_OPTIONS.map((preset) => <option key={preset} value={preset} />)}
        </datalist>
        <button type="submit" disabled={busyKey === 'create-instance' || busyKey.startsWith('update-instance-')}
          data-testid="create-instance-button"
          className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-500 disabled:opacity-60">
          <Plus size={14} /> {editingId ? 'Save instance' : 'Create instance'}
        </button>
      </form>

      <div className="mt-4 space-y-3">
        {activeInstances.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-zinc-800 p-6 text-sm text-zinc-500">No instances yet. Create the first isolated model worker above.</div>
        ) : activeInstances.map((instance) => {
          const history = historyMap[instance.instance_id];
          return (
            <article key={instance.instance_id} className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4" data-testid={`instance-card-${instance.instance_id}`}>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <label className="inline-flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900 px-2 py-0.5 text-[11px] text-zinc-300" data-testid={`instance-select-control-${instance.instance_id}`}>
                      <input
                        type="checkbox"
                        checked={selectedInstanceIds.includes(instance.instance_id)}
                        onChange={() => toggleInstanceSelected(instance.instance_id)}
                        data-testid={`instance-select-checkbox-${instance.instance_id}`}
                      />
                      Select
                    </label>
                    <h3 className="text-sm font-semibold text-zinc-100">{instance.name}</h3>
                    <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] text-emerald-300">{instance.model_id}</span>
                    {instance.archived && <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[11px] text-amber-300">Archived</span>}
                  </div>
                  <div className="space-y-1 text-xs text-zinc-500">
                    <div>Instance ID: <span className="text-zinc-300">{instance.instance_id}</span></div>
                    <div>Thread ID: <span className="text-zinc-300">{instance.thread_id}</span></div>
                    <div>History window: <span className="text-zinc-300">{instance.history_window_messages}</span></div>
                  </div>
                  {(instance.instance_prompt || instance.context?.system_message || instance.context?.prompt_modifier) && (
                    <div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-3 text-xs text-zinc-400">
                      {instance.instance_prompt && <p><span className="text-zinc-200">Prompt:</span> {instance.instance_prompt}</p>}
                      {instance.context?.system_message && <p className="mt-1"><span className="text-zinc-200">System:</span> {instance.context.system_message}</p>}
                      {instance.context?.prompt_modifier && <p className="mt-1"><span className="text-zinc-200">Modifier:</span> {instance.context.prompt_modifier}</p>}
                    </div>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  <button type="button" onClick={() => startEdit(instance)} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 transition hover:border-zinc-700 hover:text-white" data-testid={`edit-instance-button-${instance.instance_id}`}>
                    <span className="flex items-center gap-2"><Edit3 size={13} /> Edit</span>
                  </button>
                  <button type="button" onClick={() => loadHistory(instance.instance_id)} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 transition hover:border-zinc-700 hover:text-white" data-testid={`instance-history-button-${instance.instance_id}`}>
                    <span className="flex items-center gap-2"><ScrollText size={13} /> History</span>
                  </button>
                  {instance.archived ? (
                    <>
                      <button type="button" onClick={() => onToggleArchive(instance)} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 transition hover:border-zinc-700 hover:text-white" data-testid={`toggle-instance-archive-button-${instance.instance_id}`}>
                        <span className="flex items-center gap-2"><RotateCcw size={13} /> Undo archive</span>
                      </button>
                      <button type="button" onClick={() => onDeleteArchived(instance.instance_id)} className="rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-200 transition hover:bg-red-500/20" data-testid={`delete-instance-button-${instance.instance_id}`}>
                        <span className="flex items-center gap-2"><Trash2 size={13} /> Delete</span>
                      </button>
                    </>
                  ) : (
                    <button type="button" onClick={() => onToggleArchive(instance)} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 transition hover:border-zinc-700 hover:text-white" data-testid={`toggle-instance-archive-button-${instance.instance_id}`}>
                      <span className="flex items-center gap-2"><Archive size={13} /> Archive</span>
                    </button>
                  )}
                </div>
              </div>
              {history && (
                <div className="mt-4 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-3">
                  <div className="mb-2 flex items-center gap-2 text-xs text-zinc-400"><Clock3 size={12} /> Private thread history ({history.messages.length})</div>
                  <div className="space-y-2">
                    {history.messages.length === 0 ? <div className="text-xs text-zinc-500">No history yet.</div> : history.messages.slice(-6).map((message) => (
                      <div key={message.message_id} className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-3 text-xs text-zinc-300" data-testid={`instance-history-message-${message.message_id}`}>
                        <div className="mb-1 flex flex-wrap items-center gap-2 text-[11px] text-zinc-500">
                          <span>{message.role}</span>
                          {message.hub_pattern && <span>{message.hub_pattern}</span>}
                          {message.hub_role && <span>{message.hub_role}</span>}
                          {message.hub_prompt_id && <span>{message.hub_prompt_id}</span>}
                          {message.hub_synthesis_batch_id && <span>{message.hub_synthesis_batch_id}</span>}
                        </div>
                        <div className="whitespace-pre-wrap">{message.content}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}
