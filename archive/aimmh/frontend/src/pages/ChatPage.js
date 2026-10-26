import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../contexts/ChatContext';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import useEmblaCarousel from 'embla-carousel-react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Send, Plus, Settings, LogOut, ChevronDown, ChevronRight,
  ThumbsUp, ThumbsDown, Copy, Clock, Menu,
  MessageSquare, Loader2, Columns2, Layers, GalleryHorizontal,
  Lock, ChevronLeft, FileUp, Zap, Link2, Repeat, Globe, Sliders,
  Check, X
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const LAYOUTS = { STACK: 'stack', SPLIT: 'split', CAROUSEL: 'carousel' };
const MODES = { NORMAL: 'normal', SHARED_ALL: 'shared_all', SHARED_SYNTH: 'shared_synth', DAISY: 'daisy' };

// ---- Model Selector ----
function ModelSelector({ registry, selected, onToggle }) {
  const [expandedDev, setExpandedDev] = useState({});
  if (!registry.length) return null;
  return (
    <div className="space-y-1" data-testid="model-selector">
      {registry.map(dev => (
        <div key={dev.developer_id} className="rounded-md border border-zinc-800 overflow-hidden">
          <button onClick={() => setExpandedDev(p => ({ ...p, [dev.developer_id]: !p[dev.developer_id] }))}
            className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-800/60 transition-colors"
            data-testid={`dev-tab-${dev.developer_id}`}>
            <span>{dev.name}</span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-zinc-500">{dev.models.filter(m => selected.includes(m.model_id)).length}/{dev.models.length}</span>
              {expandedDev[dev.developer_id] ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </div>
          </button>
          {expandedDev[dev.developer_id] && (
            <div className="px-3 pb-2 space-y-1 bg-zinc-900/40">
              {dev.models.map(m => (
                <label key={m.model_id} className="flex items-center gap-2 py-1 px-2 rounded cursor-pointer hover:bg-zinc-800/40 text-sm" data-testid={`model-checkbox-${m.model_id}`}>
                  <input type="checkbox" checked={selected.includes(m.model_id)} onChange={() => onToggle(m.model_id)}
                    className="rounded border-zinc-600 bg-zinc-800 text-emerald-500 focus:ring-emerald-500/30" />
                  <span className="text-zinc-300">{m.display_name || m.model_id}</span>
                </label>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ---- Context Settings Panel ----
function ContextPanel({ globalContext, setGlobalContext, perModelCtx, setPerModelCtx, selectedModels, show, onToggle }) {
  if (!show) return null;
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3 space-y-3" data-testid="context-panel">
      <div>
        <label className="text-xs text-zinc-400 font-medium mb-1 block">Global Context</label>
        <textarea value={globalContext} onChange={e => setGlobalContext(e.target.value)}
          placeholder="Context applied to all models..."
          rows={2}
          className="w-full rounded bg-zinc-800 border border-zinc-700 px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-500 focus:outline-none focus:border-emerald-500/50 resize-none"
          data-testid="global-context-input" />
      </div>
      {selectedModels.length > 0 && (
        <div className="space-y-2">
          <label className="text-xs text-zinc-400 font-medium">Per-Model Context</label>
          {selectedModels.map(modelId => {
            const ctx = perModelCtx[modelId] || {};
            const updateCtx = (field, val) => setPerModelCtx(prev => ({
              ...prev, [modelId]: { ...(prev[modelId] || {}), [field]: val }
            }));
            return (
              <div key={modelId} className="rounded border border-zinc-800 p-2 space-y-1.5" data-testid={`per-model-ctx-${modelId}`}>
                <div className="text-xs font-medium text-emerald-400">{modelId}</div>
                <input value={ctx.role || ''} onChange={e => updateCtx('role', e.target.value)}
                  placeholder="Role (e.g., expert coder, devil's advocate)"
                  className="w-full rounded bg-zinc-800 border border-zinc-700 px-2 py-1 text-xs text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500/50" />
                <input value={ctx.system_message || ''} onChange={e => updateCtx('system_message', e.target.value)}
                  placeholder="System message override"
                  className="w-full rounded bg-zinc-800 border border-zinc-700 px-2 py-1 text-xs text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500/50" />
                <input value={ctx.prompt_modifier || ''} onChange={e => updateCtx('prompt_modifier', e.target.value)}
                  placeholder="Prompt modifier (e.g., respond in JSON only)"
                  className="w-full rounded bg-zinc-800 border border-zinc-700 px-2 py-1 text-xs text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500/50" />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ---- Mode Selector ----
function ModeSelector({ mode, setMode, rounds, setRounds, synthModel, setSynthModel, allModels }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5" data-testid="mode-selector">
      {[
        { id: MODES.NORMAL, icon: Send, label: 'Normal', tip: 'Independent fan-out' },
        { id: MODES.SHARED_ALL, icon: Globe, label: 'Shared Room', tip: 'Each model sees all others' },
        { id: MODES.SHARED_SYNTH, icon: Zap, label: 'Synth Room', tip: 'Synthesize then share' },
        { id: MODES.DAISY, icon: Link2, label: 'Daisy Chain', tip: 'Sequential model→model' },
      ].map(m => (
        <button key={m.id} onClick={() => setMode(m.id)} title={m.tip}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-colors ${mode === m.id ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-600/30' : 'text-zinc-500 hover:text-zinc-300 border border-zinc-800 hover:border-zinc-700'}`}
          data-testid={`mode-${m.id}`}>
          <m.icon size={12} /> {m.label}
        </button>
      ))}
      {(mode === MODES.SHARED_ALL || mode === MODES.SHARED_SYNTH || mode === MODES.DAISY) && (
        <div className="flex items-center gap-1.5 ml-2">
          <label className="text-xs text-zinc-500">Rounds:</label>
          <input type="number" min={1} max={5} value={rounds} onChange={e => setRounds(Math.max(1, Math.min(5, parseInt(e.target.value) || 1)))}
            className="w-12 rounded bg-zinc-800 border border-zinc-700 px-1.5 py-1 text-xs text-zinc-200 text-center focus:outline-none focus:border-emerald-500/50"
            data-testid="rounds-input" />
        </div>
      )}
      {mode === MODES.SHARED_SYNTH && (
        <div className="flex items-center gap-1.5 ml-1">
          <label className="text-xs text-zinc-500">Synth model:</label>
          <select value={synthModel} onChange={e => setSynthModel(e.target.value)}
            className="rounded bg-zinc-800 border border-zinc-700 px-1.5 py-1 text-xs text-zinc-200 focus:outline-none focus:border-emerald-500/50"
            data-testid="synth-model-select">
            <option value="">Select...</option>
            {allModels.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
      )}
    </div>
  );
}

// ---- Response Panel ----
function ResponsePanel({ model, content, messageId, responseTime, feedback, onFeedback, isStreaming, compact, selected, onSelect, showSelect }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => { navigator.clipboard.writeText(content); setCopied(true); setTimeout(() => setCopied(false), 1500); };

  return (
    <div className={`rounded-lg border bg-zinc-900/60 overflow-hidden flex flex-col ${compact ? 'h-full' : ''} ${selected ? 'border-emerald-500/50' : 'border-zinc-800'}`} data-testid={`response-panel-${model}`}>
      <div className="flex items-center justify-between px-4 py-2 border-b border-zinc-800 bg-zinc-900/80 flex-shrink-0">
        <div className="flex items-center gap-2">
          {showSelect && (
            <button onClick={() => onSelect && onSelect(messageId)}
              className={`p-0.5 rounded transition-colors ${selected ? 'text-emerald-400' : 'text-zinc-600 hover:text-zinc-400'}`}
              data-testid={`select-response-${model}`}>
              <Check size={14} />
            </button>
          )}
          <span className="text-sm font-medium text-emerald-400" data-testid={`response-model-${model}`}>{model}</span>
          {isStreaming && <Loader2 size={14} className="animate-spin text-emerald-400" />}
          {responseTime && !isStreaming && (
            <span className="flex items-center gap-1 text-xs text-zinc-500"><Clock size={10} /> {(responseTime / 1000).toFixed(1)}s</span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button onClick={handleCopy} className="p-1.5 rounded hover:bg-zinc-700/60 text-zinc-400 hover:text-zinc-200 transition-colors" data-testid={`copy-btn-${model}`} title={copied ? 'Copied!' : 'Copy'}>
            <Copy size={14} />
          </button>
          {messageId && (
            <>
              <button onClick={() => onFeedback(messageId, 'up')} className={`p-1.5 rounded hover:bg-zinc-700/60 transition-colors ${feedback === 'up' ? 'text-emerald-400' : 'text-zinc-400 hover:text-zinc-200'}`} data-testid={`thumbsup-btn-${model}`}><ThumbsUp size={14} /></button>
              <button onClick={() => onFeedback(messageId, 'down')} className={`p-1.5 rounded hover:bg-zinc-700/60 transition-colors ${feedback === 'down' ? 'text-red-400' : 'text-zinc-400 hover:text-zinc-200'}`} data-testid={`thumbsdown-btn-${model}`}><ThumbsDown size={14} /></button>
            </>
          )}
        </div>
      </div>
      <div className={`p-4 prose prose-invert prose-sm max-w-none overflow-y-auto flex-1 ${compact ? '' : 'min-h-[120px] max-h-[600px]'}`}>
        {content ? <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          : isStreaming ? <span className="text-zinc-500 animate-pulse">Thinking...</span>
          : <span className="text-zinc-600">No response</span>}
      </div>
    </div>
  );
}

// ---- Response Layouts ----
function StackLayout({ responses, onFeedback, streamEntries, selectedIds, onSelect, showSelect }) {
  return (
    <div className="space-y-3">
      {responses.map(r => <ResponsePanel key={r.message_id} model={r.model} content={r.content} messageId={r.message_id}
        responseTime={r.response_time_ms} feedback={r.feedback} onFeedback={onFeedback} isStreaming={false}
        selected={selectedIds.has(r.message_id)} onSelect={onSelect} showSelect={showSelect} />)}
      {streamEntries.map(([model, data]) => <ResponsePanel key={`s-${model}`} model={model} content={data.content}
        messageId={null} responseTime={null} feedback={null} onFeedback={() => {}} isStreaming={true} showSelect={false} />)}
    </div>
  );
}

function SplitLayout({ responses, onFeedback, streamEntries, locked, selectedIds, onSelect, showSelect }) {
  const all = [
    ...responses.map(r => ({ ...r, isStreaming: false })),
    ...streamEntries.map(([model, data]) => ({ model, content: data.content, message_id: null, response_time_ms: null, feedback: null, isStreaming: true })),
  ];
  if (all.length === 0) return null;
  if (all.length === 1) { const r = all[0]; return <ResponsePanel model={r.model} content={r.content} messageId={r.message_id} responseTime={r.response_time_ms} feedback={r.feedback} onFeedback={onFeedback} isStreaming={r.isStreaming} showSelect={false} />; }
  return (
    <div className="h-[500px]">
      <PanelGroup direction="horizontal" data-testid="split-panel-group">
        {all.map((r, i) => (
          <React.Fragment key={r.message_id || `s-${r.model}`}>
            {i > 0 && <PanelResizeHandle className="w-2 bg-zinc-800 hover:bg-emerald-600/40 transition-colors rounded mx-0.5 cursor-col-resize" />}
            <Panel defaultSize={locked ? (100 / all.length) : undefined} minSize={15}>
              <ResponsePanel model={r.model} content={r.content} messageId={r.message_id} responseTime={r.response_time_ms}
                feedback={r.feedback} onFeedback={onFeedback} isStreaming={r.isStreaming} compact={true}
                selected={r.message_id ? selectedIds.has(r.message_id) : false} onSelect={onSelect} showSelect={showSelect} />
            </Panel>
          </React.Fragment>
        ))}
      </PanelGroup>
    </div>
  );
}

function CarouselLayout({ responses, onFeedback, streamEntries }) {
  const all = [
    ...responses.map(r => ({ ...r, isStreaming: false })),
    ...streamEntries.map(([model, data]) => ({ model, content: data.content, message_id: null, response_time_ms: null, feedback: null, isStreaming: true })),
  ];
  const [emblaRef, emblaApi] = useEmblaCarousel({ loop: true, align: 'center' });
  const [selectedIdx, setSelectedIdx] = useState(0);
  const onSelect = useCallback(() => { if (emblaApi) setSelectedIdx(emblaApi.selectedScrollSnap()); }, [emblaApi, setSelectedIdx]);
  useEffect(() => { if (!emblaApi) return; emblaApi.on('select', onSelect); onSelect(); return () => emblaApi.off('select', onSelect); }, [emblaApi, onSelect]);

  if (all.length === 0) return null;
  if (all.length === 1) { const r = all[0]; return <ResponsePanel model={r.model} content={r.content} messageId={r.message_id} responseTime={r.response_time_ms} feedback={r.feedback} onFeedback={onFeedback} isStreaming={r.isStreaming} showSelect={false} />; }
  return (
    <div data-testid="carousel-layout">
      <div className="flex items-center justify-between mb-2">
        <button onClick={() => emblaApi?.scrollPrev()} className="p-1 rounded hover:bg-zinc-800 text-zinc-400" data-testid="carousel-prev"><ChevronLeft size={16} /></button>
        <div className="flex gap-1.5">
          {all.map((r, i) => (
            <button key={r.message_id || `carousel-tab-${r.model}-${i}`} onClick={() => emblaApi?.scrollTo(i)}
              className={`px-2 py-0.5 rounded text-xs transition-colors ${i === selectedIdx ? 'bg-emerald-600/30 text-emerald-400 border border-emerald-600/40' : 'text-zinc-500 border border-zinc-800'}`}>
              {r.model}
            </button>
          ))}
        </div>
        <button onClick={() => emblaApi?.scrollNext()} className="p-1 rounded hover:bg-zinc-800 text-zinc-400" data-testid="carousel-next"><ChevronRight size={16} /></button>
      </div>
      <div className="overflow-hidden rounded-lg" ref={emblaRef}>
        <div className="flex">
          {all.map((r, i) => (
            <div key={r.message_id || `s-${r.model}`} className="flex-[0_0_100%] min-w-0 px-1">
              <ResponsePanel model={r.model} content={r.content} messageId={r.message_id} responseTime={r.response_time_ms}
                feedback={r.feedback} onFeedback={onFeedback} isStreaming={r.isStreaming} showSelect={false} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---- Synthesis Bar ----
function SynthesisBar({ selectedIds, allModels, onSynthesize, onClear }) {
  const [synthModel, setSynthModel] = useState('');
  const [synthPrompt, setSynthPrompt] = useState('Synthesize and analyze these AI responses:');
  if (selectedIds.size === 0) return null;
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-emerald-600/30 bg-emerald-950/20" data-testid="synthesis-bar">
      <Zap size={14} className="text-emerald-400 flex-shrink-0" />
      <span className="text-xs text-emerald-400 flex-shrink-0">{selectedIds.size} selected</span>
      <input value={synthPrompt} onChange={e => setSynthPrompt(e.target.value)} placeholder="Synthesis prompt..."
        className="flex-1 rounded bg-zinc-800 border border-zinc-700 px-2 py-1 text-xs text-zinc-200 focus:outline-none focus:border-emerald-500/50 min-w-0"
        data-testid="synthesis-prompt-input" />
      <select value={synthModel} onChange={e => setSynthModel(e.target.value)}
        className="rounded bg-zinc-800 border border-zinc-700 px-1.5 py-1 text-xs text-zinc-200 focus:outline-none"
        data-testid="synthesis-model-select">
        <option value="">Synth model...</option>
        {allModels.map(m => <option key={m} value={m}>{m}</option>)}
      </select>
      <button onClick={() => { if (synthModel) onSynthesize(synthModel, synthPrompt); }}
        disabled={!synthModel} className="px-2 py-1 rounded bg-emerald-600 text-xs text-white hover:bg-emerald-500 disabled:bg-zinc-700 disabled:text-zinc-500"
        data-testid="synthesize-btn">Synthesize</button>
      <button onClick={onClear} className="p-1 rounded text-zinc-500 hover:text-zinc-300" data-testid="clear-selection-btn"><X size={14} /></button>
    </div>
  );
}

// ---- Sidebar ----
function Sidebar({ threads, currentThread, onSelect, onNew, open, onClose }) {
  return (
    <>
      {open && <div className="fixed inset-0 bg-black/50 z-30 lg:hidden" onClick={onClose} />}
      <div className={`fixed top-0 left-0 h-full w-72 bg-zinc-950 border-r border-zinc-800 z-40 transition-transform duration-200 ${open ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 lg:relative lg:z-0`}>
        <div className="flex items-center justify-between p-4 border-b border-zinc-800">
          <span className="text-sm font-semibold text-zinc-200">Threads</span>
          <button onClick={onNew} className="p-1.5 rounded hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200" data-testid="new-thread-btn"><Plus size={16} /></button>
        </div>
        <div className="overflow-y-auto h-[calc(100%-60px)] p-2 space-y-1">
          {threads.map(t => (
            <button key={t.thread_id} onClick={() => { onSelect(t.thread_id); onClose(); }}
              className={`w-full text-left px-3 py-2 rounded-md text-sm truncate transition-colors ${currentThread === t.thread_id ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200'}`}
              data-testid={`thread-item-${t.thread_id}`}>
              <div className="flex items-center gap-2"><MessageSquare size={14} className="flex-shrink-0" /><span className="truncate">{t.title || 'Untitled'}</span></div>
              <div className="text-xs text-zinc-600 mt-0.5">{t.models_used?.join(', ') || ''}</div>
            </button>
          ))}
          {threads.length === 0 && <div className="text-center text-xs text-zinc-600 py-8">No threads yet</div>}
        </div>
      </div>
    </>
  );
}

// ---- Layout + Header Toggles ----
function LayoutToggle({ layout, setLayout, splitLocked, setSplitLocked }) {
  return (
    <div className="flex items-center gap-1" data-testid="layout-toggle">
      {[{ id: LAYOUTS.STACK, Icon: Layers, t: 'Stack' }, { id: LAYOUTS.SPLIT, Icon: Columns2, t: 'Split' }, { id: LAYOUTS.CAROUSEL, Icon: GalleryHorizontal, t: 'Carousel' }].map(l => (
        <button key={l.id} onClick={() => setLayout(l.id)} title={l.t}
          className={`p-1.5 rounded transition-colors ${layout === l.id ? 'bg-zinc-700 text-emerald-400' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800'}`}
          data-testid={`layout-${l.id}-btn`}><l.Icon size={16} /></button>
      ))}
      {layout === LAYOUTS.SPLIT && (
        <button onClick={() => setSplitLocked(l => !l)} title={splitLocked ? 'Unlock' : 'Lock 50/50'}
          className={`p-1.5 rounded transition-colors ${splitLocked ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-600/30' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800'}`}
          data-testid="split-lock-btn"><Lock size={14} /></button>
      )}
    </div>
  );
}

// ---- Main ChatPage ----
export default function ChatPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { threads, currentThread, messages, loading, streaming, error, fetchThreads, loadThread, sendPrompt, newThread, submitFeedback, addOptimisticMessage } = useChat();

  const [input, setInput] = useState('');
  const [registry, setRegistry] = useState([]);
  const [selectedModels, setSelectedModels] = useState(['gpt-4o-mini']);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showModels, setShowModels] = useState(false);
  const [showContext, setShowContext] = useState(false);
  const [globalContext, setGlobalContext] = useState('');
  const [perModelCtx, setPerModelCtx] = useState({});
  const [mode, setMode] = useState(MODES.NORMAL);
  const [rounds, setRounds] = useState(1);
  const [synthModel, setSynthModel] = useState('');
  const [layout, setLayout] = useState(() => localStorage.getItem('hub_layout') || LAYOUTS.STACK);
  const [splitLocked, setSplitLocked] = useState(false);
  const [selectedResponseIds, setSelectedResponseIds] = useState(new Set());
  const [synthesizing, setSynthesizing] = useState(false);
  const [advancedLoading, setAdvancedLoading] = useState(false);
  const responseEndRef = useRef(null);
  const textareaRef = useRef(null);

  const allModelIds = registry.flatMap(d => d.models.map(m => m.model_id));

  useEffect(() => { localStorage.setItem('hub_layout', layout); }, [layout]);
  useEffect(() => {
    fetchThreads();
    axios.get(`${API}/v1/models`).then(res => setRegistry(res.data.developers || [])).catch((modelError) => {
      console.error('Failed to load model registry:', modelError);
    });
  }, [fetchThreads]);
  useEffect(() => { if (responseEndRef.current) responseEndRef.current.scrollIntoView({ behavior: 'smooth' }); }, [messages, streaming]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || selectedModels.length === 0 || loading) return;
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';

    const pmc = {};
    for (const mid of selectedModels) {
      if (perModelCtx[mid] && Object.values(perModelCtx[mid]).some(v => v)) {
        pmc[mid] = perModelCtx[mid];
      }
    }

    if (mode === MODES.NORMAL) {
      sendPrompt(trimmed, selectedModels, { globalContext, perModelContext: Object.keys(pmc).length ? pmc : undefined });
    } else {
      // Advanced modes: shared room, synth room, daisy chain
      const headers = { 'Content-Type': 'application/json' };

      let endpoint, body;
      if (mode === MODES.SHARED_ALL) {
        endpoint = `${API}/v1/a0/shared-room`;
        body = { message: trimmed, models: selectedModels, rounds, mode: 'all', global_context: globalContext || undefined, per_model_context: Object.keys(pmc).length ? pmc : undefined };
      } else if (mode === MODES.SHARED_SYNTH) {
        endpoint = `${API}/v1/a0/shared-room`;
        body = { message: trimmed, models: selectedModels, rounds, mode: 'synthesized', synthesis_model: synthModel || selectedModels[0], global_context: globalContext || undefined, per_model_context: Object.keys(pmc).length ? pmc : undefined };
      } else if (mode === MODES.DAISY) {
        endpoint = `${API}/v1/a0/daisy-chain`;
        body = { message: trimmed, models: selectedModels, rounds, global_context: globalContext || undefined, per_model_context: Object.keys(pmc).length ? pmc : undefined };
      }

      // Show user message + loading state immediately
      addOptimisticMessage({
        message_id: `msg_temp_${Date.now()}`, role: 'user', content: trimmed,
        model: 'user', timestamp: new Date().toISOString(),
      });
      setAdvancedLoading(true);

      try {
        const res = await fetch(endpoint, { method: 'POST', headers, credentials: 'include', body: JSON.stringify(body) });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data.thread_id) {
          await loadThread(data.thread_id);
          fetchThreads();
        }
      } catch (err) {
        console.error('Advanced mode error:', err);
      } finally {
        setAdvancedLoading(false);
      }
    }
  };

  const handleKeyDown = (e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); handleSend(); } };
  const toggleModel = (modelId) => setSelectedModels(prev => prev.includes(modelId) ? prev.filter(m => m !== modelId) : [...prev, modelId]);
  const handleLogout = async () => { await logout(); navigate('/auth'); };

  const toggleResponseSelect = (msgId) => {
    setSelectedResponseIds(prev => {
      const next = new Set(prev);
      next.has(msgId) ? next.delete(msgId) : next.add(msgId);
      return next;
    });
  };

  const handleSynthesize = async (targetModel, prompt) => {
    if (selectedResponseIds.size === 0 || !targetModel) return;
    setSynthesizing(true);
    try {
      const headers = { 'Content-Type': 'application/json' };
      const res = await fetch(`${API}/v1/a0/synthesize`, {
        method: 'POST', headers, credentials: 'include',
        body: JSON.stringify({
          source_message_ids: [...selectedResponseIds],
          target_models: [targetModel],
          synthesis_prompt: prompt,
          thread_id: currentThread,
        }),
      });
      const data = await res.json();
      if (data.thread_id) {
        loadThread(data.thread_id);
        setSelectedResponseIds(new Set());
      }
    } catch (err) {
      console.error('Synthesis error:', err);
    } finally {
      setSynthesizing(false);
    }
  };

  const getGroups = () => {
    const groups = []; let cur = null;
    for (const msg of messages) {
      if (msg.role === 'user') { if (cur) groups.push(cur); cur = { userMsg: msg, responses: [] }; }
      else if (msg.role === 'assistant' && cur) { cur.responses.push(msg); }
    }
    if (cur) groups.push(cur);
    return groups;
  };

  const streamEntries = Object.entries(streaming);
  const groups = getGroups();
  const showSelect = messages.some(m => m.role === 'assistant');

  const renderResponseGroup = (responses, groupStreaming = []) => {
    if (layout === LAYOUTS.SPLIT) return <SplitLayout responses={responses} onFeedback={submitFeedback} streamEntries={groupStreaming} locked={splitLocked} selectedIds={selectedResponseIds} onSelect={toggleResponseSelect} showSelect={showSelect} />;
    if (layout === LAYOUTS.CAROUSEL) return <CarouselLayout responses={responses} onFeedback={submitFeedback} streamEntries={groupStreaming} />;
    return <StackLayout responses={responses} onFeedback={submitFeedback} streamEntries={groupStreaming} selectedIds={selectedResponseIds} onSelect={toggleResponseSelect} showSelect={showSelect} />;
  };

  const handleTextareaInput = (e) => { setInput(e.target.value); e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px'; };

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-200" data-testid="chat-page">
      <Sidebar threads={threads} currentThread={currentThread} onSelect={loadThread}
        onNew={() => { newThread(); setSidebarOpen(false); }} open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <button onClick={() => setSidebarOpen(true)} className="lg:hidden p-1.5 rounded hover:bg-zinc-800 text-zinc-400" data-testid="sidebar-toggle"><Menu size={20} /></button>
            <h1 className="text-base font-semibold tracking-tight">Multi-Model Hub</h1>
            <span className="text-xs text-zinc-600 hidden sm:inline">v1.0.2-S9</span>
          </div>
          <div className="flex items-center gap-3">
            <LayoutToggle layout={layout} setLayout={setLayout} splitLocked={splitLocked} setSplitLocked={setSplitLocked} />
            <div className="w-px h-5 bg-zinc-800" />
            <button onClick={() => navigate('/analysis')} className="p-2 rounded hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200" data-testid="analysis-btn" title="Transcript Analysis"><FileUp size={18} /></button>
            <button onClick={() => navigate('/settings')} className="p-2 rounded hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200" data-testid="settings-btn"><Settings size={18} /></button>
            <button onClick={handleLogout} className="p-2 rounded hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200" data-testid="logout-btn"><LogOut size={18} /></button>
          </div>
        </header>

        {/* Prompt + Controls */}
        <div className="px-4 py-3 border-b border-zinc-800 space-y-2 bg-zinc-950/60">
          <div className="flex gap-3">
            <div className="flex-1">
              <textarea ref={textareaRef} value={input} onChange={handleTextareaInput} onKeyDown={handleKeyDown}
                placeholder="Enter your prompt... (Ctrl+Enter to send)" rows={2}
                className="w-full rounded-lg bg-zinc-900 border border-zinc-700 px-4 py-3 text-sm text-zinc-200 placeholder:text-zinc-500 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 resize-none transition-colors"
                data-testid="prompt-input" />
            </div>
            <button onClick={handleSend} disabled={!input.trim() || selectedModels.length === 0 || loading || advancedLoading}
              className="self-end px-4 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white font-medium text-sm transition-colors flex items-center gap-2"
              data-testid="send-btn">
              {(loading || advancedLoading) ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              <span className="hidden sm:inline">Send</span>
            </button>
          </div>

          {/* Mode + Context toggles */}
          <div className="flex flex-wrap items-center gap-3">
            <ModeSelector mode={mode} setMode={setMode} rounds={rounds} setRounds={setRounds} synthModel={synthModel} setSynthModel={setSynthModel} allModels={allModelIds} />
            <div className="flex items-center gap-1.5 ml-auto">
              <button onClick={() => setShowContext(!showContext)}
                className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-colors ${showContext ? 'bg-blue-600/20 text-blue-400 border border-blue-600/30' : 'text-zinc-500 border border-zinc-800 hover:text-zinc-300'}`}
                data-testid="toggle-context-btn"><Sliders size={12} /> Context</button>
              <button onClick={() => setShowModels(!showModels)}
                className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-colors ${showModels ? 'bg-zinc-700 text-zinc-200' : 'text-zinc-500 border border-zinc-800 hover:text-zinc-300'}`}
                data-testid="toggle-models-btn">Models ({selectedModels.length})</button>
            </div>
          </div>

          {/* Context Panel */}
          <ContextPanel globalContext={globalContext} setGlobalContext={setGlobalContext} perModelCtx={perModelCtx}
            setPerModelCtx={setPerModelCtx} selectedModels={selectedModels} show={showContext} onToggle={() => setShowContext(!showContext)} />

          {/* Model Selector */}
          {showModels && (
            <div className="max-h-[250px] overflow-y-auto">
              <ModelSelector registry={registry} selected={selectedModels} onToggle={toggleModel} />
            </div>
          )}
        </div>

        {/* Synthesis Bar */}
        {selectedResponseIds.size > 0 && (
          <div className="px-4 py-2 border-b border-zinc-800">
            <SynthesisBar selectedIds={selectedResponseIds} allModels={allModelIds}
              onSynthesize={handleSynthesize} onClear={() => setSelectedResponseIds(new Set())} />
          </div>
        )}

        {/* Responses */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
          {groups.length === 0 && streamEntries.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-zinc-600 space-y-3">
              <MessageSquare size={48} strokeWidth={1} />
              <p className="text-sm">Select models and send a prompt to begin</p>
            </div>
          )}
          {groups.map((group, gi) => (
            <div key={gi} className="space-y-3">
              <div className="flex justify-end">
                <div className="max-w-[85%] rounded-xl px-4 py-3 bg-emerald-600/20 border border-emerald-600/30 text-zinc-200 text-sm" data-testid={`user-message-${gi}`}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{group.userMsg.content}</ReactMarkdown>
                </div>
              </div>
              {renderResponseGroup(group.responses, gi === groups.length - 1 ? streamEntries : [])}
            </div>
          ))}
          {groups.length === 0 && streamEntries.length > 0 && renderResponseGroup([], streamEntries)}
          {advancedLoading && (
            <div className="flex items-center gap-3 px-4 py-3 rounded-lg border border-zinc-800 bg-zinc-900/40" data-testid="advanced-loading">
              <Loader2 size={18} className="animate-spin text-emerald-400" />
              <span className="text-sm text-zinc-400">
                {mode === MODES.DAISY ? 'Running daisy chain...' : mode === MODES.SHARED_SYNTH ? 'Synthesizing in shared room...' : 'Processing shared room...'}
                {rounds > 1 ? ` (${rounds} rounds)` : ''}
              </span>
            </div>
          )}
          {error && (
            <div className="flex items-center gap-2 px-4 py-2 rounded-lg border border-red-600/30 bg-red-950/20 text-sm text-red-400" data-testid="chat-error">
              <X size={14} /> {error}
            </div>
          )}
          <div ref={responseEndRef} />
        </div>
      </div>
    </div>
  );
}
