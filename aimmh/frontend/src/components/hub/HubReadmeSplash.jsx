import React from 'react';

export function HubReadmeSplash() {
  return (
    <section className="overflow-hidden rounded-3xl border border-zinc-800 bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 shadow-[0_20px_80px_rgba(0,0,0,0.35)]">
      <div className="grid gap-0 lg:grid-cols-[120px_1fr]">
        <aside className="border-b border-zinc-800 bg-zinc-950/80 px-4 py-4 text-[11px] uppercase tracking-[0.28em] text-zinc-500 lg:border-b-0 lg:border-r lg:writing-mode-vertical-rl lg:rotate-180 lg:px-3 lg:py-6">
          An interdependent maker method hovelized
        </aside>
        <div className="p-5 sm:p-7">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4 font-mono text-sm text-zinc-300">
            <div className="text-xs uppercase tracking-[0.26em] text-emerald-400">README.md</div>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-zinc-50 sm:text-5xl">AIMMH</h2>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-zinc-400 sm:text-base">changes inevitable; refinement welcome</p>
          </div>
        </div>
      </div>
    </section>
  );
}
