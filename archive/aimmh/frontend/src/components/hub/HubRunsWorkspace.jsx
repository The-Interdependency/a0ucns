import React from 'react';
import { Archive, Layers3, MessageSquareText, RotateCcw, Trash2 } from 'lucide-react';
import { HubRunBuilder } from './HubRunBuilder';

export function HubRunsWorkspace({
  sourceOptions,
  instanceOptions,
  onRun,
  busyKey,
  runs,
  selectedRunId,
  setSelectedRunId,
  includeArchivedRuns,
  setIncludeArchivedRuns,
  onToggleRunArchive,
  onDeleteArchivedRun,
}) {
  return (
    <div className="space-y-4" data-testid="hub-runs-workspace">
      <HubRunBuilder sourceOptions={sourceOptions} instanceOptions={instanceOptions} onRun={onRun} busyKey={busyKey} />
      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4" data-testid="hub-run-inventory-section">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-zinc-100"><Layers3 size={16} /> <h2 className="text-base font-semibold">Run inventory</h2></div>
            <p className="mt-1 text-xs text-zinc-500">Rooms, run orders, prompt chains, and saved results stay visible here for quick mobile switching.</p>
          </div>
          <label className="flex items-center gap-2 text-xs text-zinc-400">
            <input type="checkbox" checked={includeArchivedRuns} onChange={(event) => setIncludeArchivedRuns(event.target.checked)} data-testid="show-archived-runs-checkbox" /> Show archived
          </label>
        </div>
        <div className="mt-4 space-y-3">
          {runs.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-zinc-800 p-5 text-sm text-zinc-500">No runs yet. Build a room, define prompt order, then execute a pipeline.</div>
          ) : runs.map((run) => (
            <article key={run.run_id} className={`w-full rounded-2xl border p-4 transition ${selectedRunId === run.run_id ? 'border-emerald-500/40 bg-emerald-500/10' : 'border-zinc-800 bg-zinc-950/60 hover:border-zinc-700'}`} data-testid={`run-card-${run.run_id}`}>
              <button type="button" onClick={() => setSelectedRunId(run.run_id)} className="w-full text-left" data-testid={`select-run-button-${run.run_id}`}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="text-sm font-medium text-zinc-100">{run.label || run.run_id}</div>
                      {run.archived && <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-300">Archived</span>}
                    </div>
                    <div className="mt-1 text-xs text-zinc-500">{run.stage_summaries?.length || 0} stages · {run.status}</div>
                  </div>
                  <div className="rounded-full border border-zinc-800 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-400">
                    {run.updated_at?.slice(0, 16).replace('T', ' ')}
                  </div>
                </div>
                <div className="mt-3 flex items-center gap-2 text-xs text-zinc-400"><MessageSquareText size={12} /> {run.prompt}</div>
              </button>
              <div className="mt-4 flex flex-wrap gap-2">
                <button type="button" onClick={() => onToggleRunArchive(run)} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 hover:border-zinc-700 hover:text-white" data-testid={`toggle-run-archive-button-${run.run_id}`}>
                  <span className="flex items-center gap-2">{run.archived ? <RotateCcw size={13} /> : <Archive size={13} />} {run.archived ? 'Restore' : 'Archive'}</span>
                </button>
                {run.archived && (
                  <button type="button" onClick={() => onDeleteArchivedRun(run.run_id)} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 hover:border-red-500/30 hover:text-red-300" data-testid={`delete-archived-run-button-${run.run_id}`}>
                    <span className="flex items-center gap-2"><Trash2 size={13} /> Delete archived</span>
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
