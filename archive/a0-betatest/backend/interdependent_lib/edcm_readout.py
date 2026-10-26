# ratios: loc_comments=77:70 imports_exports=5:3 calls_definitions=33:11
# === MODULE_BUILD ===
# id: il_edcm_readout
#   module_name: edcm_readout
#   module_kind: adapter
#   summary: self-contained EDCM readout for the training view — computes the six-family projection metrics (CM constraint-mismatch, DA dissonance-accumulation, DRIFT, DVG divergence, INT intensity, TBF turn-balance-fairness) deterministically from a transcript turn / turn-pair using measurable text features (operator/bone overlap, negation density, TTR delta, length balance), each bounded to [0,1] with 0.80/0.20 alert bands. Reports raised_field_count (bone operators present) and honors the EDCM empty-field intuition. This is a lightweight readout inspired by the edcmbone metrics/projection + pcna core/edcm families — NOT the full edcmbone stats engine, and it transfers no theorem/proof status.
#   owner: Erin Spencer
#   public_surface: EDCMReadout, readout, EDCM_METRICS, ALERT_HIGH, ALERT_LOW
#   internal_surface: _tokens, _jaccard, _bone_set, _neg_density, _ttr, _intensity, _band
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.edcm_readout_bounds_holds
#   rollout: default_enabled
#   rollback: revert; the training view loses its EDCM readout panel
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: il_edcm_readout_boundaries
#   summary: pure transcript -> six-family EDCM projection metrics; no io, no network
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: il_edcm_readout
#   summary: six-family EDCM projection readout over a transcript turn / turn-pair
#   exposes: EDCMReadout, readout, EDCM_METRICS, ALERT_HIGH, ALERT_LOW
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: edcm_readout_bounds
#   given: a readout over a turn-pair, a first turn (no prior), and empty text
#   then: all six metrics are in [0,1], deterministic, alert bands agree with the
#         thresholds, TBF handles the no-prior case, and raised_field_count counts
#         the bone operators present
#   class: correctness
#   call: a0p_skills.contracts.edcm_readout_bounds_holds
# === END CONTRACTS ===
"""Self-contained EDCM readout for the chat-training view.

The six EDCM projection families (CM, DA, DRIFT, DVG, INT, TBF) are the same
directive metrics a0's engines score turns with (0.80/0.20 alert bands). This
adapter computes them deterministically from measurable text features so the
training tab can show an EDCM panel beside the ZFAE ring energies, WITHOUT
pulling in the full edcmbone stats engine. It is a lightweight readout, not a
metric authority: no edcmbone/UCNS-A theorem or proof status transfers through
it. The construction-object layer's ``NA != 0`` invariant belongs to
edcm.ucns_objects (ConstraintField/FieldMotion) and is intentionally out of scope
here — these are the [0,1] projection scores, with an explicit raised_field_count
for the empty-field intuition.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

from .zfae.morphology import BoneGonal


EDCM_METRICS = ("cm", "da", "drift", "dvg", "int", "tbf")
ALERT_HIGH = 0.80
ALERT_LOW = 0.20
_TOKEN_RE = re.compile(r"[a-z0-9']+")
_BONES = frozenset(BoneGonal().bones)
# Negation / dissonance bones (a subset of the closed class).
_NEG = frozenset({"not", "no", "never", "none", "cannot", "cant",
                  "without", "neither", "nor", "n't", "dont", "wont"})


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


def _bone_set(text: str) -> set[str]:
    return {t for t in _tokens(text) if t in _BONES}


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def _is_negation(tok: str) -> bool:
    # `_TOKEN_RE` keeps the apostrophe, so contractions arrive as "don't"/"won't"/
    # "isn't"/… — a single "n't" suffix check catches every such form; the set
    # holds the apostrophe-free + standalone spellings (no, not, cannot, ...).
    return tok in _NEG or tok.endswith("n't")


def _neg_density(text: str) -> float:
    toks = _tokens(text)
    if not toks:
        return 0.0
    return min(1.0, sum(1 for t in toks if _is_negation(t)) / len(toks) * 4.0)


def _ttr(text: str) -> float:
    toks = _tokens(text)
    return len(set(toks)) / len(toks) if toks else 0.0


def _intensity(text: str) -> float:
    raw = text or ""
    n = max(1, len(raw))
    length = min(1.0, len(_tokens(raw)) / 60.0)
    caps = sum(1 for c in raw if c.isupper()) / n
    excl = raw.count("!") + raw.count("?")
    return min(1.0, 0.5 * length + 0.3 * min(1.0, caps * 5.0) + 0.2 * min(1.0, excl / 5.0))


def _band(v: float) -> str:
    return "high" if v >= ALERT_HIGH else "low" if v <= ALERT_LOW else "nominal"


@dataclass(frozen=True)
class EDCMReadout:
    """Six-family EDCM projection over a turn (or turn-pair), each score in [0,1]."""
    grain: str
    metrics: dict          # name -> float in [0,1]
    alerts: dict           # name -> "high" | "low" | "nominal"
    raised_field_count: int

    def as_dict(self) -> dict:
        return {"grain": self.grain, "metrics": dict(self.metrics),
                "alerts": dict(self.alerts), "raised_field_count": self.raised_field_count}


def readout(cur_text: str, prev_text: Optional[str] = None, grain: str = "turn") -> EDCMReadout:
    """Compute the six EDCM projection metrics for ``cur_text`` (vs ``prev_text``).

    All measurable + deterministic:
      CM    = structural-operator mismatch (1 - bone Jaccard vs prior, or bone
              sparsity on a first turn)
      DA    = negation / dissonance density in the current turn
      DRIFT = 1 - lexical overlap vs prior (topic drift)
      DVG   = |TTR(cur) - TTR(prior)| (vocabulary-spread divergence)
      INT   = intensity (length + caps + punctuation)
      TBF   = turn-balance fairness (length balance; 0.5 when no prior)
    """
    cur_tokens = set(_tokens(cur_text))
    cur_bones = _bone_set(cur_text)
    raised = len(cur_bones)
    if prev_text is not None:
        prev_tokens = set(_tokens(prev_text))
        prev_bones = _bone_set(prev_text)
        cm = 1.0 - _jaccard(cur_bones, prev_bones)
        drift = 1.0 - _jaccard(cur_tokens, prev_tokens)
        dvg = abs(_ttr(cur_text) - _ttr(prev_text))
        lc, lp = len(_tokens(cur_text)), len(_tokens(prev_text))
        tbf = 1.0 - abs(lc - lp) / (lc + lp) if (lc + lp) else 0.5
    else:
        cm = 1.0 - (raised / len(cur_tokens)) if cur_tokens else 0.0
        drift = 0.0
        dvg = _ttr(cur_text)
        tbf = 0.5
    metrics = {
        "cm": round(min(1.0, max(0.0, cm)), 6),
        "da": round(_neg_density(cur_text), 6),
        "drift": round(min(1.0, max(0.0, drift)), 6),
        "dvg": round(min(1.0, max(0.0, dvg)), 6),
        "int": round(_intensity(cur_text), 6),
        "tbf": round(min(1.0, max(0.0, tbf)), 6),
    }
    alerts = {k: _band(v) for k, v in metrics.items()}
    return EDCMReadout(grain=grain, metrics=metrics, alerts=alerts, raised_field_count=raised)


__all__ = ["EDCMReadout", "readout", "EDCM_METRICS", "ALERT_HIGH", "ALERT_LOW"]
# ratios: loc_comments=77:70 imports_exports=5:3 calls_definitions=33:11
