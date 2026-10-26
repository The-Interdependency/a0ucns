import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  ArrowLeft, Upload, FileText, AlertTriangle, ChevronDown, ChevronRight,
  Loader2, BarChart3, User, Clock, Flag
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// ---- Metric Bar ----
function MetricBar({ name, value, label }) {
  const pct = Math.round(value * 100);
  const color = value >= 0.8 ? 'bg-red-500' : value >= 0.5 ? 'bg-amber-500' : 'bg-emerald-500';
  return (
    <div className="space-y-1" data-testid={`metric-bar-${name}`}>
      <div className="flex items-center justify-between text-xs">
        <span className="text-zinc-400 font-medium">{name}</span>
        <span className="text-zinc-300">{pct}%</span>
      </div>
      <div className="h-2 rounded-full bg-zinc-800 overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
      </div>
      {label && <div className="text-xs text-zinc-500">{label}</div>}
    </div>
  );
}

// ---- Turn Card ----
function TurnCard({ turn, expanded, onToggle }) {
  const hasFlagsArr = turn.flags && turn.flags.length > 0;
  return (
    <div className={`rounded-lg border overflow-hidden transition-colors ${hasFlagsArr ? 'border-amber-600/40 bg-amber-950/10' : 'border-zinc-800 bg-zinc-900/40'}`}
      data-testid={`turn-card-${turn.turn_index}`}>
      <button onClick={onToggle} className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-zinc-800/30 transition-colors">
        <div className="flex items-center gap-3">
          <User size={14} className="text-zinc-500 flex-shrink-0" />
          <span className="text-sm font-medium text-zinc-200">{turn.speaker}</span>
          <span className="text-xs text-zinc-600">Turn {turn.turn_index}</span>
          {hasFlagsArr && (
            <span className="flex items-center gap-1 text-xs text-amber-400">
              <Flag size={10} /> {turn.flags.length} flag{turn.flags.length > 1 ? 's' : ''}
            </span>
          )}
        </div>
        {expanded ? <ChevronDown size={14} className="text-zinc-500" /> : <ChevronRight size={14} className="text-zinc-500" />}
      </button>
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-zinc-800/50">
          <div className="text-sm text-zinc-300 mt-3">{turn.content}</div>
          {hasFlagsArr && (
            <div className="space-y-1">
              {turn.flags.map((f, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-amber-400 bg-amber-950/20 rounded px-2 py-1">
                  <AlertTriangle size={12} className="flex-shrink-0 mt-0.5" />
                  <span>{f}</span>
                </div>
              ))}
            </div>
          )}
          <div className="grid grid-cols-3 gap-2 mt-2">
            {Object.entries(turn.metrics || {}).map(([name, m]) => (
              <MetricBar key={name} name={name} value={m.value} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---- Report View ----
function ReportView({ report }) {
  const [expandedTurns, setExpandedTurns] = useState(new Set(report.flagged_turns || []));
  const [showAll, setShowAll] = useState(false);

  const toggleTurn = (idx) => {
    setExpandedTurns(prev => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  const displayTurns = showAll ? report.turns : report.turns.filter((_, i) => (report.flagged_turns || []).includes(i) || i < 3);

  return (
    <div className="space-y-6" data-testid="report-view">
      {/* Summary Metrics */}
      <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
        <h3 className="text-sm font-semibold text-zinc-200 mb-3 flex items-center gap-2">
          <BarChart3 size={16} className="text-emerald-400" /> Summary Metrics
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {Object.entries(report.summary_metrics || {}).map(([name, m]) => (
            <MetricBar key={name} name={name} value={m.value} />
          ))}
        </div>
      </div>

      {/* Narrative Summary */}
      {report.narrative_summary && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
          <h3 className="text-sm font-semibold text-zinc-200 mb-3">Analysis Summary</h3>
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{report.narrative_summary}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* Flagged Turns Summary */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-200">
          Turns ({report.turn_count} total, {(report.flagged_turns || []).length} flagged)
        </h3>
        <button onClick={() => setShowAll(!showAll)} className="text-xs text-emerald-400 hover:text-emerald-300" data-testid="show-all-turns-btn">
          {showAll ? 'Show flagged only' : 'Show all turns'}
        </button>
      </div>

      {/* Turn Cards */}
      <div className="space-y-2">
        {displayTurns.map(turn => (
          <TurnCard key={turn.turn_index} turn={turn} expanded={expandedTurns.has(turn.turn_index)}
            onToggle={() => toggleTurn(turn.turn_index)} />
        ))}
      </div>
    </div>
  );
}

// ---- Main Page ----
export default function AnalysisPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState('upload');
  const [text, setText] = useState('');
  const [model, setModel] = useState('gpt-4o-mini');
  const [goal, setGoal] = useState('');
  const [constraints, setConstraints] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [report, setReport] = useState(null);
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [models, setModels] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    axios.get(`${API}/v1/models`).then(res => {
      const allModels = [];
      (res.data.developers || []).forEach(d => {
        d.models.forEach(m => allModels.push({ id: m.model_id, name: m.display_name || m.model_id, dev: d.name }));
      });
      setModels(allModels);
    }).catch(() => {});
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const res = await axios.get(`${API}/v1/analysis/reports`);
      setReports(res.data || []);
    } catch {}
  };

  const handleAnalyze = async () => {
    if (!text.trim()) return;
    setAnalyzing(true);
    setError('');
    try {
      const res = await axios.post(`${API}/v1/analysis/transcript`, {
        transcript_text: text,
        model,
        goal_text: goal,
        declared_constraints: constraints ? constraints.split(',').map(c => c.trim()) : [],
      });
      setReport(res.data);
      setTab('report');
      fetchReports();
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setText(ev.target?.result || '');
    reader.readAsText(file);
  };

  const loadReport = async (analysisId) => {
    try {
      const res = await axios.get(`${API}/v1/analysis/reports/${analysisId}`);
      setReport(res.data);
      setTab('report');
    } catch {}
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-200" data-testid="analysis-page">
      <header className="flex items-center gap-3 px-4 py-3 border-b border-zinc-800">
        <button onClick={() => navigate('/chat')} className="p-1.5 rounded hover:bg-zinc-800 text-zinc-400" data-testid="back-to-chat-btn">
          <ArrowLeft size={18} />
        </button>
        <h1 className="text-base font-semibold">Transcript Analysis</h1>
        <span className="text-xs text-zinc-600">EDCM-powered</span>
      </header>

      <div className="max-w-4xl mx-auto p-4">
        {/* Tabs */}
        <div className="flex gap-1 border-b border-zinc-800 pb-1 mb-4">
          <button onClick={() => setTab('upload')}
            className={`px-4 py-2 text-sm rounded-t transition-colors ${tab === 'upload' ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300'}`}
            data-testid="tab-upload">
            Upload
          </button>
          <button onClick={() => setTab('report')} disabled={!report}
            className={`px-4 py-2 text-sm rounded-t transition-colors ${tab === 'report' ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300'} disabled:opacity-40`}
            data-testid="tab-report">
            Report
          </button>
          <button onClick={() => setTab('history')}
            className={`px-4 py-2 text-sm rounded-t transition-colors ${tab === 'history' ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300'}`}
            data-testid="tab-history">
            History ({reports.length})
          </button>
        </div>

        {/* Upload Tab */}
        {tab === 'upload' && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 px-3 py-2 rounded-lg border border-zinc-700 hover:border-zinc-600 cursor-pointer text-sm text-zinc-300 transition-colors"
                data-testid="file-upload-label">
                <Upload size={16} /> Upload File
                <input type="file" accept=".txt,.md,.csv" onChange={handleFileUpload} className="hidden" data-testid="file-upload-input" />
              </label>
              <span className="text-xs text-zinc-500">or paste below</span>
            </div>

            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder="Paste transcript text here...&#10;&#10;Speaker A: Hello&#10;Speaker B: Hi there&#10;..."
              rows={10}
              className="w-full rounded-lg bg-zinc-900 border border-zinc-700 px-4 py-3 text-sm text-zinc-200 placeholder:text-zinc-500 focus:outline-none focus:border-emerald-500/50 resize-y"
              data-testid="transcript-input"
            />

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-xs text-zinc-400 mb-1 block">Model</label>
                <select value={model} onChange={e => setModel(e.target.value)}
                  className="w-full rounded bg-zinc-900 border border-zinc-700 px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-emerald-500/50"
                  data-testid="model-select">
                  {models.map(m => <option key={m.id} value={m.id}>{m.name} ({m.dev})</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-zinc-400 mb-1 block">Goal / Topic (optional)</label>
                <input value={goal} onChange={e => setGoal(e.target.value)} placeholder="e.g., Contract negotiation"
                  className="w-full rounded bg-zinc-900 border border-zinc-700 px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-emerald-500/50"
                  data-testid="goal-input" />
              </div>
              <div>
                <label className="text-xs text-zinc-400 mb-1 block">Constraints (comma-separated)</label>
                <input value={constraints} onChange={e => setConstraints(e.target.value)} placeholder="e.g., accuracy, honesty"
                  className="w-full rounded bg-zinc-900 border border-zinc-700 px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-emerald-500/50"
                  data-testid="constraints-input" />
              </div>
            </div>

            {error && <div className="text-sm text-red-400 bg-red-950/20 rounded-lg px-3 py-2" data-testid="analysis-error">{error}</div>}

            <button onClick={handleAnalyze} disabled={!text.trim() || analyzing}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white font-medium text-sm transition-colors"
              data-testid="analyze-btn">
              {analyzing ? <><Loader2 size={16} className="animate-spin" /> Analyzing...</> : <><BarChart3 size={16} /> Analyze Transcript</>}
            </button>
          </div>
        )}

        {/* Report Tab */}
        {tab === 'report' && report && <ReportView report={report} />}

        {/* History Tab */}
        {tab === 'history' && (
          <div className="space-y-2">
            {reports.length === 0 && <div className="text-sm text-zinc-500 py-8 text-center">No reports yet</div>}
            {reports.map(r => (
              <button key={r.analysis_id} onClick={() => loadReport(r.analysis_id)}
                className="w-full text-left rounded-lg border border-zinc-800 p-3 hover:bg-zinc-800/40 transition-colors"
                data-testid={`report-item-${r.analysis_id}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText size={14} className="text-zinc-500" />
                    <span className="text-sm text-zinc-200">{r.title || 'Untitled'}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-zinc-500">
                    <span>{r.turn_count} turns</span>
                    <span className={r.flagged_turns?.length > 0 ? 'text-amber-400' : ''}>{r.flagged_turns?.length || 0} flagged</span>
                    <span>{r.model_used}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
