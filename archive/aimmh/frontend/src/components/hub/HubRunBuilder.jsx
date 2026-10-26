import React from 'react';
import { ArrowDownToLine, Plus, Trash2, Workflow } from 'lucide-react';
import { createEmptyStage, INPUT_MODE_OPTIONS, PATTERN_OPTIONS } from './hubConfig';
import { hubApi } from '../../lib/hubApi';

function SourceSelector({ title, selected, onToggle, sourceOptions, testIdPrefix }) {
  return (
    <div className="space-y-2 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-3" data-testid={`${testIdPrefix}-selector`}>
      <div className="text-xs font-medium text-zinc-300">{title}</div>
      <div className="grid gap-2 sm:grid-cols-2">
        {sourceOptions.map((option) => {
          const checked = selected.some((item) => item.source_type === option.source_type && item.source_id === option.source_id);
          const optionKey = `${option.source_type}-${option.source_id}`;
          return (
            <label key={`${option.source_type}:${option.source_id}`} className="flex items-start gap-2 rounded-xl border border-zinc-800 bg-zinc-950/60 px-3 py-2 text-xs text-zinc-300" data-testid={`${testIdPrefix}-option-${optionKey}`}>
              <input type="checkbox" checked={checked} onChange={() => onToggle(option)} className="mt-0.5" data-testid={`${testIdPrefix}-checkbox-${optionKey}`} />
              <span>{option.label}</span>
            </label>
          );
        })}
      </div>
    </div>
  );
}

function toggleSource(list, option) {
  const exists = list.some((item) => item.source_type === option.source_type && item.source_id === option.source_id);
  return exists ? list.filter((item) => !(item.source_type === option.source_type && item.source_id === option.source_id)) : [...list, { source_type: option.source_type, source_id: option.source_id }];
}

