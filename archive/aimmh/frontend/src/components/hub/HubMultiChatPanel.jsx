import React from 'react';
import { CheckCheck, Loader2, MessageSquareShare, Send, Sparkles } from 'lucide-react';
import { ResponseMarkdown } from './ResponseMarkdown';
import { ChatResponseComparator } from './ChatResponseComparator';
import { hubApi } from '../../lib/hubApi';

export function HubMultiChatPanel({
  instances,
  prompts,
  selectedPromptId,
  setSelectedPromptId,
  onSendPrompt,
  busyKey,
  synthesisBasket,
  onToggleSynthesisBlock,
  synthesisInstanceIds,
  setSynthesisInstanceIds,
  onRunSynthesis,
  synthesisBusy,
  synthesisBatches,
}) {
  const [prompt, setPrompt] = React.useState('');
  const [selectedInstanceIds, setSelectedInstanceIds] = React.useState([]);
  const [instruction, setInstruction] = React.useState('Compare, reconcile, and refine the selected responses into a useful synthesis.');
  const [draftLoaded, setDraftLoaded] = React.useState(false);

  const activeInstances = instances.filter((item) => !item.archived);
  const selectedPrompt = prompts.find((item) => item.prompt_id === selectedPromptId) || prompts[0] || null;
  const chatDraftKey = React.useMemo(() => `chat-draft:${selectedPromptId || 'new'}`, [selectedPromptId]);

  React.useEffect(() => {
    if (!selectedPromptId && prompts[0]?.prompt_id) {
      setSelectedPromptId(prompts[0].prompt_id);
    }
  }, [prompts, selectedPromptId, setSelectedPromptId]);

  React.useEffect(() => {
    let active = true;
    setDraftLoaded(false);
    const loadDraft = async () => {
      try {
        const state = await hubApi.getState(chatDraftKey);
        if (!active) return;
        setPrompt(state?.payload?.prompt || '');
        setInstruction(state?.payload?.instruction || 'Compare, reconcile, and refine the selected responses into a useful synthesis.');
        setSelectedInstanceIds(Array.isArray(state?.payload?.selectedInstanceIds) ? state.payload.selectedInstanceIds : []);
      } catch {
        if (!active) return;
        setPrompt('');
        setInstruction('Compare, reconcile, and refine the selected responses into a useful synthesis.');
      } finally {
        if (active) setDraftLoaded(true);
      }
    };
    loadDraft();
    return () => {
      active = false;
    };
  }, [chatDraftKey]);

  React.useEffect(() => {
    if (!draftLoaded) return;
    const timer = window.setTimeout(() => {
      hubApi.setState(chatDraftKey, {
        prompt,
        instruction,
        selectedInstanceIds,
      }).catch(() => {});
    }, 350);
    return () => window.clearTimeout(timer);
  }, [chatDraftKey, draftLoaded, instruction, prompt, selectedInstanceIds]);

  const toggleInstance = (instanceId) => {
    setSelectedInstanceIds((prev) => prev.includes(instanceId) ? prev.filter((id) => id !== instanceId) : [...prev, instanceId]);
  };

  const toggleSynthesisInstance = (instanceId) => {
    setSynthesisInstanceIds((prev) => prev.includes(instanceId) ? prev.filter((id) => id !== instanceId) : [...prev, instanceId]);
  };

  const allRecipientsSelected = activeInstances.length > 0 && selectedInstanceIds.length === activeInstances.length;

  const toggleSelectAllRecipients = () => {
    setSelectedInstanceIds(allRecipientsSelected ? [] : activeInstances.map((instance) => instance.instance_id));
  };

  const submit = async (event) => {
    event.preventDefault();
    if (!prompt.trim() || selectedInstanceIds.length === 0) return;
    const detail = await onSendPrompt({ prompt, instance_ids: selectedInstanceIds });
    setPrompt('');
    hubApi.deleteState(chatDraftKey).catch(() => {});
    setSelectedPromptId(detail.prompt_id);
  };

  const submitSynthesis = async () => {
    if (synthesisBasket.length === 0 || synthesisInstanceIds.length === 0) return;
    await onRunSynthesis({
      synthesis_instance_ids: synthesisInstanceIds,
      selected_blocks: synthesisBasket,
      instruction,
      label: 'Chat synthesis',
    });
  };

  return (
    <div className="space-y-4" data-testid="hub-multi-chat-panel">
      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4" data-testid="hub-direct-chat-section">
        <div className="flex items-center gap-2 text-zinc-100"><MessageSquareShare size={16} /> <h2 className="text-base font-semibold">Direct multi-instance chat</h2></div>
        <p className="mt-1 text-xs text-zinc-500">Send the exact same prompt to one or more selected instances at once. Each reply appends to that instance’s private thread history.</p>
        <form onSubmit={submit} className="mt-4 space-y-4">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-3" data-testid="chat-recipient-list">
            <div className="mb-2 flex items-center justify-between gap-2">
              <div className="text-xs font-medium text-zinc-300">Recipients</div>
              <button type="button" onClick={toggleSelectAllRecipients} className="rounded-xl border border-zinc-800 px-3 py-1 text-xs text-zinc-300" data-testid="chat-select-all-instances-button">
                <span className="flex items-center gap-2"><CheckCheck size={12} /> {allRecipientsSelected ? 'Clear all' : 'Select all instances'}</span>
              </button>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {activeInstances.length === 0 ? <div className="text-xs text-zinc-500">Create instances first in the instantiation tab.</div> : activeInstances.map((instance) => (
                <label key={instance.instance_id} className="flex items-start gap-2 rounded-xl border border-zinc-800 bg-zinc-900/60 px-3 py-2 text-xs text-zinc-300" data-testid={`chat-recipient-option-${instance.instance_id}`}>
                  <input type="checkbox" checked={selectedInstanceIds.includes(instance.instance_id)} onChange={() => toggleInstance(instance.instance_id)} className="mt-0.5" data-testid={`chat-recipient-checkbox-${instance.instance_id}`} aria-label={`chat recipient ${instance.name}`} />
                  <span>{instance.name} · {instance.model_id}</span>
                </label>
              ))}
            </div>
          </div>
          <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={4} placeholder="Broadcast prompt to selected instances"
            data-testid="chat-prompt-textarea"
            className="w-full rounded-2xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-zinc-100 outline-none focus:border-emerald-500/50" />
          <button type="submit" disabled={!prompt.trim() || selectedInstanceIds.length === 0 || busyKey === 'send-chat-prompt'} className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-60" data-testid="chat-send-button">
            <span className="flex items-center gap-2">{busyKey === 'send-chat-prompt' ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />} Send to all selected</span>
          </button>
        </form>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4" data-testid="hub-synthesis-workspace">
        <div className="flex items-center gap-2 text-zinc-100"><Sparkles size={16} /> <h2 className="text-base font-semibold">Synthesis workspace</h2></div>
        <p className="mt-1 text-xs text-zinc-500">Queue response blocks from chat or the Responses tab, choose one or more synthesis model instances, then synthesize selected content.</p>
        <div className="mt-4 grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-3 rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4" data-testid="synthesis-basket-list">
            <div className="text-xs font-medium text-zinc-300">Queued response blocks ({synthesisBasket.length})</div>
            {synthesisBasket.length === 0 ? <div className="text-sm text-zinc-500">No response blocks queued yet.</div> : synthesisBasket.map((block) => (
              <div key={block.source_id} className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-3" data-testid={`synthesis-basket-item-${block.source_id}`}>
                <div className="text-xs text-zinc-500">{block.source_label || block.instance_name || block.model}</div>
                <div className="mt-1 text-sm text-zinc-200">{block.content.slice(0, 180)}{block.content.length > 180 ? '…' : ''}</div>
              </div>
            ))}
          </div>
          <div className="space-y-3 rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4" data-testid="synthesis-model-list">
            <div className="text-xs font-medium text-zinc-300">Synthesis models ({synthesisInstanceIds.length} selected)</div>
            <div className="space-y-2">
              {activeInstances.length === 0 ? <div className="text-sm text-zinc-500">Create instances first.</div> : activeInstances.map((instance) => (
                <label key={instance.instance_id} className={`flex items-start gap-2 rounded-xl border px-3 py-2 text-xs ${synthesisInstanceIds.includes(instance.instance_id) ? 'border-violet-500/30 bg-violet-500/10 text-violet-200' : 'border-zinc-800 bg-zinc-900/60 text-zinc-300'}`} data-testid={`synthesis-model-option-${instance.instance_id}`}>
                  <input type="checkbox" checked={synthesisInstanceIds.includes(instance.instance_id)} onChange={() => toggleSynthesisInstance(instance.instance_id)} className="mt-0.5" data-testid={`synthesis-model-checkbox-${instance.instance_id}`} aria-label={`synthesis model ${instance.name}`} />
                  <span>{instance.name} · {instance.model_id}</span>
                </label>
              ))}
            </div>
            {synthesisInstanceIds.length > 0 && (
              <div className="flex flex-wrap gap-2 text-[11px] text-violet-200">
                {activeInstances.filter((instance) => synthesisInstanceIds.includes(instance.instance_id)).map((instance) => (
                  <span key={instance.instance_id} className="rounded-full border border-violet-500/30 bg-violet-500/10 px-2 py-1" data-testid={`synthesis-selected-model-chip-${instance.instance_id}`}>
                    {instance.name}
                  </span>
                ))}
              </div>
            )}
            <textarea value={instruction} onChange={(event) => setInstruction(event.target.value)} rows={5} placeholder="Synthesis instruction"
              data-testid="synthesis-instruction-textarea"
              className="w-full rounded-2xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 outline-none focus:border-violet-500/50" />
            <button type="button" onClick={submitSynthesis} disabled={synthesisBasket.length === 0 || synthesisInstanceIds.length === 0 || synthesisBusy} className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-60" data-testid="synthesis-submit-button">
              <span className="flex items-center gap-2">{synthesisBusy ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />} Synthesize selected responses</span>
            </button>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4" data-testid="prompt-indexed-responses-section">
        <div className="text-base font-semibold text-zinc-100">Prompt-indexed responses</div>
        <p className="mt-1 text-xs text-zinc-500">Every response is grouped by prompt batch and instance. Queue blocks for synthesis with one tap.</p>
        <div className="mt-4 space-y-3">
          {prompts.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-zinc-800 p-5 text-sm text-zinc-500">No direct chat prompts yet.</div>
          ) : prompts.map((promptItem) => (
            <button key={promptItem.prompt_id} type="button" onClick={() => setSelectedPromptId(promptItem.prompt_id)} className={`w-full rounded-2xl border p-4 text-left transition ${selectedPromptId === promptItem.prompt_id ? 'border-emerald-500/40 bg-emerald-500/10' : 'border-zinc-800 bg-zinc-950/60 hover:border-zinc-700'}`} data-testid={`prompt-batch-button-${promptItem.prompt_id}`}>
              <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">Prompt batch</div>
              <div className="mt-2 text-sm text-zinc-100">{promptItem.prompt}</div>
              <div className="mt-3 text-xs text-zinc-500">{promptItem.responses?.length || 0} responses · {promptItem.instance_names?.join(', ')}</div>
            </button>
          ))}
        </div>
      </section>

      {selectedPrompt && (
        <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4" data-testid="selected-prompt-section">
          <div className="text-sm font-semibold text-zinc-100">Selected prompt</div>
          <div className="mt-2 whitespace-pre-wrap text-sm text-zinc-300">{selectedPrompt.prompt}</div>
          <div className="mt-4">
            <ChatResponseComparator
              promptId={selectedPrompt.prompt_id}
              responses={selectedPrompt.responses || []}
              synthesisBasket={synthesisBasket}
              onToggleSynthesisBlock={onToggleSynthesisBlock}
            />
          </div>
        </section>
      )}

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4" data-testid="recent-syntheses-section">
        <div className="text-base font-semibold text-zinc-100">Recent syntheses</div>
        <div className="mt-4 space-y-3">
          {synthesisBatches.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-zinc-800 p-5 text-sm text-zinc-500">No synthesis batches yet.</div>
          ) : synthesisBatches.map((batch) => (
            <article key={batch.synthesis_batch_id} className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4" data-testid={`synthesis-batch-${batch.synthesis_batch_id}`}>
              <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">Synthesis batch</div>
              <div className="mt-2 text-sm text-zinc-200">{batch.label || batch.synthesis_batch_id}</div>
              <div className="mt-2 text-xs text-zinc-500">{batch.synthesis_instance_names?.join(', ')}</div>
              <div className="mt-4 space-y-3">
                {(batch.outputs || []).map((output) => (
                  <div key={output.message_id || `${batch.synthesis_batch_id}-${output.synthesis_instance_id}`} className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4" data-testid={`synthesis-output-${output.message_id || `${batch.synthesis_batch_id}-${output.synthesis_instance_id}`}`}>
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="text-sm font-medium text-zinc-100">{output.synthesis_instance_name}</div>
                      <span className="rounded-full border border-zinc-800 bg-zinc-950 px-2 py-1 text-[11px] text-zinc-400">{output.model}</span>
                    </div>
                    <div className="mt-3"><ResponseMarkdown content={output.content} fontScale={1} /></div>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
