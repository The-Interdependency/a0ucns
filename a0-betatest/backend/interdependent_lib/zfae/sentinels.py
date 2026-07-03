# ratios: loc_comments=104:62 imports_exports=4:9 calls_definitions=25:13
# === MODULE_BUILD ===
# id: zfae_sentinels_13
#   module_name: sentinels
#   module_kind: engine
#   summary: the 13 canonical sentinels per ZFAE core view — verbatim job descriptions; 6 cliff/structural flag + 7 slope observe by default; halt-and-override authority when in flag mode
#   owner: Erin Spencer
#   public_surface: Sentinel, SENTINELS, SentinelMode, SentinelVerdict, Verdict13, MODE_OBSERVE, MODE_FLAG, MODE_OFF
#   internal_surface: _CLIFF_NAMES, _STRUCTURAL_NAMES, _SLOPE_NAMES
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_sentinels_13_canon_holds
#   rollout: default_enabled
#   rollback: revert file; runtime falls back to 11-sentinel set (architecturally non-coherence-prime — discouraged)
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_sentinels_13_boundaries
#   summary: in-process; reads agent character-sheet mode/weight overrides; no network
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_sentinels_13
#   summary: declares the 13-sentinel canonical set, modes (observe/flag/off), and verdict shape
#   exposes: Sentinel, SENTINELS, SentinelMode, SentinelVerdict, Verdict13
#   boundaries: auth:none, storage:read, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
"""13 canonical sentinels per ZFAE core view.

Names and job descriptions are user-canon, verbatim:

  S1  Provenance         — recorded ‖ asserted
  S2  Parser Integrity   — preserved ‖ imposed
  S3  Constraint / EDCM  — flowing ‖ accumulating
  S4  Safety & Approval  — permitted ‖ forbidden  (cliff)
  S5  Drift              — grounded ‖ plausible    (slope)
  S6  Conflict           — claim against claim (horizontal)
  S7  Compression        — essential ‖ reconstructible
  S8  Budget             — within capacity ‖ beyond it
  S9  Output Policy      — inside ‖ outside (membrane)
  S10 Cost               — spend buying progress ‖ spend buying nothing
  S11 Rate               — rhythm ‖ thrash
  S12 Reversibility      — two-way doors ‖ one-way doors  (cliff)
  S13 Coherence          — becoming more itself ‖ becoming something else (vertical)

13 is a coherence prime; the count is structural.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Literal


class SentinelMode(str, Enum):
    OBSERVE = "observe"   # compute + log; never halts
    FLAG = "flag"         # compute + log + HALT on threshold/cliff
    OFF = "off"           # no compute, no log, vector slot null


MODE_OBSERVE = SentinelMode.OBSERVE
MODE_FLAG = SentinelMode.FLAG
MODE_OFF = SentinelMode.OFF


@dataclass(frozen=True)
class Sentinel:
    """One of the 13 canonical sentinels. Immutable canon."""
    name: str                                       # "S1".."S13"
    title: str                                      # short label
    cut: str                                        # verbatim division statement
    cliff: bool                                     # True for S4, S12 (boolean gates)
    structural: bool                                # True for S1, S2, S8, S9 (structural posts)
    plane: Literal["horizontal", "vertical", "none"] = "none"


SENTINELS: tuple[Sentinel, ...] = (
    Sentinel("S1",  "Provenance",
             "recorded ‖ asserted",
             cliff=False, structural=True),
    Sentinel("S2",  "Parser Integrity",
             "preserved ‖ imposed",
             cliff=False, structural=True),
    Sentinel("S3",  "Constraint / EDCM",
             "flowing ‖ accumulating",
             cliff=False, structural=False),
    Sentinel("S4",  "Safety & Approval",
             "permitted ‖ forbidden",
             cliff=True,  structural=False),
    Sentinel("S5",  "Drift",
             "grounded ‖ plausible",
             cliff=False, structural=False),
    Sentinel("S6",  "Conflict",
             "claim against claim",
             cliff=False, structural=False, plane="horizontal"),
    Sentinel("S7",  "Compression / Recall",
             "essential ‖ reconstructible",
             cliff=False, structural=False),
    Sentinel("S8",  "Budget / Resource",
             "within capacity ‖ beyond it",
             cliff=False, structural=True),
    Sentinel("S9",  "Output Policy",
             "inside ‖ outside",
             cliff=False, structural=True),
    Sentinel("S10", "Cost",
             "spend buying progress ‖ spend buying nothing",
             cliff=False, structural=False),
    Sentinel("S11", "Rate",
             "rhythm ‖ thrash",
             cliff=False, structural=False),
    Sentinel("S12", "Reversibility",
             "two-way doors ‖ one-way doors",
             cliff=True,  structural=False),
    Sentinel("S13", "Coherence",
             "becoming more itself ‖ becoming something else",
             cliff=False, structural=False, plane="vertical"),
)

_NAMES = tuple(s.name for s in SENTINELS)
_CLIFF_NAMES = frozenset(s.name for s in SENTINELS if s.cliff)
_STRUCTURAL_NAMES = frozenset(s.name for s in SENTINELS if s.structural)
_SLOPE_NAMES = frozenset(s.name for s in SENTINELS if not s.cliff and not s.structural)


def all_names() -> tuple[str, ...]:
    return _NAMES


def is_cliff(name: str) -> bool:
    return name in _CLIFF_NAMES


def is_structural(name: str) -> bool:
    return name in _STRUCTURAL_NAMES


def is_slope(name: str) -> bool:
    return name in _SLOPE_NAMES


@dataclass(frozen=True)
class SentinelVerdict:
    """One sentinel's verdict for one event."""
    name: str               # S1..S13
    mode: SentinelMode      # observe | flag | off
    weight: float           # contribution to attention budget
    value: float | None     # the verdict signal in [0, 1]; None if mode=off
    flagged: bool           # True iff this sentinel halts the action
    reason: str             # human-readable; empty when not flagged


@dataclass(frozen=True)
class Verdict13:
    """13-sentinel verdict per event. Signed into the fiq audit chain."""
    verdicts: tuple[SentinelVerdict, ...]   # length 13, ordered by SENTINELS

    @property
    def vector(self) -> tuple[float | None, ...]:
        return tuple(v.value for v in self.verdicts)

    @property
    def flagged_sentinels(self) -> tuple[str, ...]:
        return tuple(v.name for v in self.verdicts if v.flagged)

    @property
    def requires_override(self) -> bool:
        return any(v.flagged for v in self.verdicts)

    @property
    def blocking_cliff(self) -> bool:
        """Any cliff sentinel flagged → action absolutely halts."""
        return any(v.flagged and is_cliff(v.name) for v in self.verdicts)

    @property
    def disabled_sentinels(self) -> tuple[str, ...]:
        return tuple(v.name for v in self.verdicts if v.mode == SentinelMode.OFF)


__all__ = [
    "Sentinel", "SENTINELS",
    "SentinelMode", "MODE_OBSERVE", "MODE_FLAG", "MODE_OFF",
    "SentinelVerdict", "Verdict13",
    "all_names", "is_cliff", "is_structural", "is_slope",
]

# === CONTRACTS ===
# id: zfae_sentinels_13_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===

# ratios: loc_comments=104:62 imports_exports=4:9 calls_definitions=25:13
