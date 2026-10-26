import React from 'react';
import { X } from 'lucide-react';
import { ResponseMarkdown } from './ResponseMarkdown';

export function ResponsesComparePopout({ open, selectedResponses, fontScale, onClose }) {
  if (!open || selectedResponses.length < 2) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 p-4 sm:p-8" data-testid="responses-compare-popout-overlay">
      <div className="mx-auto flex h-full w-full max-w-[1300px] flex-col rounded-3xl border border-zinc-700 bg-zinc-950" data-testid="responses-compare-popout-modal">
        <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
          <div className="text-sm font-semibold text-zinc-100" data-testid="responses-compare-popout-title">Compare selected responses ({selectedResponses.length})</div>
          <button type="button" onClick={onClose} className="rounded-full border border-zinc-700 p-2 text-zinc-300 hover:text-white" data-testid="responses-compare-popout-close-button">
            <X size={14} />
          </button>
        </div>
        <div className="grid min-h-0 flex-1 gap-3 overflow-auto p-4 md:grid-cols-2 xl:grid-cols-3" data-testid="responses-compare-popout-grid">
          {selectedResponses.map((item) => (
            <article key={`compare-${item.run_step_id}`} className="flex min-h-0 flex-col rounded-2xl border border-zinc-800 bg-zinc-900/60 p-3" data-testid={`responses-compare-popout-item-${item.run_step_id}`}>
              <div className="mb-2 text-sm font-medium text-zinc-100">{item.instance_name || item.model}</div>
              <div className="rounded-full border border-zinc-700 bg-zinc-950 px-2 py-1 text-[11px] text-zinc-400">{item.model}</div>
              <div className="mt-3 min-h-0 flex-1 overflow-auto rounded-2xl border border-zinc-800 bg-zinc-950/70 p-3" data-testid={`responses-compare-popout-content-${item.run_step_id}`}>
                <ResponseMarkdown content={item.content} fontScale={fontScale} />
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
