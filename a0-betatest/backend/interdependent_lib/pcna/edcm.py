# ratios: loc_comments=43:50 imports_exports=3:2 calls_definitions=13:6
# === MODULE_BUILD ===
# id: pcna_edcm
#   module_name: edcm
#   module_kind: engine
#   summary: Energy Dissonance Circuit Model — CM/DA/DRIFT/DVG/INT/TBF per-tick scoring (canon directives pending wiring)
#   owner: a0p maintainer
#   public_surface: EDCM, EDCMScores
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: pcna_edcm_boundaries
#   summary: Energy Dissonance Circuit Model — CM/DA/DRIFT/DVG/INT/TBF per-tick scoring (canon directives pending wiring)
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: pcna_edcm
#   summary: Energy Dissonance Circuit Model — CM/DA/DRIFT/DVG/INT/TBF per-tick scoring (canon directives pending wiring)
#   exposes: EDCM, EDCMScores
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""EDCM — Energy Dissonance Circuit Model.

Behavioral-directive scoring: tracks six per-tick metrics:
    CM    — coherence_marker (target alignment)
    DA    — directive_adherence
    DRIFT — drift from declared intent
    DVG   — divergence across rings
    INT   — internal_dissonance
    TBF   — token-budget friction
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from statistics import mean


@dataclass
class EDCMScores:
    cm: float = 0.0
    da: float = 0.0
    drift: float = 0.0
    dvg: float = 0.0
    int_: float = 0.0
    tbf: float = 0.0

    def as_dict(self) -> dict:
        d = asdict(self)
        d["int"] = d.pop("int_")
        return d


class EDCM:
    def __init__(self):
        self.history: list[EDCMScores] = []

    def score(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        ring_signals: dict[str, float],
        intent_match: float = 0.5,
    ) -> EDCMScores:
        ring_vals = list(ring_signals.values()) or [0.0]
        avg = mean(ring_vals)
        diverg = (max(ring_vals) - min(ring_vals)) if len(ring_vals) > 1 else 0.0
        tbf = 0.0
        if prompt_tokens + completion_tokens > 0:
            tbf = round(min(1.0, (prompt_tokens + completion_tokens) / 100_000.0), 4)
        s = EDCMScores(
            cm=round(intent_match, 4),
            da=round(min(1.0, avg + 0.1 * intent_match), 4),
            drift=round(max(0.0, 1.0 - intent_match - 0.1 * avg), 4),
            dvg=round(diverg, 4),
            int_=round(abs(avg - intent_match), 4),
            tbf=tbf,
        )
        self.history.append(s)
        return s

    def latest(self) -> EDCMScores | None:
        return self.history[-1] if self.history else None

# === CONTRACTS ===
# id: pcna_edcm_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=43:50 imports_exports=3:2 calls_definitions=13:6
