import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { ArrowLeft, Save, Copy, RefreshCw, CreditCard } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Slider } from '../components/ui/slider';
import { Switch } from '../components/ui/switch';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { ConsoleLogViewer } from '../components/console/ConsoleLogViewer';
import { ConsoleContextEditor } from '../components/console/ConsoleContextEditor';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
axios.defaults.withCredentials = true;

const getAuthConfig = () => undefined;

const parseJsonField = (label, rawValue) => {
  const trimmed = String(rawValue || '').trim();
  if (!trimmed) return null;
  try {
    return JSON.parse(trimmed);
  } catch {
    throw new Error(`${label} must be valid JSON`);
  }
};

export default function ConsolePage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('cost');
  const [loading, setLoading] = useState(true);
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [savingContext, setSavingContext] = useState(false);

  const [summary, setSummary] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [authInfo, setAuthInfo] = useState(null);
  const [preferences, setPreferences] = useState({
    enforce_token_limit: false,
    enforce_cost_limit: false,
    token_limit: 25000,
    cost_limit_usd: 25,
  });

  const [contextLogs, setContextLogs] = useState([]);
  const [selectedContextId, setSelectedContextId] = useState('');
  const [contextEditor, setContextEditor] = useState({
    message: '',
    global_context: '',
    context_mode: 'compartmented',
    shared_room_mode: 'parallel_all',
    model_roles: '{}',
    per_model_messages: '{}',
    shared_pairs: '{}',
  });

  const selectedContext = useMemo(
    () => contextLogs.find((log) => log.id === selectedContextId) || null,
    [contextLogs, selectedContextId],
  );

  const populateContextEditor = React.useCallback((log) => {
    if (!log) {
      setContextEditor({
        message: '',
        global_context: '',
        context_mode: 'compartmented',
        shared_room_mode: 'parallel_all',
        model_roles: '{}',
        per_model_messages: '{}',
        shared_pairs: '{}',
      });
      return;
    }

    setContextEditor({
      message: log.message || '',
      global_context: log.global_context || '',
      context_mode: log.context_mode || 'compartmented',
      shared_room_mode: log.shared_room_mode || 'parallel_all',
      model_roles: JSON.stringify(log.model_roles || {}, null, 2),
      per_model_messages: JSON.stringify(log.per_model_messages || {}, null, 2),
      shared_pairs: JSON.stringify(log.shared_pairs || {}, null, 2),
    });
  }, []);

  const loadConsoleData = React.useCallback(async () => {
    setLoading(true);
    try {
      const authConfig = getAuthConfig();
      const [summaryRes, dashboardRes, prefsRes, contextRes, authRes] = await Promise.all([
        axios.get(`${API}/payments/summary`, authConfig),
        axios.get(`${API}/edcm/dashboard`, authConfig),
        axios.get(`${API}/console/preferences`, authConfig),
        axios.get(`${API}/console/context-logs?limit=60`, authConfig),
        axios.get(`${API}/auth/me`, authConfig),
      ]);

      setSummary(summaryRes.data);
      setDashboard(dashboardRes.data);
      setPreferences(prefsRes.data);
      setContextLogs(contextRes.data.logs || []);
      setAuthInfo(authRes.data);

      const firstId = contextRes.data.logs?.[0]?.id || '';
      setSelectedContextId((prev) => prev || firstId);
      populateContextEditor(contextRes.data.logs?.[0] || null);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to load console data');
    } finally {
      setLoading(false);
    }
  }, [populateContextEditor]);

  useEffect(() => {
    loadConsoleData();
  }, [loadConsoleData]);

  useEffect(() => {
    populateContextEditor(selectedContext);
  }, [populateContextEditor, selectedContext]);

  const savePreferences = async () => {
    setSavingPrefs(true);
    try {
      const authConfig = getAuthConfig();
      const payload = {
        enforce_token_limit: !!preferences.enforce_token_limit,
        enforce_cost_limit: !!preferences.enforce_cost_limit,
        token_limit: Number(preferences.token_limit),
        cost_limit_usd: Number(preferences.cost_limit_usd),
      };
      const response = await axios.put(`${API}/console/preferences`, payload, authConfig);
      setPreferences(response.data);
      toast.success('Limit controls saved');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save preferences');
    } finally {
      setSavingPrefs(false);
    }
  };

  const saveContextLog = async () => {
    if (!selectedContextId) return;

    setSavingContext(true);
    try {
      const authConfig = getAuthConfig();
      const payload = {
        message: contextEditor.message,
        global_context: contextEditor.global_context,
        context_mode: contextEditor.context_mode,
        shared_room_mode: contextEditor.shared_room_mode,
        model_roles: parseJsonField('Model roles', contextEditor.model_roles),
        per_model_messages: parseJsonField('Per-model messages', contextEditor.per_model_messages),
        shared_pairs: parseJsonField('Shared pairs', contextEditor.shared_pairs),
      };

      const response = await axios.put(`${API}/console/context-logs/${selectedContextId}`, payload, authConfig);
      setContextLogs((prev) => prev.map((item) => (item.id === selectedContextId ? response.data : item)));
      toast.success('Context log updated');
    } catch (error) {
      toast.error(error.response?.data?.detail || error.message || 'Failed to save context log');
    } finally {
      setSavingContext(false);
    }
  };

  const copyContextPayload = () => {
    if (!selectedContext) {
      toast.error('No context payload selected');
      return;
    }
    navigator.clipboard.writeText(JSON.stringify(selectedContext, null, 2));
    toast.success('Context payload copied');
  };

  const updateContextEditor = React.useCallback((field, value) => {
    setContextEditor((prev) => ({ ...prev, [field]: value }));
  }, []);

  const usagePct = summary && summary.total_paid_usd > 0
    ? Math.min(100, (summary.estimated_usage_cost_usd / summary.total_paid_usd) * 100)
    : 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6" data-testid="console-page-loading">
        <div className="text-sm text-muted-foreground">Loading console telemetry…</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-16" data-testid="console-page">
      <div className="max-w-6xl mx-auto p-4 md:p-6 space-y-4">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => navigate('/chat')} data-testid="console-back-chat-btn">
            <ArrowLeft className="h-4 w-4 mr-1" />Chat
          </Button>
          <h1 className="text-2xl font-semibold">Operations Console</h1>
          <Button variant="outline" size="sm" onClick={() => navigate('/pricing')} className="ml-auto" data-testid="console-go-pricing-btn">
            <CreditCard className="h-4 w-4 mr-1" />Pricing
          </Button>
          <Button variant="ghost" size="sm" onClick={loadConsoleData} data-testid="console-refresh-btn">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} data-testid="console-tabs">
          <TabsList className="grid grid-cols-4 w-full" data-testid="console-tabs-list">
            <TabsTrigger value="cost" data-testid="console-tab-cost">Token & Cost</TabsTrigger>
            <TabsTrigger value="edcm" data-testid="console-tab-edcm">EDCM Brain</TabsTrigger>
            <TabsTrigger value="context" data-testid="console-tab-context">Prompt Context</TabsTrigger>
            <TabsTrigger value="finance" data-testid="console-tab-finance">Donations vs Costs</TabsTrigger>
          </TabsList>

          <TabsContent value="cost" className="space-y-4" data-testid="console-cost-tab-content">
            <div className="grid md:grid-cols-3 gap-3">
              <Card data-testid="cost-total-paid-card"><CardHeader className="pb-2"><CardTitle className="text-sm">Total Paid</CardTitle></CardHeader><CardContent><div className="text-xl font-semibold">${summary?.total_paid_usd?.toFixed(2) || '0.00'}</div></CardContent></Card>
              <Card data-testid="cost-estimated-usage-card"><CardHeader className="pb-2"><CardTitle className="text-sm">Estimated Usage Cost</CardTitle></CardHeader><CardContent><div className="text-xl font-semibold">${summary?.estimated_usage_cost_usd?.toFixed(4) || '0.0000'}</div></CardContent></Card>
              <Card data-testid="cost-token-card"><CardHeader className="pb-2"><CardTitle className="text-sm">Estimated Tokens</CardTitle></CardHeader><CardContent><div className="text-xl font-semibold">{summary?.total_estimated_tokens?.toLocaleString() || '0'}</div></CardContent></Card>
            </div>

            <Card data-testid="cost-limit-controls-card">
              <CardHeader>
                <CardTitle>Limit Controls</CardTitle>
                <CardDescription>Toggle hard guardrails for token and spend telemetry.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="token-limit-switch">Enforce token limit</Label>
                  <Switch id="token-limit-switch" checked={preferences.enforce_token_limit} onCheckedChange={(value) => setPreferences((prev) => ({ ...prev, enforce_token_limit: value }))} data-testid="token-limit-switch" />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs text-muted-foreground"><span>Token limit</span><span data-testid="token-limit-value">{Number(preferences.token_limit).toLocaleString()}</span></div>
                  <Slider min={1000} max={5000000} step={1000} value={[Number(preferences.token_limit) || 25000]} onValueChange={(values) => setPreferences((prev) => ({ ...prev, token_limit: values[0] }))} data-testid="token-limit-slider" />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="cost-limit-switch">Enforce cost limit</Label>
                  <Switch id="cost-limit-switch" checked={preferences.enforce_cost_limit} onCheckedChange={(value) => setPreferences((prev) => ({ ...prev, enforce_cost_limit: value }))} data-testid="cost-limit-switch" />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs text-muted-foreground"><span>Cost limit (USD)</span><span data-testid="cost-limit-value">${Number(preferences.cost_limit_usd).toFixed(2)}</span></div>
                  <Slider min={1} max={1000} step={1} value={[Number(preferences.cost_limit_usd) || 25]} onValueChange={(values) => setPreferences((prev) => ({ ...prev, cost_limit_usd: values[0] }))} data-testid="cost-limit-slider" />
                </div>

                <div className="h-2 rounded-full bg-muted overflow-hidden" data-testid="cost-usage-progress-track">
                  <div className="h-full bg-primary transition-all" style={{ width: `${usagePct}%` }} data-testid="cost-usage-progress-fill" />
                </div>

                <Button onClick={savePreferences} disabled={savingPrefs} data-testid="save-limit-controls-btn">
                  <Save className="h-4 w-4 mr-1" />{savingPrefs ? 'Saving…' : 'Save controls'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="edcm" className="space-y-4" data-testid="console-edcm-tab-content">
            <Card>
              <CardHeader>
                <CardTitle>EDCM Brain Connections</CardTitle>
                <CardDescription>Live instrument panel for cross-model cognitive drift metrics.</CardDescription>
              </CardHeader>
              <CardContent className="grid md:grid-cols-2 gap-3">
                {[
                  ['Constraint Mismatch Density', dashboard?.edcm_metrics?.[0]?.constraint_mismatch_density],
                  ['Fixation Coefficient', dashboard?.edcm_metrics?.[0]?.fixation_coefficient],
                  ['Escalation Gradient', dashboard?.edcm_metrics?.[0]?.escalation_gradient],
                  ['Context Drift Index', dashboard?.edcm_metrics?.[0]?.context_drift_index],
                  ['Load Saturation Index', dashboard?.edcm_metrics?.[0]?.load_saturation_index],
                ].map(([label, value]) => (
                  <div key={label} className="rounded border border-border p-3" data-testid={`console-edcm-${label.toLowerCase().replace(/\s+/g, '-')}`}>
                    <div className="text-xs text-muted-foreground">{label}</div>
                    <div className="text-lg font-semibold">{value == null ? 'Awaiting a0' : Number(value).toFixed(3)}</div>
                    <div className="mt-2 h-2 rounded-full bg-muted overflow-hidden">
                      <div className="h-full bg-cyan-400" style={{ width: `${Math.max(2, Math.min(100, Number(value || 0) * 100))}%` }} />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="context" className="space-y-4" data-testid="console-context-tab-content">
            <div className="grid lg:grid-cols-[300px_minmax(0,1fr)] gap-3">
              <ConsoleLogViewer
                contextLogs={contextLogs}
                selectedContextId={selectedContextId}
                onSelectContext={setSelectedContextId}
              />

              <ConsoleContextEditor
                contextEditor={contextEditor}
                onChange={updateContextEditor}
                onSave={saveContextLog}
                onCopy={copyContextPayload}
                savingContext={savingContext}
                selectedContextId={selectedContextId}
              />
            </div>
          </TabsContent>

          <TabsContent value="finance" className="space-y-4" data-testid="console-finance-tab-content">
            <div className="grid md:grid-cols-2 gap-3">
              <Card data-testid="finance-oauth-status-card">
                <CardHeader>
                  <CardTitle className="text-sm">OAuth Login</CardTitle>
                  <CardDescription>Identity state for payment + telemetry controls.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" data-testid="finance-oauth-badge">{authInfo?.email ? 'Connected' : 'Unknown'}</Badge>
                    <span className="text-sm" data-testid="finance-oauth-email">{authInfo?.email || 'No account loaded'}</span>
                  </div>
                </CardContent>
              </Card>

              <Card data-testid="finance-donations-vs-costs-card">
                <CardHeader>
                  <CardTitle className="text-sm">Donations vs Costs</CardTitle>
                  <CardDescription>Gross support compared with estimated model+infra burn.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="text-xs text-muted-foreground">Support + Founder inflow</div>
                  <div className="text-lg font-semibold" data-testid="finance-inflow-value">${((summary?.total_support_usd || 0) + (summary?.total_founder_usd || 0)).toFixed(2)}</div>
                  <div className="text-xs text-muted-foreground">Estimated model cost outflow</div>
                  <div className="text-lg font-semibold" data-testid="finance-outflow-value">${(summary?.estimated_usage_cost_usd || 0).toFixed(4)}</div>
                  <div className="text-xs text-muted-foreground">Compute credits sold</div>
                  <div className="text-lg font-semibold" data-testid="finance-credits-sold-value">${(summary?.total_compute_usd || 0).toFixed(2)}</div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
