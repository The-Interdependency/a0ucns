import React from 'react';
import { toast } from 'sonner';
import { hubApi } from '../../lib/hubApi';
import { ResponseCarousel } from './ResponseCarousel';
import { ResponsePane } from './ResponsePane';
import { ResponsesToolbar } from './ResponsesToolbar';
import { ResponsesComparePopout } from './ResponsesComparePopout';
import { SynthesisQueuePanel } from './SynthesisQueuePanel';

export function HubResponsesPanel({
  runs,
  selectedRun,
  selectedRunId,
  setSelectedRunId,
  prompts,
  selectedPromptId,
  setSelectedPromptId,
  synthesisBasket,
  onToggleSynthesisBlock,
}) {
  const [sourceType, setSourceType] = React.useState('runs');
  const [selectedStageIndex, setSelectedStageIndex] = React.useState(0);
  const [compareMode, setCompareMode] = React.useState('stack');
  const [selectedIds, setSelectedIds] = React.useState([]);
  const [feedbackMap, setFeedbackMap] = React.useState({});
  const [fontScale, setFontScale] = React.useState(1);
  const [activeIndex, setActiveIndex] = React.useState(0);
  const [archivedResponseIds, setArchivedResponseIds] = React.useState([]);
  const [showArchivedResponses, setShowArchivedResponses] = React.useState(false);
  const [comparePopoutOpen, setComparePopoutOpen] = React.useState(false);

  React.useEffect(() => {
    setSelectedStageIndex(0);
    setSelectedIds([]);
    setActiveIndex(0);
  }, [selectedRunId, selectedPromptId, sourceType]);

  const stageSummaries = selectedRun?.stage_summaries || [];
  const stageOptions = stageSummaries.map((summary) => ({ value: summary.stage_index, label: summary.stage_name || summary.pattern }));
  const selectedPrompt = prompts.find((item) => item.prompt_id === selectedPromptId) || prompts[0] || null;
  const toSynthesisBlock = React.useCallback((item) => ({
    source_type: sourceType === 'runs' ? 'run_response' : 'prompt_response',
    source_id: item.run_step_id,
    source_label: sourceType === 'runs'
      ? `Run ${selectedRunId || 'unknown'} · ${item.instance_name || item.model}`
      : `Prompt ${selectedPromptId || 'unknown'} · ${item.instance_name || item.model}`,
    instance_id: item.instance_id,
    instance_name: item.instance_name,
    model: item.model,
    content: item.content,
  }), [selectedPromptId, selectedRunId, sourceType]);
  const stageResponses = sourceType === 'runs'
    ? (selectedRun?.results || []).filter((item) => item.stage_index === Number(selectedStageIndex))
    : (selectedPrompt?.responses || []).map((item, index) => ({
        ...item,
        run_step_id: item.message_id || `${item.prompt_id}-${item.instance_id}-${index}`,
        round_num: 0,
        step_num: index + 1,
        role: 'assistant',
        slot_idx: index,
      }));
  const visibleResponses = stageResponses.filter((item) => showArchivedResponses || !archivedResponseIds.includes(item.run_step_id));
  const synthesisIds = synthesisBasket.map((item) => item.source_id);
  const selectedResponses = visibleResponses.filter((item) => selectedIds.includes(item.run_step_id));

  const toggleSelected = (item) => {
    setSelectedIds((prev) => prev.includes(item.run_step_id) ? prev.filter((id) => id !== item.run_step_id) : [...prev, item.run_step_id]);
  };

  const toggleResponseArchive = (item) => {
    setArchivedResponseIds((prev) => prev.includes(item.run_step_id)
      ? prev.filter((id) => id !== item.run_step_id)
      : [...prev, item.run_step_id]);
    if (!archivedResponseIds.includes(item.run_step_id)) {
      setSelectedIds((prev) => prev.filter((id) => id !== item.run_step_id));
    }
  };

  const copyText = async (text, label = 'Response copied') => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(label);
    } catch {
      toast.error('Copy failed');
    }
  };

  const shareResponse = async (item) => {
    const payload = { title: item.instance_name || item.model, text: item.content };
    if (navigator.share) {
      try {
        await navigator.share(payload);
        return;
      } catch {
        // fall through
      }
    }
    await copyText(item.content, 'Share not available — copied instead');
  };

  const submitFeedback = async (item, value) => {
    if (!item.message_id) {
      toast.info('Feedback is available for fresh persisted responses.');
      setFeedbackMap((prev) => ({ ...prev, [item.run_step_id]: value }));
      return;
    }
    try {
      await hubApi.submitFeedback(item.message_id, value);
      setFeedbackMap((prev) => ({ ...prev, [item.message_id]: value }));
      toast.success(`Marked ${value === 'up' ? 'thumbs up' : 'thumbs down'}`);
    } catch (error) {
      toast.error(error.message || 'Feedback failed');
    }
  };

  const copySelected = async () => {
    if (selectedResponses.length === 0) return;
    const text = selectedResponses.map((item) => `# ${item.instance_name || item.model}\n\n${item.content}`).join('\n\n---\n\n');
    await copyText(text, 'Selected responses copied');
  };

  const shareSelected = async () => {
    if (selectedResponses.length === 0) return;
    const text = selectedResponses.map((item) => `# ${item.instance_name || item.model}\n\n${item.content}`).join('\n\n---\n\n');
    if (navigator.share) {
      try {
        await navigator.share({ title: 'AIMMH selected responses', text });
        return;
      } catch {
        // fall through
      }
    }
    await copyText(text, 'Share unavailable — copied selected responses');
  };

  const toggleSelectAllResponses = () => {
    if (visibleResponses.length === 0) return;
    const visibleIds = visibleResponses.map((item) => item.run_step_id);
    const allSelected = visibleIds.every((id) => selectedIds.includes(id));
    setSelectedIds(allSelected ? selectedIds.filter((id) => !visibleIds.includes(id)) : Array.from(new Set([...selectedIds, ...visibleIds])));
  };

  const visibleIds = visibleResponses.map((item) => item.run_step_id);
  const allVisibleSelected = visibleIds.length > 0 && visibleIds.every((id) => selectedIds.includes(id));

  return (
    <section className="space-y-4" data-testid="hub-responses-panel">
      <ResponsesToolbar
        sourceType={sourceType}
        setSourceType={setSourceType}
        compareMode={compareMode}
        setCompareMode={setCompareMode}
        showArchivedResponses={showArchivedResponses}
        setShowArchivedResponses={setShowArchivedResponses}
        selectedRunId={selectedRunId}
        setSelectedRunId={setSelectedRunId}
        runs={runs}
        selectedStageIndex={selectedStageIndex}
        setSelectedStageIndex={setSelectedStageIndex}
        stageOptions={stageOptions}
        selectedPromptId={selectedPromptId}
        setSelectedPromptId={setSelectedPromptId}
        prompts={prompts}
        onToggleSelectAll={toggleSelectAllResponses}
        onCopySelected={copySelected}
        onShareSelected={shareSelected}
        onOpenCompare={() => setComparePopoutOpen(true)}
        visibleResponsesCount={visibleResponses.length}
        selectedResponsesCount={selectedResponses.length}
        allVisibleSelected={allVisibleSelected}
      />

      <SynthesisQueuePanel
        synthesisBasket={synthesisBasket}
        onToggleSynthesisBlock={onToggleSynthesisBlock}
      />

      {(sourceType === 'runs' && !selectedRun) || (sourceType === 'prompts' && !selectedPrompt) ? (
        <div className="rounded-2xl border border-dashed border-zinc-800 p-6 text-sm text-zinc-500" data-testid="responses-empty-state">Select a {sourceType === 'runs' ? 'run' : 'prompt batch'} to compare responses.</div>
      ) : compareMode === 'carousel' ? (
        <ResponseCarousel
          items={visibleResponses}
          activeIndex={activeIndex}
          setActiveIndex={setActiveIndex}
          fontScale={fontScale}
          setFontScale={setFontScale}
          selectedIds={selectedIds}
          feedbackMap={feedbackMap}
          onToggleSelected={toggleSelected}
          onFeedback={submitFeedback}
          onCopy={(item) => copyText(item.content)}
          onShare={shareResponse}
          archivedIds={archivedResponseIds}
          onToggleArchive={toggleResponseArchive}
          synthesisIds={synthesisIds}
          onToggleSynthesis={(item) => onToggleSynthesisBlock(toSynthesisBlock(item))}
        />
      ) : (
        <div className="space-y-4" data-testid="responses-stack-mode">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-3 text-xs text-zinc-500" data-testid="responses-gesture-hint">
            Pinch/spread to zoom font size. Switch to pane mode for two-finger vertical pane sliding while one-finger scrolling within each response.
          </div>
          {visibleResponses.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-zinc-800 p-6 text-sm text-zinc-500" data-testid="responses-no-results">No responses yet for this selection.</div>
          ) : visibleResponses.map((item) => (
            <ResponsePane
              key={item.run_step_id}
              item={item}
              selected={selectedIds.includes(item.run_step_id)}
              fontScale={fontScale}
              feedback={feedbackMap[item.message_id || item.run_step_id]}
              onToggleSelected={() => toggleSelected(item)}
              onFeedback={(value) => submitFeedback(item, value)}
              onCopy={() => copyText(item.content)}
              onShare={() => shareResponse(item)}
              archived={archivedResponseIds.includes(item.run_step_id)}
              onToggleArchive={() => toggleResponseArchive(item)}
              synthesisSelected={synthesisIds.includes(item.run_step_id)}
              onToggleSynthesis={() => onToggleSynthesisBlock(toSynthesisBlock(item))}
            />
          ))}
        </div>
      )}

      <ResponsesComparePopout
        open={comparePopoutOpen}
        selectedResponses={selectedResponses}
        fontScale={fontScale}
        onClose={() => setComparePopoutOpen(false)}
      />
    </section>
  );
}
