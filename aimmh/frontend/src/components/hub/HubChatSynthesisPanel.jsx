import React from 'react';
import { Sparkles } from 'lucide-react';
import { HubRunTimeline } from './HubRunTimeline';

export function HubChatSynthesisPanel({ options, runs, selectedRunId, setSelectedRunId, selectedRun }) {
  const synthesisHints = (selectedRun?.stage_summaries || []).filter((item) => ['room_synthesized', 'council'].includes(item.pattern));

  return (
    <div className="space-y-4">
      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
        <div className="flex items-center gap-2 text-zinc-100"><Sparkles size={16} /> <h2 className="text-base font-semibold">Chat & synthesis</h2></div>
        <p className="mt-1 text-xs text-zinc-500">Inspect the prompt flow, synthesis-heavy stages, and detailed stage timeline in one place.</p>
        <div className="mt-4 space-y-2">
          {synthesisHints.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-zinc-800 p-4 text-sm text-zinc-500">No explicit synthesis stages yet. Run a council or room_synthesized pipeline to surface synthesis summaries here.</div>
          ) : synthesisHints.map((item) => (
            <div key={`${item.stage_index}-${item.pattern}`} className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-3">
              <div className="text-sm font-medium text-zinc-100">{item.stage_name || item.pattern}</div>
              <div className="mt-1 text-xs text-zinc-500">{item.prompt_used}</div>
            </div>
          ))}
        </div>
      </section>
      <HubRunTimeline options={options} runs={runs} selectedRunId={selectedRunId} setSelectedRunId={setSelectedRunId} selectedRun={selectedRun} />
    </div>
  );
}
