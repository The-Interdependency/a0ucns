import React, { useMemo, useState } from 'react';
import { Archive, Boxes, Edit3, Plus, RotateCcw } from 'lucide-react';

const emptyForm = {
  name: '',
  description: '',
  members: [],
};

function buildMemberKey(item) {
  return `${item.member_type}:${item.member_id}`;
}

export function HubGroupsPanel({
  instances,
  groups,
  includeArchived,
  setIncludeArchived,
  onCreate,
  onUpdate,
  onToggleArchive,
  busyKey,
}) {
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState('');

  const selectableMembers = useMemo(() => ([
    ...instances.filter((item) => !item.archived).map((item) => ({
      member_type: 'instance',
      member_id: item.instance_id,
      label: `${item.name} · ${item.model_id}`,
    })),
    ...groups.filter((item) => !item.archived && item.group_id !== editingId).map((item) => ({
      member_type: 'group',
      member_id: item.group_id,
      label: `${item.name} · nested group`,
    })),
  ]), [editingId, groups, instances]);

  const toggleMember = (option) => {
    const key = buildMemberKey(option);
    setForm((prev) => {
      const exists = prev.members.some((item) => buildMemberKey(item) === key);
      return {
        ...prev,
        members: exists ? prev.members.filter((item) => buildMemberKey(item) !== key) : [...prev.members, option],
      };
    });
  };

  const submit = async (event) => {
    event.preventDefault();
    const payload = {
      name: form.name.trim(),
      description: form.description || null,
      members: form.members,
    };
    if (!payload.name) return;
    if (editingId) await onUpdate(editingId, payload);
    else await onCreate(payload);
    setEditingId('');
    setForm(emptyForm);
  };

  const startEdit = (group) => {
    setEditingId(group.group_id);
    setForm({
      name: group.name || '',
      description: group.description || '',
      members: group.members || [],
    });
  };

  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4" data-testid="hub-groups-panel">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-zinc-100">Groups</h2>
          <p className="text-xs text-zinc-500">Build nested orchestration trees by combining instances and groups recursively.</p>
        </div>
        <label className="flex items-center gap-2 text-xs text-zinc-400">
          <input type="checkbox" checked={includeArchived} onChange={(e) => setIncludeArchived(e.target.checked)} data-testid="show-archived-groups-checkbox" /> Show archived
        </label>
      </div>

      <form onSubmit={submit} className="mt-4 space-y-3 rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4" data-testid="group-form">
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-sm font-medium text-zinc-200">{editingId ? 'Edit group' : 'Create group'}</h3>
          {editingId && <button type="button" onClick={() => { setEditingId(''); setForm(emptyForm); }} className="text-xs text-zinc-500 hover:text-zinc-300" data-testid="cancel-group-edit-button">Cancel edit</button>}
        </div>
        <input value={form.name} onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))} placeholder="Group name"
          data-testid="group-name-input"
          className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50" />
        <textarea value={form.description} onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))} rows={2} placeholder="Describe what this nested cluster is for"
          data-testid="group-description-textarea"
          className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50" />

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-3" data-testid="group-member-selector">
          <div className="mb-2 text-xs font-medium text-zinc-300">Members</div>
          <div className="grid gap-2 sm:grid-cols-2">
            {selectableMembers.length === 0 ? <div className="text-xs text-zinc-500">Create instances first.</div> : selectableMembers.map((option) => {
              const checked = form.members.some((item) => buildMemberKey(item) === buildMemberKey(option));
              return (
                <label key={buildMemberKey(option)} className="flex items-start gap-2 rounded-xl border border-zinc-800 bg-zinc-950/70 px-3 py-2 text-xs text-zinc-300" data-testid={`group-member-option-${option.member_type}-${option.member_id}`}>
                  <input type="checkbox" checked={checked} onChange={() => toggleMember(option)} className="mt-0.5" data-testid={`group-member-checkbox-${option.member_type}-${option.member_id}`} />
                  <span>{option.label}</span>
                </label>
              );
            })}
          </div>
        </div>

        <button type="submit" disabled={busyKey === 'create-group' || busyKey.startsWith('update-group-')}
          data-testid="create-group-button"
          className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-500 disabled:opacity-60">
          <Plus size={14} /> {editingId ? 'Save group' : 'Create group'}
        </button>
      </form>

      <div className="mt-4 space-y-3">
        {groups.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-zinc-800 p-6 text-sm text-zinc-500">No groups yet. Build a nested orchestration cluster here.</div>
        ) : groups.map((group) => (
          <article key={group.group_id} className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4" data-testid={`group-card-${group.group_id}`}>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-sm font-semibold text-zinc-100">{group.name}</h3>
                  <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2 py-0.5 text-[11px] text-sky-300">{group.members.length} members</span>
                  {group.archived && <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[11px] text-amber-300">Archived</span>}
                </div>
                <p className="mt-2 text-xs text-zinc-500">{group.description || 'No description yet.'}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {group.members.map((member) => (
                    <span key={buildMemberKey(member)} className="rounded-full border border-zinc-800 bg-zinc-900/70 px-2 py-1 text-[11px] text-zinc-400">
                      {member.member_type} · {member.member_id}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={() => startEdit(group)} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 transition hover:border-zinc-700 hover:text-white" data-testid={`edit-group-button-${group.group_id}`}>
                  <span className="flex items-center gap-2"><Edit3 size={13} /> Edit</span>
                </button>
                <button type="button" onClick={() => onToggleArchive(group)} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 transition hover:border-zinc-700 hover:text-white" data-testid={`toggle-group-archive-button-${group.group_id}`}>
                  <span className="flex items-center gap-2">{group.archived ? <RotateCcw size={13} /> : <Archive size={13} />} {group.archived ? 'Restore' : 'Archive'}</span>
                </button>
              </div>
            </div>
            <div className="mt-4 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-3 text-xs text-zinc-400">
              <div className="mb-2 flex items-center gap-2 text-zinc-300"><Boxes size={13} /> Nested structure</div>
              <div className="space-y-1">
                {group.members.length === 0 ? <div>No members.</div> : group.members.map((member) => <div key={buildMemberKey(member)}>{member.member_type}: {member.member_id}</div>)}
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
