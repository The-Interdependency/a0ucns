import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { ArrowLeft, Activity, Clock, ThumbsUp, ThumbsDown, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
axios.defaults.withCredentials = true;

const EDCM_LABELS = {
  constraint_mismatch_density: { label: 'Constraint Mismatch Density', desc: 'Measures divergence between model constraints and outputs', color: '#EF4444' },
  fixation_coefficient: { label: 'Fixation Coefficient', desc: 'Degree of repetitive pattern adherence', color: '#F59E0B' },
  escalation_gradient: { label: 'Escalation Gradient', desc: 'Rate of response intensity increase', color: '#8B5CF6' },
  context_drift_index: { label: 'Context Drift Index', desc: 'Semantic drift from original prompt context', color: '#3B82F6' },
  load_saturation_index: { label: 'Load Saturation Index', desc: 'Token/context window utilization ratio', color: '#06B6D4' },
};

const MODEL_COLORS = {
  gpt: '#10A37F',
  claude: '#D97757',
  gemini: '#4285F4',
  perplexity: '#22B8CF',
  grok: '#FFFFFF',
  deepseek: '#4D6BFE'
};

const getModelColor = (model) => {
  if (!model) return '#888';
  const lower = model.toLowerCase();
  for (const [key, color] of Object.entries(MODEL_COLORS)) {
    if (lower.includes(key)) return color;
  }
  return '#888';
};

function MetricGauge({ value, label, desc, color }) {
  const pct = value != null ? Math.min(100, Math.max(0, value * 100)) : 0;
  const isStub = value == null;

  return (
    <div className="space-y-2" data-testid={`edcm-metric-${label.toLowerCase().replace(/\s/g, '-')}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium" style={{ color }}>{label}</span>
        <span className="text-xs font-mono">
          {isStub ? <Badge variant="outline" className="text-[9px]">Awaiting a0</Badge> : value.toFixed(3)}
        </span>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color, opacity: isStub ? 0.3 : 1 }}
        />
      </div>
      <p className="text-[10px] text-muted-foreground">{desc}</p>
    </div>
  );
}

function ResponseTimeBar({ model, avg_ms, min_ms, max_ms, count }) {
  const maxBar = 10000;
  const pct = Math.min(100, (avg_ms / maxBar) * 100);

  return (
    <div className="flex items-center gap-3" data-testid={`rt-bar-${model}`}>
      <span className="text-xs font-mono w-36 truncate" style={{ color: getModelColor(model) }}>{model}</span>
      <div className="flex-1 h-3 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: getModelColor(model) }}
        />
      </div>
      <span className="text-xs font-mono w-20 text-right">{avg_ms}ms</span>
      <span className="text-[10px] text-muted-foreground w-10 text-right">({count})</span>
    </div>
  );
}

function FeedbackRow({ model, up, down }) {
  const total = up + down;
  const upPct = total > 0 ? (up / total) * 100 : 50;

  return (
    <div className="flex items-center gap-3" data-testid={`fb-row-${model}`}>
      <span className="text-xs font-mono w-36 truncate" style={{ color: getModelColor(model) }}>{model}</span>
      <div className="flex-1 h-3 bg-muted rounded-full overflow-hidden flex">
        <div className="h-full bg-emerald-500 transition-all" style={{ width: `${upPct}%` }} />
        <div className="h-full bg-red-500 transition-all" style={{ width: `${100 - upPct}%` }} />
      </div>
      <div className="flex items-center gap-2 text-xs">
        <span className="flex items-center gap-0.5 text-emerald-400">
          <ThumbsUp className="h-3 w-3" />{up}
        </span>
        <span className="flex items-center gap-0.5 text-red-400">
          <ThumbsDown className="h-3 w-3" />{down}
        </span>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/edcm/dashboard`);
      setData(res.data);
    } catch (err) {
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDashboard(); }, []);

  const latestEdcm = data?.edcm_metrics?.[0] || {};

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-3xl mx-auto p-3 sm:p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={() => navigate('/chat')} data-testid="back-to-chat-btn">
              <ArrowLeft className="h-4 w-4 mr-1" /> Chat
            </Button>
            <h1 className="text-lg font-bold" style={{ fontFamily: 'Manrope, sans-serif' }}>EDCM Dashboard</h1>
          </div>
          <Button variant="ghost" size="sm" onClick={fetchDashboard} disabled={loading} data-testid="refresh-dashboard-btn">
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <Card className="bg-card border-border">
            <CardContent className="p-3 text-center">
              <div className="text-2xl font-bold">{data?.total_conversations ?? '-'}</div>
              <div className="text-[10px] text-muted-foreground">Conversations</div>
            </CardContent>
          </Card>
          <Card className="bg-card border-border">
            <CardContent className="p-3 text-center">
              <div className="text-2xl font-bold">{data?.total_messages ?? '-'}</div>
              <div className="text-[10px] text-muted-foreground">AI Responses</div>
            </CardContent>
          </Card>
        </div>

        {/* EDCM Metrics */}
        <Card className="mb-4 border-border" data-testid="edcm-metrics-card">
          <CardHeader className="p-3 pb-1">
            <CardTitle className="text-sm flex items-center gap-2">
              <Activity className="h-4 w-4" /> EDCM Metrics
              <Badge variant="outline" className="text-[9px] ml-auto">Stubs &mdash; Fed by a0</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3 space-y-3">
            {Object.entries(EDCM_LABELS).map(([key, meta]) => (
              <MetricGauge
                key={key}
                value={latestEdcm[key] ?? null}
                label={meta.label}
                desc={meta.desc}
                color={meta.color}
              />
            ))}
          </CardContent>
        </Card>

        {/* Response Times */}
        <Card className="mb-4 border-border" data-testid="response-times-card">
          <CardHeader className="p-3 pb-1">
            <CardTitle className="text-sm flex items-center gap-2">
              <Clock className="h-4 w-4" /> Response Times
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3 space-y-2">
            {data?.response_times?.length > 0 ? (
              data.response_times.map(rt => (
                <ResponseTimeBar key={rt.model} {...rt} />
              ))
            ) : (
              <div className="text-xs text-muted-foreground text-center py-4">
                No response data yet. Start chatting to see model performance.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Feedback Stats */}
        <Card className="mb-4 border-border" data-testid="feedback-stats-card">
          <CardHeader className="p-3 pb-1">
            <CardTitle className="text-sm flex items-center gap-2">
              <ThumbsUp className="h-4 w-4" /> Feedback Ratings
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3 space-y-2">
            {data?.feedback_stats?.length > 0 ? (
              data.feedback_stats.map(fb => (
                <FeedbackRow key={fb.model} {...fb} />
              ))
            ) : (
              <div className="text-xs text-muted-foreground text-center py-4">
                No feedback data yet. Use thumbs up/down on responses.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
