// === MODULE_BUILD ===
// id: fe_page_workspace
//   module_name: WorkspacePage
//   module_kind: ui_page
//   summary: chat workspace bound to one agent instance; sends prompts through /api/chat/instance/{id}; renders per-turn sentinel verdict ribbon; intercepts HTTP 202 sentinel-halts and opens an OverrideModal that resumes the same prompt with override_id on approval
//   owner: Erin Spencer
//   public_surface: WorkspacePage
//   internal_surface: useQueryAgentId, Turn, AgentBar, ModeBar
//   auth_boundary: none
//   storage_boundary: write
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; chat requires curl
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_page_workspace_boundaries
//   summary: page-level chat workspace bound to one agent instance
//   auth_boundary: none
//   storage_boundary: write
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_workspace
//   summary: page-level chat workspace bound to one agent instance
//   exposes: WorkspacePage
//   boundaries: auth:none, storage:write, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { PaperPlaneTilt, Pulse, ShieldWarning, ArrowsClockwise, Wrench } from "@phosphor-icons/react";
import { api } from "../lib/api";
import MarkdownView from "../components/MarkdownView";
import SentinelVerdictRibbon from "../components/SentinelVerdictRibbon";
import OverrideModal from "../components/OverrideModal";
import AuditTape from "../components/AuditTape";
import { MODE_OPTIONS, canonicalAgentName } from "../lib/sentinels";

