import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useHubWorkspace } from '../hooks/useHubWorkspace';
import { HubGroupsPanel } from '../components/hub/HubGroupsPanel';
import { HubHeader } from '../components/hub/HubHeader';
import { HubInstancesPanel } from '../components/hub/HubInstancesPanel';
import { HubRunBuilder } from '../components/hub/HubRunBuilder';
import { HubRunTimeline } from '../components/hub/HubRunTimeline';

export default function HubPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const workspace = useHubWorkspace();

  const instanceOptions = workspace.instances
    .filter((item) => !item.archived)
    .map((item) => ({ value: item.instance_id, label: `${item.name} · ${item.model_id}` }));

  if (workspace.loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100">
        <HubHeader onLogout={logout} onOpenSettings={() => navigate('/settings')} onExportInventory={workspace.exportInventory} />
        <div className="flex min-h-[70vh] items-center justify-center px-4">
          <div className="flex items-center gap-3 rounded-2xl border border-zinc-800 bg-zinc-900/60 px-5 py-4 text-sm text-zinc-400">
            <Loader2 size={16} className="animate-spin text-emerald-400" /> Loading AIMMH hub…
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <HubHeader onLogout={logout} onOpenSettings={() => navigate('/settings')} />

      <main className="mx-auto max-w-[1800px] px-4 py-4 sm:px-6 sm:py-6">
        <div className="grid gap-4 xl:grid-cols-[1.1fr_1fr_1.2fr]">
          <div className="space-y-4">
            <HubInstancesPanel
              modelOptions={workspace.modelOptions}
              instances={workspace.instances}
              includeArchived={workspace.includeArchivedInstances}
              setIncludeArchived={workspace.setIncludeArchivedInstances}
              onCreate={workspace.createInstance}
              onUpdate={workspace.updateInstance}
              onToggleArchive={workspace.toggleInstanceArchive}
              onFetchHistory={workspace.fetchInstanceHistory}
              busyKey={workspace.busyKey}
            />
          </div>

          <div className="space-y-4">
            <HubGroupsPanel
              instances={workspace.instances}
              groups={workspace.groups}
              includeArchived={workspace.includeArchivedGroups}
              setIncludeArchived={workspace.setIncludeArchivedGroups}
              onCreate={workspace.createGroup}
              onUpdate={workspace.updateGroup}
              onToggleArchive={workspace.toggleGroupArchive}
              busyKey={workspace.busyKey}
            />
            <HubRunBuilder
              sourceOptions={workspace.sourceOptions}
              instanceOptions={instanceOptions}
              onRun={workspace.createRun}
              busyKey={workspace.busyKey}
            />
          </div>

          <HubRunTimeline
            options={workspace.options}
            runs={workspace.runs}
            selectedRunId={workspace.selectedRunId}
            setSelectedRunId={workspace.setSelectedRunId}
            selectedRun={workspace.selectedRun}
          />
        </div>
      </main>
    </div>
  );
}
