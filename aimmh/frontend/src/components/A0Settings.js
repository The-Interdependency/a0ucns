import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { toast } from 'sonner';
import { Wifi, WifiOff, Cloud, Smartphone, RefreshCw, Copy, Save, ChevronDown, ChevronUp } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const APP_URL = process.env.REACT_APP_BACKEND_URL;
const SESSION_KEY = 'a0_session_config';
axios.defaults.withCredentials = true;

const ENDPOINTS = [
  { method: 'GET', path: '/api/a0/non-ui/options', desc: 'Discover all non-UI input/output options' },
  { method: 'POST', path: '/api/a0/non-ui/chat/stream', desc: 'Programmatic chat stream with full options (SSE)' },
  { method: 'GET', path: '/api/a0/non-ui/conversations', desc: 'List all conversations for automation' },
  { method: 'GET', path: '/api/a0/non-ui/transcript/{id}', desc: 'Fetch full transcript + metadata' },
  { method: 'POST', path: '/api/edcm/ingest', desc: 'Push EDCM metrics (5 indices)' },
  { method: 'POST', path: '/api/a0/route', desc: 'Send prompts through hub' },
  { method: 'POST', path: '/api/chat/stream', desc: 'Stream multi-model responses (SSE)' },
  { method: 'GET', path: '/api/conversations/{id}/export?format=json', desc: 'Pull transcripts' },
  { method: 'GET', path: '/api/edcm/dashboard', desc: 'Read all dashboard data' },
];

const A0_EXPECTS = [
  { method: 'GET', path: '/health', desc: 'Health check (this app calls a0)' },
  { method: 'POST', path: '/ingest/transcript', desc: 'Receive conversation (auto-ingest)' },
  { method: 'POST', path: '/route', desc: 'Receive routed prompts' },
];

function loadSessionConfig() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