function Turn({ t }) {
  const isUser = t.role === "user";
  return (
    <div className={`space-y-2 ${isUser ? "" : "border-l-2 border-accent-cyan/40 pl-3"}`}
         data-testid={`turn-${t.id}-${t.role}`}>
      <div className="flex items-center gap-2 text-[0.6rem] font-mono uppercase tracking-ultra">
        <span className={isUser ? "text-neutral-400" : "text-accent-cyan"}>{isUser ? "user" : "agent"}</span>
        {t.mode && <span className="text-neutral-600">· mode {t.mode}</span>}
        {t.reply_source && <span className={`px-1 border ${t.reply_source === "zfae_halted" ? "border-rose-500/40 text-rose-300" : t.reply_source === "zfae_refused" ? "border-amber-400/40 text-amber-300" : "border-emerald-500/40 text-emerald-300"}`}>
          {t.reply_source}
        </span>}
        {t.teacher_called && <span className="text-neutral-600">teacher ✓</span>}
        {t.zfae_weights_updated && <span className="text-neutral-600">weights Δ</span>}
      </div>
      {isUser
        ? <pre className="font-mono text-sm text-white whitespace-pre-wrap break-words">{t.content}</pre>
        : <MarkdownView text={t.content} />
      }
      {t.tool_trace?.length > 0 && (
        <div className="space-y-1" data-testid={`turn-${t.id}-tools`}>
          <div className="text-[0.55rem] font-mono uppercase tracking-ultra text-violet-300/70">mid-thought tool calls</div>
          {t.tool_trace.map((tr, i) => (
            <div key={i} data-testid={`tool-call-${t.id}-${i}`}
                 className="flex items-center gap-2 text-[0.6rem] font-mono border-l-2 border-violet-400/40 pl-2 py-0.5">
              <Wrench size={11} className="text-violet-300" />
              <span className="text-violet-300">{tr.name}</span>
              <span className="text-neutral-500">({Object.keys(tr.args || {}).join(", ")})</span>
              <span className={
                tr.status === "halted" ? "text-rose-300" :
                tr.status === "error" ? "text-amber-300" : "text-emerald-300/80"
              }>{tr.status}</span>
              {tr.result_preview && (
                <span className="text-neutral-500 truncate" title={String(tr.result_preview)}>
                  · {String(tr.result_preview).slice(0, 90)}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
      {t.sentinel_verdict && <SentinelVerdictRibbon verdict={t.sentinel_verdict} />}
      {t.zfae_metrics && (
        <div className="text-[0.6rem] font-mono text-neutral-600 flex flex-wrap gap-3">
          <span>step {t.zfae_metrics.zfae_training_step ?? 0}</span>
          <span>loss {t.zfae_metrics.zfae_last_loss == null ? "—" : Number(t.zfae_metrics.zfae_last_loss).toFixed(4)}</span>
          {t.zfae_metrics.zfae_checkpoint_digest && <span title={t.zfae_metrics.zfae_checkpoint_digest}>digest {t.zfae_metrics.zfae_checkpoint_digest.slice(0, 10)}…</span>}
        </div>
      )}
    </div>
  );
}

export default function WorkspacePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialAgent = searchParams.get("agent") || "";
  const [agents, setAgents] = useState([]);
  const [agentId, setAgentId] = useState(initialAgent);
  const [agent, setAgent] = useState(null);
  const [mode, setMode] = useState("");
  const [prompt, setPrompt] = useState("");
  const [turns, setTurns] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  // halt / override state
  const [pendingOverride, setPendingOverride] = useState(null); // { id, verdict, prompt, mode }

  const inputRef = useRef(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    api.listInstances().then(r => {
      setAgents(r.agents || []);
      if (!agentId && r.agents?.length) {
        setAgentId(r.agents[0].id);
      }
    }).catch(e => setErr(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!agentId) return setAgent(null);
    api.getInstance(agentId).then(setAgent).catch(e => setErr(e.message));
    setSearchParams(agentId ? { agent: agentId } : {}, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentId]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [turns.length, busy]);

  const transcriptForApi = useMemo(() => turns.map(t => ({ role: t.role, content: t.content })), [turns]);

  const send = useCallback(async (textOverride, modeOverride, overrideId) => {
    const text = (textOverride ?? prompt).trim();
    const m = modeOverride ?? mode ?? agent?.sheet?.mode;
    if (!text || !agentId || busy) return;
    const myId = Date.now();
    setTurns(prev => [...prev, { id: myId, role: "user", content: text, mode: m }]);
    setPrompt("");
    setBusy(true); setErr(null);
    try {
      const { status, data } = await api.chatInstance(agentId, {
        user_id: "local",
        prompt: text,
        mode: m || undefined,
        transcript: transcriptForApi,
        override_id: overrideId || undefined,
      });
      const assistantTurn = {
        id: myId + 1,
        role: "assistant",
        content: data.assistantText || "(empty)",
        mode: data.mode,
        reply_source: data.reply_source,
        teacher_called: data.teacher_called,
        zfae_weights_updated: data.zfae_weights_updated,
        sentinel_verdict: data.sentinel_verdict,
        zfae_metrics: data.zfae_metrics,
        tool_trace: data.trace?.tool_trace,
      };
      setTurns(prev => [...prev, assistantTurn]);
      if (status === 202 && data.pending_override_id) {
        setPendingOverride({
          id: data.pending_override_id,
          verdict: data.sentinel_verdict,
          prompt: text,
          mode: m,
        });
      }
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message);
    } finally {
      setBusy(false);
      // refresh agent metrics
      if (agentId) api.getInstance(agentId).then(setAgent).catch(() => {});
    }
  }, [prompt, mode, agent, agentId, busy, transcriptForApi]);

  const approveAndResume = useCallback(async (reason) => {
    if (!pendingOverride) return;
    setBusy(true); setErr(null);
    try {
      await api.approveOverride(pendingOverride.id, { user_id: "local", justification: reason });
      const { id, prompt: p, mode: m } = pendingOverride;
      setPendingOverride(null);
      // resume by re-sending the same prompt with the override_id
      await send(p, m, id);
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message);
    } finally {
      setBusy(false);
    }
  }, [pendingOverride, send]);

  const rejectOverride = useCallback(async (reason) => {
    if (!pendingOverride) return;
    setBusy(true);
    try {
      await api.rejectOverride(pendingOverride.id, { user_id: "local", reason });
      setPendingOverride(null);
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message);
    } finally { setBusy(false); }
  }, [pendingOverride]);

  const metrics = agent?.zfae_metrics || {};

  return (
    <div className="space-y-4 h-full" data-testid="page-workspace">
      <header className="border border-white/10 bg-bg-panel p-3 flex flex-wrap items-center gap-3" data-testid="ws-agent-bar">
        <div className="flex-1 min-w-[18rem]">
          <label className="block text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-500">agent</label>
          <select data-testid="ws-agent-select" value={agentId} onChange={e => { setAgentId(e.target.value); setTurns([]); }}
                  className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-sm text-white">
            <option value="">— select agent —</option>
            {agents.map(a => <option key={a.id} value={a.id}>{a.sheet?.name || a.id.slice(0, 8)}</option>)}
          </select>
        </div>
        <div className="flex-1 min-w-[18rem]">
          <label className="block text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-500">mode override (per turn)</label>
          <select data-testid="ws-mode-select" value={mode} onChange={e => setMode(e.target.value)}
                  disabled={!agent}
                  className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white disabled:opacity-40 disabled:cursor-not-allowed">
            <option value="">
              {agent
                ? `— use agent default (${canonicalAgentName(agent.sheet?.mode, agent.sheet?.base_model, agent.sheet?.outer_model)}) —`
                : "— select an agent first —"}
            </option>
            {agent && MODE_OPTIONS.map(o => {
              const resolved = canonicalAgentName(o.value, agent?.sheet?.base_model, agent?.sheet?.outer_model);
              const desc = o.label.includes("—") ? o.label.split("—").slice(1).join("—").trim() : "";
              return <option key={o.value} value={o.value}>{desc ? `${resolved} — ${desc}` : resolved}</option>;
            })}
          </select>
        </div>
        {agent && (
          <Link to="/agents" data-testid="ws-edit-agent-link" className="text-[0.65rem] font-mono uppercase tracking-wider text-accent-cyan/80 hover:text-accent-cyan">
            edit sheet →
          </Link>
        )}
      </header>

      {agent && (
        <div className="border border-white/10 bg-bg-surface px-3 py-2 flex flex-wrap items-center gap-4 text-[0.65rem] font-mono text-neutral-400" data-testid="ws-metrics">
          <Pulse size={12} className="text-accent-cyan" />
          <span>scalars <span className="text-white">{(metrics.zfae_weight_count_total ?? metrics.zfae_weight_count ?? 0).toLocaleString()}</span></span>
          <span>step <span className="text-white">{metrics.zfae_training_step ?? 0}</span></span>
          <span>seeds <span className="text-white">{metrics.zfae_total_seeds_touched ?? 0} / 471</span></span>
          <span>last loss <span className="text-white">{metrics.zfae_last_loss == null ? "—" : Number(metrics.zfae_last_loss).toFixed(4)}</span></span>
          <span className="truncate" title={metrics.zfae_checkpoint_digest}>digest <span className="text-white">{metrics.zfae_checkpoint_digest?.slice(0, 12) || "—"}…</span></span>
        </div>
      )}

      {err && (
        <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="ws-error">{String(err)}</div>
      )}

      {agentId && <AuditTape agentId={agentId} />}

      <div ref={scrollRef} className="border border-white/10 bg-bg-panel min-h-[20rem] max-h-[60vh] overflow-y-auto p-4 space-y-4" data-testid="ws-transcript">
        {turns.length === 0 && (
          <div className="text-neutral-500 text-xs font-mono" data-testid="ws-transcript-empty">
            {agentId ? "Send a prompt to begin. Every turn is gated by the 13 sentinels." : "Select or create an agent to start."}
          </div>
        )}
        {turns.map(t => <Turn key={t.id} t={t} />)}
        {busy && <div className="text-[0.7rem] font-mono text-neutral-500 animate-pulse" data-testid="ws-busy">processing turn…</div>}
      </div>

      <form
        data-testid="ws-form"
        onSubmit={e => { e.preventDefault(); send(); }}
        className="flex items-end gap-2"
      >
        <textarea
          ref={inputRef}
          data-testid="ws-prompt-input"
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          onKeyDown={e => { if ((e.metaKey || e.ctrlKey) && e.key === "Enter") { e.preventDefault(); send(); } }}
          rows={3}
          placeholder={agentId ? "Prompt the agent. ⌘/Ctrl+Enter to send." : "Pick an agent above first."}
          disabled={!agentId || busy}
          className="flex-1 bg-bg-surface border border-white/10 px-3 py-2 font-mono text-sm text-white disabled:opacity-40"
        />
        <button type="submit" disabled={!agentId || busy || !prompt.trim()} data-testid="ws-send-btn"
                className="px-4 py-2 border border-accent-cyan/40 text-accent-cyan font-mono text-xs uppercase tracking-wider hover:bg-accent-cyan/10 disabled:opacity-40 flex items-center gap-1.5">
          <PaperPlaneTilt size={14} /> send
        </button>
      </form>

      {pendingOverride && (
        <div className="border border-rose-500/40 bg-rose-500/5 px-3 py-2 flex items-center gap-3 text-xs font-mono text-rose-200" data-testid="ws-halt-banner">
          <ShieldWarning size={14} />
          Sentinel halt — explicit override required to continue.
          <Link to="/overrides" className="ml-auto underline text-rose-100">manage overrides</Link>
          <button onClick={() => setPendingOverride(null)} className="text-rose-400 hover:text-white">dismiss</button>
        </div>
      )}

      <OverrideModal
        overrideId={pendingOverride?.id}
        verdict={pendingOverride?.verdict}
        busy={busy}
        onApprove={approveAndResume}
        onReject={rejectOverride}
        onDismiss={() => setPendingOverride(null)}
      />
    </div>
  );
}
