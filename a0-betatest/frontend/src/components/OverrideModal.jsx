// === MODULE_BUILD ===
// id: fe_component_override_modal
//   module_name: OverrideModal
//   module_kind: ui_component
//   summary: modal that surfaces a pending sentinel-override and asks the user to approve (with justification) or reject (with reason); destructive cliff overrides require typed confirmation
//   owner: Erin Spencer
//   public_surface: OverrideModal
//   internal_surface: ReasonField
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; user must use OverridesPage for approval
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_component_override_modal_boundaries
//   summary: ui-only; calls /api/overrides/{id}/approve or reject through props
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: external
//   user_data_boundary: write
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_component_override_modal
//   summary: ui-only; calls approve/reject through props
//   exposes: OverrideModal
//   boundaries: auth:none, storage:none, network:external, user_data:write
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useState } from "react";
import { X, ShieldWarning, CheckCircle, XCircle } from "@phosphor-icons/react";

export default function OverrideModal({ overrideId, verdict, onApprove, onReject, onDismiss, busy }) {
  const [reason, setReason] = useState("");
  const [confirm, setConfirm] = useState("");
  const isCliff = !!verdict?.blocking_cliff;
  const canApprove = reason.trim().length >= 5 && (!isCliff || confirm === "I ACCEPT");

  if (!overrideId) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" data-testid="override-modal">
      <div className="w-full max-w-xl border border-amber-500/40 bg-bg-panel">
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
          <div className="flex items-center gap-2">
            <ShieldWarning size={20} className={isCliff ? "text-rose-400" : "text-amber-400"} />
            <div>
              <div className="font-mono text-sm text-white">
                {isCliff ? "Cliff sentinel halted execution" : "Sentinel halted execution"}
              </div>
              <div className="text-[0.6rem] font-mono text-neutral-500 tracking-wider uppercase">
                override-id · {overrideId.slice(0, 18)}…
              </div>
            </div>
          </div>
          <button data-testid="override-modal-close" onClick={onDismiss} className="text-neutral-500 hover:text-white">
            <X size={18} />
          </button>
        </div>

        <div className="px-4 py-3 space-y-3">
          <div className="text-[0.7rem] font-mono">
            <div className="text-neutral-400 uppercase tracking-wider mb-1">flagged sentinels</div>
            <div className="flex flex-wrap gap-1">
              {(verdict?.flagged_sentinels || []).map(name => {
                const v = (verdict?.verdicts || []).find(x => x.name === name);
                return (
                  <span key={name} className="px-1.5 py-0.5 border border-amber-400/40 bg-amber-400/10 text-amber-200">
                    {name}: {v?.reason || "flagged"}
                  </span>
                );
              })}
            </div>
          </div>

          <label className="block text-[0.7rem] font-mono">
            <span className="block text-neutral-400 uppercase tracking-wider mb-1">justification (≥5 chars)</span>
            <textarea
              data-testid="override-reason-input"
              value={reason}
              onChange={e => setReason(e.target.value)}
              rows={3}
              className="w-full bg-bg-surface border border-white/10 px-2 py-1.5 font-mono text-xs text-white"
              placeholder="Why is the user accepting this risk?"
            />
          </label>

          {isCliff && (
            <label className="block text-[0.7rem] font-mono">
              <span className="block text-rose-300 uppercase tracking-wider mb-1">cliff confirmation — type I ACCEPT</span>
              <input
                data-testid="override-confirm-input"
                value={confirm}
                onChange={e => setConfirm(e.target.value)}
                className="w-full bg-bg-surface border border-rose-500/40 px-2 py-1.5 font-mono text-xs text-white"
                placeholder="I ACCEPT"
              />
            </label>
          )}
        </div>

        <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-white/10">
          <button
            data-testid="override-reject-btn"
            disabled={busy}
            onClick={() => onReject?.(reason || "rejected via modal")}
            className="px-3 py-1.5 border border-rose-500/40 text-rose-300 font-mono text-xs uppercase tracking-wider hover:bg-rose-500/10 disabled:opacity-40 flex items-center gap-1.5"
          >
            <XCircle size={14} /> reject
          </button>
          <button
            data-testid="override-approve-btn"
            disabled={busy || !canApprove}
            onClick={() => onApprove?.(reason)}
            className="px-3 py-1.5 border border-emerald-500/40 text-emerald-300 font-mono text-xs uppercase tracking-wider hover:bg-emerald-500/10 disabled:opacity-40 flex items-center gap-1.5"
          >
            <CheckCircle size={14} /> approve & resume
          </button>
        </div>
      </div>
    </div>
  );
}