export default function A0Settings() {
  const [config, setConfig] = useState({
    mode: 'local',
    local_name: 'local-device',
    local_url: '',
    local_port: 8787,
    cloud_url: '',
    api_key: '',
    route_via_a0: false,
    auto_ingest: false,
  });
  const [health, setHealth] = useState(null);
  const [checking, setChecking] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showEndpoints, setShowEndpoints] = useState(false);
  const [hasSaved, setHasSaved] = useState(false);

  useEffect(() => {
    // Session config takes priority (manual entry per session)
    const session = loadSessionConfig();
    if (session) {
      setConfig(session);
      return;
    }
    // Fall back to saved server config
    loadSavedConfig();
  }, []);

  // Persist to session on every change
  useEffect(() => {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(config));
  }, [config]);

  const loadSavedConfig = async () => {
    try {
      const res = await axios.get(`${API}/a0/config`);
      const data = res.data;
      if (data.local_url || data.cloud_url) {
        setConfig(data);
        setHasSaved(true);
      }
    } catch {
      // use defaults
    }
  };

  const saveToServer = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/a0/config`, config);
      setHasSaved(true);
      toast.success('Config saved permanently');
    } catch {
      toast.error('Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const checkHealth = async () => {
    setChecking(true);
    try {
      // Push session config to server first so health check uses it
      await axios.put(`${API}/a0/config`, config);
      const res = await axios.get(`${API}/a0/health`);
      setHealth(res.data);
      toast[res.data.status === 'connected' ? 'success' : 'error'](
        `a0: ${res.data.status}`
      );
    } catch {
      setHealth({ status: 'error' });
      toast.error('Health check failed');
    } finally {
      setChecking(false);
    }
  };

  const copyEndpoints = () => {
    const text = `# Multi-AI Hub → a0 Endpoints\nBase URL: ${APP_URL}\nAuth: Bearer <JWT> header\n\n` +
      `## Endpoints a0 can call:\n` +
      ENDPOINTS.map(e => `${e.method} ${APP_URL}${e.path}\n  ${e.desc}`).join('\n') +
      `\n\n## Endpoints a0 must expose:\n` +
      A0_EXPECTS.map(e => `${e.method} ${e.path}\n  ${e.desc}`).join('\n');
    navigator.clipboard.writeText(text);
    toast.success('Endpoint info copied');
  };

  const clearSession = () => {
    sessionStorage.removeItem(SESSION_KEY);
    setConfig({ mode: 'local', local_name: 'local-device', local_url: '', local_port: 8787, cloud_url: '', api_key: '', route_via_a0: false, auto_ingest: false });
    setHealth(null);
    toast('Session config cleared');
  };

  return (
    <Card className="border-border" data-testid="a0-settings-card">
      <CardHeader className="p-4 pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          a0 Integration
          <Badge
            variant={health?.status === 'connected' ? 'default' : 'outline'}
            className="text-[10px] ml-auto"
          >
            {health?.status || 'Not tested'}
          </Badge>
        </CardTitle>
        <CardDescription className="text-xs">
          Manual entry per session &middot; {hasSaved ? 'Saved config loaded' : 'Not saved'} &middot; Non-UI I/O API enabled
        </CardDescription>
      </CardHeader>
      <CardContent className="p-4 space-y-4">
        {/* Connection Mode */}
        <div className="flex gap-2">
          <Button
            variant={config.mode === 'local' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setConfig(p => ({ ...p, mode: 'local' }))}
            className="flex-1"
            data-testid="a0-mode-local"
          >
            <Smartphone className="h-3 w-3 mr-1" /> Local Device
          </Button>
          <Button
            variant={config.mode === 'cloud' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setConfig(p => ({ ...p, mode: 'cloud' }))}
            className="flex-1"
            data-testid="a0-mode-cloud"
          >
            <Cloud className="h-3 w-3 mr-1" /> Google Cloud
          </Button>
        </div>

        {/* Local Device */}
        {config.mode === 'local' && (
          <div className="space-y-3 p-3 rounded-lg bg-muted/30 border border-border">
            <div className="space-y-2">
              <Label className="text-xs font-medium flex items-center gap-1">
                <Smartphone className="h-3 w-3" /> Local device
              </Label>
              <div>
                <Label className="text-[10px] text-muted-foreground">Device name</Label>
                <Input
                  value={config.local_name || ''}
                  onChange={e => setConfig(p => ({ ...p, local_name: e.target.value }))}
                  placeholder="e.g., lab-laptop / galaxy-a16u"
                  className="font-mono text-xs h-8"
                  data-testid="a0-local-name"
                />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div className="col-span-2">
                <Label className="text-[10px] text-muted-foreground">Device IP / URL</Label>
                <Input
                  value={config.local_url}
                  onChange={e => setConfig(p => ({ ...p, local_url: e.target.value }))}
                  placeholder="http://192.168.1.50"
                  className="font-mono text-xs h-8"
                  data-testid="a0-local-url"
                />
              </div>
              <div>
                <Label className="text-[10px] text-muted-foreground">Port</Label>
                <Input
                  type="number"
                  value={config.local_port}
                  onChange={e => setConfig(p => ({ ...p, local_port: parseInt(e.target.value) || 8787 }))}
                  className="font-mono text-xs h-8"
                  data-testid="a0-local-port"
                />
              </div>
            </div>
            <p className="text-[10px] text-muted-foreground">
              Configurable port for spawning subagents
            </p>
          </div>
        )}

        {/* Google Cloud (Stub) */}
        {config.mode === 'cloud' && (
          <div className="space-y-3 p-3 rounded-lg bg-muted/30 border border-border">
            <Label className="text-xs font-medium flex items-center gap-1">
              <Cloud className="h-3 w-3" /> Google Cloud Endpoint
            </Label>
            <Input
              value={config.cloud_url}
              onChange={e => setConfig(p => ({ ...p, cloud_url: e.target.value }))}
              placeholder="https://your-a0-instance.run.app"
              className="font-mono text-xs h-8"
              data-testid="a0-cloud-url"
            />
            <Badge variant="outline" className="text-[9px]">In progress &mdash; creating cloud access</Badge>
          </div>
        )}

        {/* API Key */}
        <div className="space-y-1">
          <Label className="text-xs">a0 API Key (optional)</Label>
          <Input
            type="password"
            value={config.api_key}
            onChange={e => setConfig(p => ({ ...p, api_key: e.target.value }))}
            placeholder="Leave empty if not required"
            className="font-mono text-xs h-8"
            data-testid="a0-api-key"
          />
        </div>

        {/* Toggles */}
        <div className="space-y-2">
          <div className="flex items-center justify-between p-2 rounded bg-muted/30">
            <div>
              <Label className="text-xs">Route via a0</Label>
              <p className="text-[10px] text-muted-foreground">TIW policy gate + unified logging</p>
            </div>
            <Switch
              checked={config.route_via_a0}
              onCheckedChange={v => setConfig(p => ({ ...p, route_via_a0: v }))}
              data-testid="a0-route-toggle"
            />
          </div>
          <div className="flex items-center justify-between p-2 rounded bg-muted/30">
            <div>
              <Label className="text-xs">Auto-Ingest to a0</Label>
              <p className="text-[10px] text-muted-foreground">Export EDCM jsonl after each conversation</p>
            </div>
            <Switch
              checked={config.auto_ingest}
              onCheckedChange={v => setConfig(p => ({ ...p, auto_ingest: v }))}
              data-testid="a0-ingest-toggle"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={checkHealth} disabled={checking} className="flex-1" data-testid="a0-health-btn">
            <RefreshCw className={`h-3 w-3 mr-1 ${checking ? 'animate-spin' : ''}`} />
            Test Connection
          </Button>
          <Button size="sm" onClick={saveToServer} disabled={saving} data-testid="a0-save-btn">
            <Save className="h-3 w-3 mr-1" />
            {saving ? 'Saving...' : 'Save'}
          </Button>
          <Button size="sm" variant="ghost" onClick={clearSession} className="text-xs" data-testid="a0-clear-btn">
            Clear
          </Button>
        </div>

        {/* Health result */}
        {health && (
          <div className="text-[10px] p-2 rounded bg-muted/30 space-y-1">
            <div className="flex items-center gap-1">
              {health.status === 'connected' ?
                <Wifi className="h-3 w-3 text-emerald-400" /> :
                <WifiOff className="h-3 w-3 text-red-400" />
              }
              <span className={health.status === 'connected' ? 'text-emerald-400' : 'text-red-400'}>
                {health.status}
              </span>
            </div>
            {health.a0_url && <div className="text-muted-foreground font-mono">{health.a0_url}</div>}
            {health.error && <div className="text-red-400">{health.error}</div>}
          </div>
        )}

        {/* Endpoint Connection Info */}
        <div className="border border-border rounded-lg overflow-hidden">
          <div
            onClick={() => setShowEndpoints(!showEndpoints)}
            className="w-full flex items-center justify-between p-3 text-xs font-medium hover:bg-muted/30 transition-colors cursor-pointer"
            data-testid="a0-endpoints-toggle"
            role="button"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setShowEndpoints(!showEndpoints); }}
          >
            <span>Endpoint Connection Info</span>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="ghost"
                className="h-6 px-2 text-[10px]"
                onClick={e => { e.stopPropagation(); copyEndpoints(); }}
                data-testid="a0-copy-endpoints"
              >
                <Copy className="h-3 w-3 mr-1" /> Copy
              </Button>
              {showEndpoints ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </div>
          </div>

          {showEndpoints && (
            <div className="p-3 pt-0 space-y-3">
              {/* Endpoints a0 can call on this app */}
              <div>
                <Label className="text-[10px] text-muted-foreground mb-1 block">
                  a0 calls this app at: <span className="font-mono text-foreground">{APP_URL}</span>
                </Label>
                <div className="space-y-1">
                  {ENDPOINTS.map(e => (
                    <div key={e.path} className="flex items-start gap-2 text-[10px] font-mono p-1.5 rounded bg-muted/20">
                      <Badge variant="outline" className="text-[8px] shrink-0 mt-0.5 w-10 justify-center">
                        {e.method}
                      </Badge>
                      <div>
                        <div className="text-foreground">{e.path}</div>
                        <div className="text-muted-foreground font-sans">{e.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Endpoints a0 must expose */}
              <div>
                <Label className="text-[10px] text-muted-foreground mb-1 block">
                  a0 must expose (this app calls a0):
                </Label>
                <div className="space-y-1">
                  {A0_EXPECTS.map(e => (
                    <div key={e.path} className="flex items-start gap-2 text-[10px] font-mono p-1.5 rounded bg-muted/20">
                      <Badge variant="outline" className="text-[8px] shrink-0 mt-0.5 w-10 justify-center">
                        {e.method}
                      </Badge>
                      <div>
                        <div className="text-foreground">{e.path}</div>
                        <div className="text-muted-foreground font-sans">{e.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="text-[10px] text-muted-foreground p-2 rounded bg-muted/20">
                Auth: <span className="font-mono">Authorization: Bearer &lt;JWT&gt;</span> header on all calls.
                a0-to-app also accepts <span className="font-mono">X-a0-Key</span> if set above.
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
