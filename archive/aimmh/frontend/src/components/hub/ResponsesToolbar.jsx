import React from 'react';
import { CheckCheck, Copy, LayoutPanelTop, Rows3, Share2 } from 'lucide-react';

export function ResponsesToolbar({
  sourceType,
  setSourceType,
  compareMode,
  setCompareMode,
  showArchivedResponses,
  setShowArchivedResponses,
  selectedRunId,
  setSelectedRunId,
  runs,
  selectedStageIndex,
  setSelectedStageIndex,
  stageOptions,
  selectedPromptId,
  setSelectedPromptId,
  prompts,
  onToggleSelectAll,
  onCopySelected,
  onShareSelected,
  onOpenCompare,
  visibleResponsesCount,
  selectedResponsesCount,
  allVisibleSelected,
}) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4" data-testid="responses-toolbar">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-zinc-100">Response synthesis</h2>
          <p className="mt-1 text-xs text-zinc-500">Queue model responses, compare variants, and keep a running token/cost estimate for synthesis planning.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="flex items-center gap-2 rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300" data-testid="responses-show-archived-toggle-wrap">
            <input
              type="checkbox"
              checked={showArchivedResponses}
              onChange={(event) => setShowArchivedResponses(event.target.checked)}
              data-testid="responses-show-archived-checkbox"
            />
            Show archived
          </label>
          <button type="button" onClick={() => setSourceType('runs')} className={`rounded-xl border px-3 py-2 text-xs ${sourceType === 'runs' ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300' : 'border-zinc-800 text-zinc-300'}`} data-testid="responses-source-runs-button">
            Run responses
          </button>
          <button type="button" onClick={() => setSourceType('prompts')} className={`rounded-xl border px-3 py-2 text-xs ${sourceType === 'prompts' ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300' : 'border-zinc-800 text-zinc-300'}`} data-testid="responses-source-prompts-button">
            Prompt responses
          </button>
          <button type="button" onClick={() => setCompareMode('stack')} className={`rounded-xl border px-3 py-2 text-xs ${compareMode === 'stack' ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300' : 'border-zinc-800 text-zinc-300'}`} data-testid="responses-compare-stack-button">
            <span className="flex items-center gap-2"><Rows3 size={13} /> Stack</span>
          </button>
          <button type="button" onClick={() => setCompareMode('carousel')} className={`rounded-xl border px-3 py-2 text-xs ${compareMode === 'carousel' ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300' : 'border-zinc-800 text-zinc-300'}`} data-testid="responses-compare-carousel-button">
            <span className="flex items-center gap-2"><LayoutPanelTop size={13} /> Pane mode</span>
          </button>
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_auto]">
        {sourceType === 'runs' ? (
          <>
            <select value={selectedRunId || ''} onChange={(event) => setSelectedRunId(event.target.value)} className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50" data-testid="responses-run-select">
              <option value="">Select a run</option>
              {runs.map((run) => <option key={run.run_id} value={run.run_id}>{run.label || run.run_id}</option>)}
            </select>
            <select value={selectedStageIndex} onChange={(event) => setSelectedStageIndex(Number(event.target.value))} className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50" data-testid="responses-stage-select">
              {stageOptions.length === 0 ? <option value={0}>Stage 1</option> : stageOptions.map((stage) => <option key={stage.value} value={stage.value}>{stage.label}</option>)}
            </select>
          </>
        ) : (
          <>
            <select value={selectedPromptId || ''} onChange={(event) => setSelectedPromptId(event.target.value)} className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50 md:col-span-2" data-testid="responses-prompt-select">
              <option value="">Select a prompt batch</option>
              {prompts.map((prompt) => <option key={prompt.prompt_id} value={prompt.prompt_id}>{prompt.label || prompt.prompt}</option>)}
            </select>
          </>
        )}
        <div className="flex gap-2">
          <button type="button" onClick={onToggleSelectAll} disabled={visibleResponsesCount === 0} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 disabled:opacity-40" data-testid="responses-select-all-button">
            <span className="flex items-center gap-2"><CheckCheck size={13} /> {allVisibleSelected ? 'Clear visible' : 'Select all responses'}</span>
          </button>
          <button type="button" onClick={onCopySelected} disabled={selectedResponsesCount === 0} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 disabled:opacity-40" data-testid="responses-copy-selected-button"><span className="flex items-center gap-2"><Copy size={13} /> Copy selected</span></button>
          <button type="button" onClick={onShareSelected} disabled={selectedResponsesCount === 0} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 disabled:opacity-40" data-testid="responses-share-selected-button"><span className="flex items-center gap-2"><Share2 size={13} /> Share selected</span></button>
          <button
            type="button"
            onClick={onOpenCompare}
            disabled={selectedResponsesCount < 2}
            className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300 disabled:opacity-40"
            data-testid="responses-compare-popout-button"
          >
            Compare popout
          </button>
        </div>
      </div>
    </div>
  );
}
