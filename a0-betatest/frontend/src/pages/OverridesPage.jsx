// === MODULE_BUILD ===
// id: fe_page_overrides
//   module_name: OverridesPage
//   module_kind: ui_page
//   summary: queue of pending sentinel overrides; approve (with justification) or reject; expired overrides housekeeping; shows flagged sentinels + raw request snippet
//   owner: Erin Spencer
//   public_surface: OverridesPage
//   internal_surface: OverrideRow, useOverrides
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_page_overrides_boundaries
//   summary: page-level approve/reject of pending overrides
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_page_overrides
//   summary: page-level approve/reject of pending overrides
//   exposes: OverridesPage
//   boundaries: auth:none, storage:none, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import { CheckCircle, XCircle, ArrowsClockwise, ShieldWarning, Clock } from "@phosphor-icons/react";

function fmtTs(ms) {
  if (!ms) return "—";
  try { return new Date(Number(ms)).toLocaleString(); } catch { return String(ms); }
}

function OverrideRow({ rec, onApprove, onReject, busy }) {
  const [reason, setReason] = useState("");
  const cliff = !!rec.blocking_cliff;
  return (
    <div className={`border ${cliff ? "border-rose-500/40 bg-rose-500/5" : "border-amber-500/40 bg-amber-500/5"} p-3 space-y-2`}
         data-testid={`override-row-${rec.id}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldWarning size={16} className={cliff ? "text-rose-400" : "text-amber-400"} />
          <span className="font-mono text-xs text-white">
            {rec.event_kind} · {(rec.agent_id || "").slice(0, 12)}…
          </span>
          {cliff && <span className="px-1.5 py-0.5 border border-rose-500 bg-rose-500/20 text-rose-200 text-[0.6rem] font-mono uppercase tracking-wider">cliff</span>}
        </div>
        <span className="flex items-center gap-1 text-[0.6rem] font-mono text-neutral-500">
          <Clock size={11} /> {fmtTs(rec.created_at_ms)}
        </span>
      </div>

      <div className="flex flex-wrap gap-1">
        {(rec.flagged_sentinels || []).map(name => (
          <span key={name} className="px-1.5 py-0.5 border border-amber-400/40 bg-amber-400/10 text-amber-200 text-[0.65rem] font-mono">
            {name}: {rec.reasons?.[name] || "flagged"}
          </span>
        ))}
      </div>

      {rec.raw_request?.prompt && (
        <div className="text-[0.7rem] font-mono text-neutral-400 border border-white/5 bg-bg-surface p-2 truncate">
          ▸ {rec.raw_request.prompt}
        </div>
      )}

      <div className="flex items-center gap-2">
        <input
          data-testid={`override-reason-${rec.id}`}
          value={reason}
          onChange={e => setReason(e.target.value)}
          placeholder="justification / reason"
          className="flex-1 bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
        />
        <button
          data-testid={`override-reject-${rec.id}`}
          disabled={busy}
          onClick={() => onReject(rec.id, reason || "rejected via overrides page")}
          className="px-3 py-1.5 border border-rose-500/40 text-rose-300 font-mono text-xs uppercase tracking-wider hover:bg-rose-500/10 disabled:opacity-40 flex items-center gap-1.5"
        >
          <XCircle size={14} /> reject
        </button>
        <button
          data-testid={`override-approve-${rec.id}`}
          disabled={busy || reason.trim().length < 5}
          onClick={() => onApprove(rec.id, reason)}
          className="px-3 py-1.5 border border-emerald-500/40 text-emerald-300 font-mono text-xs uppercase tracking-wider hover:bg-emerald-500/10 disabled:opacity-40 flex items-center gap-1.5"
        >
          <CheckCircle size={14} /> approve
        </button>
      </div>
    </div>
  );
}

export default function OverridesPage() {
  const [records, setRecords] = useState([]);
  const [showAll, setShowAll] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const load = useCallback(async () => {
    setBusy(true); setErr(null);
    try {
      const r = await api.listOverrides(showAll ? {} : { status: "pending" });
      setRecords(r.overrides || []);
    } catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setBusy(false); }
  }, [showAll]);

  useEffect(() => { load(); }, [load]);

  async function approve(id, reason) {
    setBusy(true);
    try { await api.approveOverride(id, { user_id: "local", justification: reason }); await load(); }
    catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setBusy(false); }
  }

  async function reject(id, reason) {
    setBusy(true);
    try { await api.rejectOverride(id, { user_id: "local", reason }); await load(); }
    catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setBusy(false); }
  }

  async function expire() {
    setBusy(true);
    try { await api.expireOverrides(); await load(); }
    catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setBusy(false); }
  }

  const pending = records.filter(r => r.status === "pending");
  const others = records.filter(r => r.status !== "pending");

  return (
    <div className="space-y-6" data-testid="page-overrides">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-mono tracking-tight text-white">Overrides</h1>
          <p className="text-xs text-neutral-400 mt-1 font-mono">
            Sentinel-halted turns wait here until you explicitly approve (with justification) or reject.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-[0.65rem] font-mono uppercase tracking-ultra text-neutral-400 flex items-center gap-1.5">
            <input data-testid="overrides-showall-toggle" type="checkbox" checked={showAll} onChange={e => setShowAll(e.target.checked)} />
            show all (history)
          </label>
          <button data-testid="overrides-expire-btn" onClick={expire} disabled={busy}
                  className="px-2 py-1.5 border border-white/10 text-neutral-400 font-mono text-[0.65rem] uppercase tracking-wider hover:bg-bg-surface flex items-center gap-1 disabled:opacity-40">
            <Clock size={12} /> expire stale
          </button>
          <button data-testid="overrides-refresh-btn" onClick={load} disabled={busy}
                  className="px-2 py-1.5 border border-white/10 text-neutral-400 font-mono text-[0.65rem] uppercase tracking-wider hover:bg-bg-surface flex items-center gap-1 disabled:opacity-40">
            <ArrowsClockwise size={12} /> refresh
          </button>
        </div>
      </header>

      {err && (
        <div className="border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-rose-300 text-xs font-mono" data-testid="overrides-error">
          {String(err)}
        </div>
      )}

      <section className="space-y-2" data-testid="overrides-pending-section">
        <h2 className="text-xs font-mono uppercase tracking-ultra text-neutral-400">
          pending · {pending.length}
        </h2>
        {pending.length === 0 ? (
          <div className="border border-white/10 px-3 py-4 text-neutral-500 text-xs font-mono" data-testid="overrides-pending-empty">
            No pending overrides.
          </div>
        ) : (
          pending.map(rec => <OverrideRow key={rec.id} rec={rec} busy={busy} onApprove={approve} onReject={reject} />)
        )}
      </section>

      {showAll && others.length > 0 && (
        <section className="space-y-2" data-testid="overrides-history-section">
          <h2 className="text-xs font-mono uppercase tracking-ultra text-neutral-400">history · {others.length}</h2>
          {others.map(rec => (
            <div key={rec.id} className="border border-white/10 bg-bg-surface px-3 py-2 text-xs font-mono flex items-center justify-between" data-testid={`override-history-${rec.id}`}>
              <div className="flex items-center gap-2">
                <span className={rec.status === "approved" ? "text-emerald-300" : rec.status === "rejected" ? "text-rose-300" : "text-neutral-500"}>
                  {rec.status}
                </span>
                <span className="text-neutral-500">{rec.event_kind}</span>
                <span className="text-neutral-600">{(rec.flagged_sentinels || []).join(", ")}</span>
              </div>
              <span className="text-[0.6rem] text-neutral-600">{fmtTs(rec.resolved_at_ms || rec.created_at_ms)}</span>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
