import React from 'react';
import { Sparkles, Trash2 } from 'lucide-react';
import { estimateResponseCostUsd, estimateTokens } from '../../lib/responseCosting';

export function SynthesisQueuePanel({ synthesisBasket, onToggleSynthesisBlock }) {
  const totals = React.useMemo(() => {
    return synthesisBasket.reduce((acc, block) => {
      const tokens = estimateTokens(block.content);
      const cost = estimateResponseCostUsd(block.model, block.content);
      acc.tokens += tokens;
      acc.cost += cost;
      return acc;
    }, { tokens: 0, cost: 0 });
  }, [synthesisBasket]);

  return (
    <section className="rounded-2xl border border-violet-500/20 bg-violet-500/5 p-4" data-testid="response-synthesis-queue-panel">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-zinc-100">
          <Sparkles size={15} />
          <h3 className="text-sm font-semibold">Response synthesis queue</h3>
        </div>
        <div className="flex items-center gap-2 text-xs text-violet-200" data-testid="response-synthesis-running-totals">
          <span className="rounded-full border border-violet-500/30 bg-violet-500/10 px-2 py-1">{synthesisBasket.length} queued</span>
          <span className="rounded-full border border-violet-500/30 bg-violet-500/10 px-2 py-1">~{totals.tokens} tokens</span>
          <span className="rounded-full border border-violet-500/30 bg-violet-500/10 px-2 py-1">~${totals.cost.toFixed(4)}</span>
        </div>
      </div>
      <div className="mt-3 grid gap-2">
        {synthesisBasket.length === 0 ? (
          <div className="rounded-xl border border-dashed border-zinc-700 p-3 text-xs text-zinc-500">No responses queued yet. Use “Queue for synthesis” on any model response card.</div>
        ) : synthesisBasket.map((block) => (
          <div key={block.source_id} className="flex flex-wrap items-start justify-between gap-2 rounded-xl border border-zinc-800 bg-zinc-950/70 p-3" data-testid={`response-synthesis-queue-item-${block.source_id}`}>
            <div className="min-w-0">
              <div className="text-xs text-zinc-400">{block.source_label || block.instance_name || block.model}</div>
              <div className="mt-1 text-xs text-zinc-500">{block.model} · ~{estimateTokens(block.content)} tokens · ~${estimateResponseCostUsd(block.model, block.content).toFixed(4)}</div>
            </div>
            <button
              type="button"
              onClick={() => onToggleSynthesisBlock(block)}
              className="rounded-xl border border-zinc-800 px-2 py-1 text-xs text-zinc-300 hover:text-white"
              data-testid={`response-synthesis-queue-remove-${block.source_id}`}
            >
              <span className="flex items-center gap-1"><Trash2 size={11} /> Remove</span>
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
