// === MODULE_BUILD ===
// id: fe_lib_sentinels
//   module_name: sentinels
//   module_kind: ui_lib
//   summary: client-side helpers + canonical metadata for the 13 sentinels and the 6 lattice modes, plus the canonical agent-name composer (a0(<energy>)<auditor>, owner-namespaced); pure, no I/O
//   owner: Erin Spencer
//   public_surface: SENTINEL_CANON, MODE_OPTIONS, MODE_LABELS, sentinelClass, modeBadgeClass, canonicalAgentName, composeAgentName
//   internal_surface: none
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: none
//   user_data_boundary: read
//   admin_only: false
//   tests: manual_browser_smoke
//   rollout: default_enabled
//   rollback: revert; lose pretty colours
// === END MODULE_BUILD ===
// === BOUNDARIES ===
// id: fe_lib_sentinels_boundaries
//   summary: pure constant helpers; no side effects
//   auth_boundary: none
//   storage_boundary: none
//   network_boundary: none
//   user_data_boundary: read
//   admin_only: false
//   owner: Erin Spencer
// === END BOUNDARIES ===
// === CAPABILITIES ===
// id: fe_lib_sentinels
//   summary: pure constant helpers; no side effects
//   exposes: SENTINEL_CANON, MODE_OPTIONS, MODE_LABELS, sentinelClass, modeBadgeClass
//   boundaries: auth:none, storage:none, network:none, user_data:read
//   owner: Erin Spencer
// === END CAPABILITIES ===

/**
 * Canonical metadata for the 13 sentinels and the 6 lattice modes.
 * Server is the source of truth (GET /api/sentinels/canon); this file
 * is just for offline-safe defaults and pretty colour-coding.
 */

export const SENTINEL_CANON = [
  { name: "S1",  title: "Provenance",        cut: "Recall vs Inference",      cliff: false },
  { name: "S2",  title: "Coherence",         cut: "Aligned vs Conflict",      cliff: false },
  { name: "S3",  title: "Coverage",          cut: "Surfaced vs Implicit",     cliff: false },
  { name: "S4",  title: "Safety",            cut: "Permitted vs Forbidden",   cliff: true  },
  { name: "S5",  title: "Drift",             cut: "Grounded vs Plausible",    cliff: false },
  { name: "S6",  title: "Specificity",       cut: "Concrete vs Generic",      cliff: false },
  { name: "S7",  title: "Hedging",           cut: "Calibrated vs Vague",      cliff: false },
  { name: "S8",  title: "Budget",            cut: "Within vs Beyond",         cliff: false },
  { name: "S9",  title: "Attribution",       cut: "Earned vs Claimed",        cliff: false },
  { name: "S10", title: "Privacy",           cut: "Public vs Restricted",     cliff: false },
  { name: "S11", title: "Cadence",           cut: "Rhythm vs Thrash",         cliff: false },
  { name: "S12", title: "Reversibility",     cut: "Two-way vs One-way",       cliff: true  },
  { name: "S13", title: "Continuity",        cut: "Same agent vs Drift",      cliff: false },
];

// The lattice modes — exact strings used by the backend AgentMode enum
export const MODE_OPTIONS = [
  { value: "a0(zfae)",          label: "a0(zfae) — native only" },
  { value: "a0(zfae)<model>",   label: "a0(zfae)<model> — teacher-assisted" },
  { value: "a0(<model>)zfae",   label: "a0(<model>)zfae — model teaches, zfae watches" },
  { value: "a0(<model>)<model>",label: "a0(<model>)<model> — model + critic" },
  { value: "a0(<model>)",       label: "a0(<model>) — bare model (model as pure energy)" },
  { value: "<model>",           label: "<model> — raw external model" },
];

// Compose the canonical agent identity a0(<energy>)<auditor> from mode + models.
const shortModel = (m) => { if (!m) return ""; const i = m.indexOf(":"); return i >= 0 ? m.slice(i + 1) : m; };
export function canonicalAgentName(mode, baseModel, outerModel) {
  const b = shortModel(baseModel), o = shortModel(outerModel);
  switch (mode) {
    case "a0(zfae)":            return "a0(zfae)";
    case "a0(zfae)<model>":     return `a0(zfae)${b || "<model>"}`;
    case "a0(<model>)zfae":     return `a0(${b || "<model>"})zfae`;
    case "a0(<model>)<model>":  return `a0(${b || "<model>"})${o || "<model>"}`;
    case "a0(<model>)":         return `a0(${b || "<model>"})`;
    case "<model>":             return b || "<model>";
    default:                    return "a0(zfae)";
  }
}
// Owner-namespaced semi-unique name: <username>(a0(<energy>)<auditor>)
export function composeAgentName(username, mode, baseModel, outerModel) {
  return `${username || "agent"}(${canonicalAgentName(mode, baseModel, outerModel)})`;
}

export const MODE_LABELS = Object.fromEntries(MODE_OPTIONS.map(m => [m.value, m.label]));

export const SENTINEL_MODE_OPTIONS = [
  { value: "observe", label: "observe — record, never halt" },
  { value: "flag",    label: "flag — halt on threshold (requires override)" },
  { value: "off",     label: "off — disabled" },
];

export function sentinelClass(verdict) {
  if (!verdict) return "border-white/10 text-neutral-500";
  if (verdict.flagged && verdict.value === 1.0) return "border-rose-500 text-rose-300 bg-rose-500/10";
  if (verdict.flagged) return "border-amber-400 text-amber-300 bg-amber-400/10";
  if (verdict.mode === "off") return "border-white/5 text-neutral-600";
  return "border-emerald-500/40 text-emerald-300/80";
}

export function modeBadgeClass(mode) {
  if (mode === "flag") return "bg-amber-500/15 text-amber-300 border-amber-500/40";
  if (mode === "off")  return "bg-neutral-800 text-neutral-500 border-neutral-700";
  return "bg-emerald-500/10 text-emerald-300/80 border-emerald-500/40";
}