function StageCard({ index, stage, sourceOptions, instanceOptions, onChange, onRemove }) {
  const isRoleplay = stage.pattern === 'roleplay';
  const isSynthRoom = stage.pattern === 'room_synthesized';
  const stageId = `run-stage-${index + 1}`;

  const updateNumericField = (field) => (event) => {
    const raw = event.target.value;
    if (raw === '') {
      onChange({ ...stage, [field]: '' });
      return;
    }
    const parsed = Number(raw);
    if (Number.isNaN(parsed)) return;
    onChange({ ...stage, [field]: parsed });
  };

  const normalizeNumericField = (field, fallback, min, max) => () => {
    const parsed = Number(stage[field]);
    const safeValue = Number.isNaN(parsed) || stage[field] === ''
      ? fallback
      : Math.min(max, Math.max(min, parsed));
    onChange({ ...stage, [field]: safeValue });
  };

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4" data-testid={`${stageId}-card`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">Stage {index + 1}</div>
          <input value={stage.name} onChange={(e) => onChange({ ...stage, name: e.target.value })} placeholder="Optional stage label"
            data-testid={`${stageId}-name-input`}
            className="mt-2 w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500/80 outline-none focus:border-emerald-500/50" />
        </div>
        <button type="button" onClick={onRemove} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-400 transition hover:border-red-500/30 hover:text-red-300" data-testid={`${stageId}-remove-button`}>
          <span className="flex items-center gap-2"><Trash2 size={13} /> Remove</span>
        </button>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <select value={stage.pattern} onChange={(e) => onChange({ ...createEmptyStage(), ...stage, pattern: e.target.value })}
          data-testid={`${stageId}-pattern-select`}
          className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50">
          {PATTERN_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
        <select value={stage.input_mode} onChange={(e) => onChange({ ...stage, input_mode: e.target.value })}
          data-testid={`${stageId}-input-mode-select`}
          className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50">
          {INPUT_MODE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
        <input type="number" min={1} max={10} value={stage.rounds ?? ''} onChange={updateNumericField('rounds')} onBlur={normalizeNumericField('rounds', 1, 1, 10)}
          placeholder="Rounds (default 1)"
          data-testid={`${stageId}-rounds-input`}
          className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500/80 outline-none focus:border-emerald-500/50" />
        <input type="number" min={1} max={10} value={stage.verbosity ?? ''} onChange={updateNumericField('verbosity')} onBlur={normalizeNumericField('verbosity', 5, 1, 10)}
          placeholder="Verbosity (default 5)"
          data-testid={`${stageId}-verbosity-input`}
          className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500/80 outline-none focus:border-emerald-500/50" />
        <input type="number" min={1} max={200} value={stage.max_history ?? ''} onChange={updateNumericField('max_history')} onBlur={normalizeNumericField('max_history', 30, 1, 200)}
          placeholder="Max history (default 30)"
          data-testid={`${stageId}-max-history-input`}
          className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500/80 outline-none focus:border-emerald-500/50" />
        {!isRoleplay && (
          <label className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-300">
            <input type="checkbox" checked={stage.include_original_prompt} onChange={(e) => onChange({ ...stage, include_original_prompt: e.target.checked })} data-testid={`${stageId}-include-original-checkbox`} />
            Keep original prompt in chain
          </label>
        )}
        <textarea value={stage.prompt} onChange={(e) => onChange({ ...stage, prompt: e.target.value })} rows={3} placeholder="Optional stage prompt override"
          data-testid={`${stageId}-prompt-textarea`}
          className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500/80 outline-none focus:border-emerald-500/50 lg:col-span-2" />
      </div>

      {isRoleplay ? (
        <div className="mt-4 space-y-3">
          <SourceSelector title="Player participants" selected={stage.player_participants} sourceOptions={sourceOptions} onToggle={(option) => onChange({ ...stage, player_participants: toggleSource(stage.player_participants, option) })} testIdPrefix={`${stageId}-player-participants`} />
          <div className="grid gap-3 lg:grid-cols-2">
            <select value={stage.dm_instance_id} onChange={(e) => onChange({ ...stage, dm_instance_id: e.target.value, dm_group_id: '' })}
              data-testid={`${stageId}-dm-instance-select`}
              className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50">
              <option value="">Fixed DM instance (optional)</option>
              {instanceOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
            <select value={stage.dm_group_id} onChange={(e) => onChange({ ...stage, dm_group_id: e.target.value, dm_instance_id: '' })}
              data-testid={`${stageId}-dm-group-select`}
              className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50">
              <option value="">DM rotation group (optional)</option>
              {sourceOptions.filter((option) => option.source_type === 'group').map((option) => <option key={option.source_id} value={option.source_id}>{option.label}</option>)}
            </select>
            <input type="number" min={10} max={2000} value={stage.action_word_limit ?? ''} onChange={updateNumericField('action_word_limit')} onBlur={normalizeNumericField('action_word_limit', 120, 10, 2000)}
              placeholder="Action word limit (default 120)"
              data-testid={`${stageId}-action-word-limit-input`}
              className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500/80 outline-none focus:border-emerald-500/50" />
            <div className="flex flex-wrap gap-3 rounded-2xl border border-zinc-800 bg-zinc-900 px-3 py-3 text-xs text-zinc-300">
              <label className="flex items-center gap-2"><input type="checkbox" checked={stage.use_initiative} onChange={(e) => onChange({ ...stage, use_initiative: e.target.checked })} data-testid={`${stageId}-use-initiative-checkbox`} /> Use initiative</label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={stage.allow_reactions} onChange={(e) => onChange({ ...stage, allow_reactions: e.target.checked })} data-testid={`${stageId}-allow-reactions-checkbox`} /> Allow reactions</label>
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-4 space-y-3">
          <SourceSelector title="Participants" selected={stage.participants} sourceOptions={sourceOptions} onToggle={(option) => onChange({ ...stage, participants: toggleSource(stage.participants, option) })} testIdPrefix={`${stageId}-participants`} />
          {isSynthRoom && (
            <div className="grid gap-3 lg:grid-cols-2">
              <select value={stage.synthesis_instance_id} onChange={(e) => onChange({ ...stage, synthesis_instance_id: e.target.value, synthesis_group_id: '' })}
                data-testid={`${stageId}-synthesis-instance-select`}
                className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50">
                <option value="">Synthesis instance</option>
                {instanceOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select>
              <select value={stage.synthesis_group_id} onChange={(e) => onChange({ ...stage, synthesis_group_id: e.target.value, synthesis_instance_id: '' })}
                data-testid={`${stageId}-synthesis-group-select`}
                className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500/50">
                <option value="">Single-member synthesis group</option>
                {sourceOptions.filter((option) => option.source_type === 'group').map((option) => <option key={option.source_id} value={option.source_id}>{option.label}</option>)}
              </select>
              <textarea value={stage.synthesis_prompt} onChange={(e) => onChange({ ...stage, synthesis_prompt: e.target.value })} rows={2} placeholder="Synthesis prompt"
                data-testid={`${stageId}-synthesis-prompt-textarea`}
                className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500/80 outline-none focus:border-emerald-500/50 lg:col-span-2" />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function HubRunBuilder({ sourceOptions, instanceOptions, onRun, busyKey }) {
  const [label, setLabel] = React.useState('');
  const [prompt, setPrompt] = React.useState('');
  const [stages, setStages] = React.useState([createEmptyStage()]);
  const [draftLoaded, setDraftLoaded] = React.useState(false);
  const runDraftKey = 'run-builder-draft:new';

  React.useEffect(() => {
    let active = true;
    const loadDraft = async () => {
      try {
        const state = await hubApi.getState(runDraftKey);
        if (!active) return;
        setLabel(state?.payload?.label || '');
        setPrompt(state?.payload?.prompt || '');
        setStages(Array.isArray(state?.payload?.stages) && state.payload.stages.length > 0 ? state.payload.stages : [createEmptyStage()]);
      } catch {
        if (!active) return;
        setLabel('');
        setPrompt('');
        setStages([createEmptyStage()]);
      } finally {
        if (active) setDraftLoaded(true);
      }
    };
    loadDraft();
    return () => {
      active = false;
    };
  }, []);

  React.useEffect(() => {
    if (!draftLoaded) return;
    const timer = window.setTimeout(() => {
      hubApi.setState(runDraftKey, {
        label,
        prompt,
        stages,
      }).catch(() => {});
    }, 350);
    return () => window.clearTimeout(timer);
  }, [draftLoaded, label, prompt, stages]);

  const updateStage = (index, nextStage) => {
    setStages((prev) => prev.map((stage, stageIndex) => stageIndex === index ? nextStage : stage));
  };

  const removeStage = (index) => {
    setStages((prev) => prev.filter((_, stageIndex) => stageIndex !== index));
  };

  const submit = async (event) => {
    event.preventDefault();
    if (!prompt.trim() || stages.length === 0) return;
    await onRun({
      label: label || null,
      prompt,
      persist_instance_threads: true,
      stages: stages.map((stage) => ({
        ...stage,
        rounds: Number(stage.rounds) || 1,
        verbosity: Number(stage.verbosity) || 5,
        max_history: Number(stage.max_history) || 30,
        action_word_limit: Number(stage.action_word_limit) || 120,
        prompt: stage.prompt || null,
        synthesis_instance_id: stage.synthesis_instance_id || null,
        synthesis_group_id: stage.synthesis_group_id || null,
        dm_instance_id: stage.dm_instance_id || null,
        dm_group_id: stage.dm_group_id || null,
      })),
    });
    setLabel('');
    setPrompt('');
    setStages([createEmptyStage()]);
    hubApi.deleteState(runDraftKey).catch(() => {});
  };

  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4" data-testid="hub-run-builder">
      <div>
        <h2 className="text-base font-semibold text-zinc-100">Pipeline builder</h2>
        <p className="text-xs text-zinc-500">Compose nested groups and isolated instances into aimmh-lib stage pipelines.</p>
      </div>

      <div className="mt-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-sm text-zinc-300" data-testid="hub-run-builder-guide">
        <div className="flex items-center gap-2 text-emerald-300"><ArrowDownToLine size={14} /> How to start a run</div>
        <ol className="mt-3 list-decimal space-y-1 pl-5 text-xs text-zinc-400">
          <li>Create one or more instances on the left. The same model can appear many times.</li>
          <li>Optionally create nested groups in the middle column.</li>
          <li>In Stage 1, choose a pattern and check the instances/groups that should participate.</li>
          <li>Write the root prompt, then click <span className="text-zinc-200">Execute pipeline</span>.</li>
        </ol>
      </div>

      <form onSubmit={submit} className="mt-4 space-y-4" data-testid="run-builder-form">
        <input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Run label (optional)"
          data-testid="run-label-input"
          className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500/80 outline-none focus:border-emerald-500/50" />
        <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={4} placeholder="Root prompt"
          data-testid="run-root-prompt-textarea"
          className="w-full rounded-2xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-500/80 outline-none focus:border-emerald-500/50" />

        <div className="space-y-4">
          {stages.map((stage, index) => (
            <StageCard key={`${index}-${stage.pattern}`} index={index} stage={stage} sourceOptions={sourceOptions} instanceOptions={instanceOptions}
              onChange={(nextStage) => updateStage(index, nextStage)} onRemove={() => removeStage(index)} />
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button type="button" onClick={() => setStages((prev) => [...prev, createEmptyStage()])}
            data-testid="add-run-stage-button"
            className="rounded-xl border border-zinc-800 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-700 hover:text-white">
            <span className="flex items-center gap-2"><Plus size={14} /> Add stage</span>
          </button>
          <button type="submit" disabled={!prompt.trim() || stages.length === 0 || busyKey === 'create-run'}
            data-testid="execute-run-button"
            className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-500 disabled:opacity-60">
            <span className="flex items-center gap-2"><Workflow size={14} /> Execute pipeline</span>
          </button>
          <div className="text-xs text-zinc-500">Runs persist structured stage/round/step results.</div>
        </div>
      </form>
    </section>
  );
}
