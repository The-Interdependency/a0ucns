import React from 'react';

const TAB_GUIDE_MAP = {
  registry: {
    title: 'Registry setup',
    human: 'Verify available models, then instantiate the workers you want to run.',
    agent: 'List /api/v1/registry, select compatible models, and avoid unavailable/deprecated IDs.',
  },
  instantiation: {
    title: 'Instantiation strategy',
    human: 'Create 2-5 focused instances and optional groups for reusable collaboration units.',
    agent: 'Prefer explicit persona/system prompts and stable history windows per instance.',
  },
  runs: {
    title: 'Automated prompt flows',
    human: 'Build staged runs using fan_out, daisy_chain, room_all, room_synthesized, council, or roleplay.',
    agent: 'Use fan_out for options, daisy_chain for refinement, council for critique+consensus.',
  },
  responses: {
    title: 'Compare and select',
    human: 'Review outputs in stack or pane mode, archive noise, and pick high-signal responses.',
    agent: 'Use compare popout for 2+ selected responses before synthesis decisions.',
  },
  chat: {
    title: 'Chat + synthesis',
    human: 'Broadcast one prompt to multiple instances, queue response blocks, then synthesize.',
    agent: 'Constrain synthesis input to relevant blocks only to improve coherence and reduce drift.',
  },
};

export function AiVisitorGuidePanel({ activeTab }) {
  const current = TAB_GUIDE_MAP[activeTab] || TAB_GUIDE_MAP.registry;

  return (
    <section className="rounded-2xl border border-cyan-500/30 bg-cyan-500/5 p-4" data-testid="ai-visitor-guide-panel">
      <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.2em] text-cyan-200" data-testid="ai-visitor-guide-label">
        AI + Human Guide
      </div>
      <h2 className="mt-2 text-base font-semibold text-zinc-100" data-testid="ai-visitor-guide-title">{current.title}</h2>
      <div className="mt-3 grid gap-3 lg:grid-cols-2">
        <article className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3" data-testid="ai-visitor-guide-human-block">
          <div className="text-xs font-medium uppercase tracking-[0.18em] text-zinc-500">Human quickstep</div>
          <p className="mt-2 text-sm text-zinc-300">{current.human}</p>
        </article>
        <article className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3" data-testid="ai-visitor-guide-agent-block">
          <div className="text-xs font-medium uppercase tracking-[0.18em] text-zinc-500">Agent protocol</div>
          <p className="mt-2 text-sm text-zinc-300">{current.agent}</p>
        </article>
      </div>
      <div className="mt-3 rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 text-xs text-zinc-400" data-testid="ai-visitor-guide-endpoints">
        Machine-readable instructions:
        <code className="ml-2 text-cyan-200" data-testid="ai-guide-endpoint-json">/api/ai-instructions</code>
        <code className="ml-2 text-cyan-200" data-testid="ai-guide-endpoint-text">/ai-instructions.txt</code>
      </div>
    </section>
  );
}
