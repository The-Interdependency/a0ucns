import React from 'react';
import { Layers3, Link2, Network, TerminalSquare } from 'lucide-react';

function groupResults(results = []) {
  return results.reduce((acc, result) => {
    const stageBucket = acc[result.stage_index] || { stageName: result.stage_name, pattern: result.pattern, items: [] };
    stageBucket.items.push(result);
    acc[result.stage_index] = stageBucket;
    return acc;
  }, {});
}

export function HubRunTimeline({ options, runs, selectedRunId, setSelectedRunId, selectedRun }) {
  const stageMap = groupResults(selectedRun?.results || []);

  return (
    <section className="space-y-4">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
        <div className="flex items-center gap-2 text-zinc-100"><TerminalSquare size={16} /> <h2 className="text-base font-semibold">FastAPI connections</h2></div>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          {Object.entries(options?.fastapi_connections || {}).map(([section, endpoints]) => (
            <div key={section} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-3">
              <div className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">{section}</div>
              <div className="space-y-1 text-xs text-zinc-300">
                {Object.entries(endpoints).map(([label, path]) => <div key={label}><span className="text-zinc-500">{label}</span>: {path}</div>)}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
        <div className="flex flex-wrap items-center gap-2 text-zinc-100"><Network size={16} /> <h2 className="text-base font-semibold">Runs</h2></div>
        <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {runs.length === 0 ? <div className="text-sm text-zinc-500">No runs yet.</div> : runs.map((run) => (
            <button key={run.run_id} onClick={() => setSelectedRunId(run.run_id)}
              className={`min-w-[220px] rounded-2xl border px-3 py-3 text-left transition ${selectedRunId === run.run_id ? 'border-emerald-500/40 bg-emerald-500/10 text-white' : 'border-zinc-800 bg-zinc-950/70 text-zinc-300 hover:border-zinc-700'}`}>
              <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">{run.status}</div>
              <div className="mt-1 text-sm font-medium">{run.label || run.run_id}</div>
              <div className="mt-2 text-xs text-zinc-500">{run.stage_summaries?.length || 0} stages</div>
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
        <div className="flex items-center gap-2 text-zinc-100"><Layers3 size={16} /> <h2 className="text-base font-semibold">Structured timeline</h2></div>
        {!selectedRun ? (
          <div className="mt-4 text-sm text-zinc-500">Select a run to inspect stage, round, step, role, and thread isolation.</div>
        ) : (
          <div className="mt-4 space-y-4">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
              <div className="flex flex-wrap items-center gap-3">
                <div>
                  <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">Run</div>
                  <div className="text-sm font-semibold text-zinc-100">{selectedRun.label || selectedRun.run_id}</div>
                </div>
                <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-[11px] text-emerald-300">{selectedRun.status}</span>
                <span className="rounded-full border border-zinc-800 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-400">{selectedRun.stage_summaries?.length || 0} stages</span>
              </div>
              <div className="mt-3 whitespace-pre-wrap text-sm text-zinc-300">{selectedRun.prompt}</div>
            </div>

            {(selectedRun.stage_summaries || []).map((summary) => {
              const items = stageMap[summary.stage_index]?.items || [];
              return (
                <div key={summary.stage_index} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">Stage {summary.stage_index + 1}</div>
                      <h3 className="mt-1 text-sm font-semibold text-zinc-100">{summary.stage_name || summary.pattern}</h3>
                      <p className="mt-2 text-xs text-zinc-500">{summary.pattern} · {summary.result_count} results</p>
                    </div>
                    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-xs text-zinc-400">
                      Participants: {(summary.participants || []).join(', ') || '—'}
                    </div>
                  </div>
                  <div className="mt-3 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-3 text-xs text-zinc-400">
                    <div className="mb-1 text-zinc-200">Prompt used</div>
                    <div className="whitespace-pre-wrap">{summary.prompt_used}</div>
                  </div>
                  <div className="mt-4 space-y-3">
                    {items.map((item) => (
                      <article key={item.run_step_id} className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-3">
                        <div className="flex flex-wrap items-center gap-2 text-[11px] text-zinc-500">
                          <span className="rounded-full border border-zinc-800 px-2 py-0.5">round {item.round_num + 1}</span>
                          <span className="rounded-full border border-zinc-800 px-2 py-0.5">step {item.step_num}</span>
                          <span className="rounded-full border border-zinc-800 px-2 py-0.5">{item.role}</span>
                          <span className="rounded-full border border-zinc-800 px-2 py-0.5">slot {item.slot_idx}</span>
                          {item.instance_name && <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-emerald-300">{item.instance_name}</span>}
                          {item.thread_id && <span className="rounded-full border border-blue-500/20 bg-blue-500/10 px-2 py-0.5 text-blue-300">{item.thread_id}</span>}
                        </div>
                        <div className="mt-2 text-xs text-zinc-400">{item.model}</div>
                        <div className="mt-2 whitespace-pre-wrap text-sm text-zinc-200">{item.content}</div>
                      </article>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
        <div className="flex items-center gap-2 text-zinc-100"><Link2 size={16} /> <h2 className="text-base font-semibold">Capabilities</h2></div>
        <div className="mt-3 flex flex-wrap gap-2">
          {Object.entries(options?.supports || {}).map(([key, enabled]) => (
            <span key={key} className={`rounded-full border px-3 py-1 text-xs ${enabled ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300' : 'border-zinc-800 bg-zinc-900 text-zinc-500'}`}>
              {key}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
