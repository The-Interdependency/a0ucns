// === MODULE_BUILD ===
// id: fe_component_sentinel_ribbon
//   module_name: SentinelVerdictRibbon
//   module_kind: ui_component
//   summary: render the 13-sentinel verdict as a horizontal pill ribbon; hover shows full verdict row; click toggles details panel
//   owner: Erin Spencer
//   public_surface: SentinelVerdictRibbon
//   internal_surface: Pill
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: none
//   user_data_boundary: read
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; replace with text dump
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_component_sentinel_ribbon_boundaries
//   summary: presentational component over a sentinel Verdict13 dict
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: none
//   user_data_boundary: read
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_component_sentinel_ribbon
//   summary: presentational component over a sentinel Verdict13 dict
//   exposes: SentinelVerdictRibbon
//   boundaries: auth:none, storage:none, network:none, user_data:read
//   owner: Erin Spencer
// === END CAPABILITIES ===

import React, { useState } from "react";
import { SENTINEL_CANON, sentinelClass } from "../lib/sentinels";

function Pill({ s, verdict, onClick }) {
  return (
    <button
      data-testid={`sentinel-pill-${s.name}`}
      onClick={onClick}
      title={`${s.name} · ${s.title} (${s.cut})${verdict ? ` — ${verdict.mode}${verdict.value != null ? ` v=${verdict.value.toFixed(2)}` : ""}` : ""}`}
      className={`px-1.5 py-0.5 border text-[0.6rem] font-mono tracking-wider uppercase ${sentinelClass(verdict)}`}
    >
      {s.name}
    </button>
  );
}

export default function SentinelVerdictRibbon({ verdict }) {
  const [open, setOpen] = useState(false);
  const byName = Object.fromEntries((verdict?.verdicts || []).map(v => [v.name, v]));
  return (
    <div className="space-y-2" data-testid="sentinel-verdict-ribbon">
      <div className="flex items-center gap-1 flex-wrap">
        <span className="text-[0.6rem] font-mono uppercase tracking-ultra text-neutral-500 mr-2">sentinels</span>
        {SENTINEL_CANON.map(s => (
          <Pill key={s.name} s={s} verdict={byName[s.name]} onClick={() => setOpen(o => !o)} />
        ))}
        {verdict?.blocking_cliff && (
          <span className="ml-2 px-1.5 py-0.5 border border-rose-500 bg-rose-500/20 text-rose-200 text-[0.6rem] font-mono uppercase tracking-wider" data-testid="cliff-banner">cliff</span>
        )}
        {verdict?.flagged_sentinels?.length > 0 && (
          <span className="ml-2 text-[0.6rem] font-mono text-amber-300" data-testid="flagged-count">
            {verdict.flagged_sentinels.length} flagged
          </span>
        )}
      </div>
      {open && verdict?.verdicts && (
        <div className="border border-white/10 bg-bg-surface p-2 text-[0.7rem] font-mono space-y-1" data-testid="sentinel-detail-table">
          {verdict.verdicts.map(v => (
            <div key={v.name} className="grid grid-cols-[3rem_5rem_5rem_4rem_1fr] gap-2">
              <span className={v.flagged ? "text-amber-300" : "text-neutral-400"}>{v.name}</span>
              <span className="text-neutral-500">{v.mode}</span>
              <span className="text-neutral-500">w={v.weight?.toFixed?.(2) ?? "—"}</span>
              <span className={v.flagged ? "text-amber-300" : "text-neutral-500"}>
                {v.value == null ? "—" : v.value.toFixed(2)}
              </span>
              <span className="text-neutral-400 truncate">{v.reason || ""}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
