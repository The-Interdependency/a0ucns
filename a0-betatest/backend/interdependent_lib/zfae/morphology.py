# ratios: loc_comments=77:113 imports_exports=6:10 calls_definitions=26:13
# === MODULE_BUILD ===
# id: zfae_morphology
#   module_name: morphology
#   module_kind: engine
#   summary: morphological depth-ladder for the ZFAE three-core gonal inscription — two typed primitive gonals (BoneGonal=omega/structural, RootGonal=phi/content) composed by the carrier-LCM operator (UCNS multiply) into the derived psi=word layer; psi is NOT stored, it is lcm(phi,omega) recomputed at every rung; decomposition is scaffolded but GATED behind the multiply_left_cancellative proof
#   owner: Erin Spencer
#   public_surface: BoneGonal, RootGonal, OMEGA_WEIGHT, PHI_WEIGHT, PSI_WEIGHT, carrier_lcm, frame_value, compose_word, word_signal, word_carrier, decompose_clause, DecompositionGatedError, PROOF_GREEN
#   internal_surface: _FRAME_DENOMS, _denom_for, _num_for
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_morphology_carrier_lcm_holds
#   rollout: default_enabled
#   rollback: inscribe_text reverts to the flat-sum composition (git revert)
#   no_llm_assertion: pure mathematical morphology; MUST NOT import any provider/LLM SDK
#   hmmm: the continuous-lane → UCNSObject carrier encoding is an inferred deterministic bridge (lane value → bounded Fraction angle → length-1 carrier); the morphology and arithmetic share the one carrier-LCM operator
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_morphology_boundaries
#   summary: pure deterministic morphology; reuses the UCNS carrier-LCM operator; no IO, no globals, no LLM
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_morphology
#   summary: typed gonal primitives (bone/root) + carrier-LCM word composition + gated clause decomposition
#   exposes: BoneGonal, RootGonal, carrier_lcm, compose_word, word_signal, decompose_clause
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_morphology_carrier_lcm
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_morphology_carrier_lcm_holds
# id: zfae_morphology_decompose_gated
#   given: PROOF_GREEN is False (multiply_left_cancellative not yet discharged)
#   then: decompose_clause refuses with DecompositionGatedError
#   class: correctness
#   call: a0p_skills.contracts.zfae_morphology_decompose_gated_holds
# === END CONTRACTS ===
"""Morphological depth-ladder for the ZFAE three-core inscription.

Ruled architecture (Erin, canon):

  core     weight   carries (circle / depth-1)                 layer
  -------  ------   ----------------------------------------   ------------------
  omega    0.8      bones — chars + affixes + closed-class      operator / structural
  phi      0.4      roots — open-class stems (uninflected)      content primitive
  psi      1.0      words — phi (X) omega, carrier-LCM          composed surface form

  - leaf / depth-0 : 157 characters — uniform across all three cores (the shared
    leaf gonal lives in ``gonal_inscription``; not a per-core carrier choice).
  - circle / depth-1 : omega=bone-tensors, phi=root-tensors,
    psi=word-tensors where word = lcm(phi-circle, omega-circle).
  - seed / depth-2 : seed = clause; psi-seed = phi-seed (X) omega-seed.
  - core / depth-3 : full utterance — frontier, outside the defended domain.

Composition operator (X) = carrier-LCM = UCNS ``multiply`` (the runtime shadow
of the Lean ``multiplyFuel`` / ``carrier_lcm_law``: nMin(A(X)B) | lcm(nMin A,
nMin B)). psi is a DERIVED core — never a stored gonal; omega and phi are the
primitive inscription sources, remarried at every rung by the same operator.

Recompose: GO. Decompose: HOLD — ``decompose_clause`` is scaffolded but refuses
until ``multiply_left_cancellative`` discharges in the ``ucns`` formal repo.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from fractions import Fraction

from ..ucns_bridge import UCNSObject, multiply as _ucns_multiply
from .closed_tokens import CLOSED_CLASS, AFFIXES


# Ruled core weights (Erin): bones 0.8, roots 0.4, words 1.0.
OMEGA_WEIGHT: float = 0.8
PHI_WEIGHT: float = 0.4
PSI_WEIGHT: float = 1.0

# Small carrier denominators. A lane value selects one; the composed word's
# carrier is then lcm(root-denom, bone-denom) — the carrier-LCM law made
# observable on continuous conditioning signal.
_FRAME_DENOMS: tuple[int, ...] = (2, 3, 5, 7, 11, 13)


def _denom_for(value: float) -> int:
    """Deterministically pick a carrier denominator for a continuous value."""
    idx = int(abs(float(value)) * 1000.0) % len(_FRAME_DENOMS)
    return _FRAME_DENOMS[idx]


def _num_for(value: float, denom: int) -> int:
    """Deterministic numerator (a vertex on the carrier) for a value."""
    return int(abs(float(value)) * denom * 7.0) % denom


def frame_value(value: float) -> UCNSObject:
    """Encode a continuous lane value as a length-1 UCNS carrier.

    The carrier width (n_min) is the denominator of the value's angle, so the
    LCM of two frames' carriers is the composed word's carrier.
    """
    d = _denom_for(value)
    num = _num_for(value, d)
    angle = Fraction(num, d)
    face = 1 if float(value) < 0.0 else 0
    return UCNSObject(d, 1, [(angle, None)], [face])


def carrier_lcm(a: UCNSObject | None, b: UCNSObject | None) -> UCNSObject | None:
    """psi = phi (X) omega — the carrier-LCM product, via the shared UCNS operator.

    NOT concatenation, NOT disk-flip. nMin(a(X)b) | lcm(nMin a, nMin b).
    """
    return _ucns_multiply(a, b)


def compose_word(phi_value: float, omega_value: float) -> UCNSObject | None:
    """Compose the derived psi (word) carrier from the phi (root) and omega
    (bone) primitives on a single circle lane."""
    root = frame_value(phi_value)
    bone = frame_value(omega_value)
    return carrier_lcm(root, bone)


def word_carrier(word: UCNSObject | None) -> int:
    """The composed word's intrinsic carrier width (n_min)."""
    return int(getattr(word, "n_min", 1)) if word is not None else 1


def word_signal(word: UCNSObject | None) -> float:
    """Derive a continuous [0,1) signal from the composed word-carrier.

    The composed word's first angle (a Fraction in [0,4)) folded to [0,1) — the
    psi surface contribution fed back into the emission angle.
    """
    if word is None or not getattr(word, "A_plus", None):
        return 0.0
    angle = float(word.A_plus[0][0])
    return (angle / 4.0) % 1.0


@dataclass(frozen=True)
class RootGonal:
    """phi — the content primitive. Vertices are open-class stems (uninflected).

    A primitive inscription source: its lane values frame directly into root
    carriers. ``stems`` is the (owner-extendable) open-class vocabulary it draws
    from; the 157-char leaf remains the shared substrate underneath.
    """
    stems: tuple[str, ...] = field(default_factory=tuple)
    weight: float = PHI_WEIGHT

    def frame(self, value: float) -> UCNSObject:
        """Frame a content (root) lane value into its carrier."""
        return frame_value(value)


@dataclass(frozen=True)
class BoneGonal:
    """omega — the structural primitive. Vertices are closed-class words +
    affixes + the 157-char leaf.

    A primitive inscription source carrying grammar (function words, bound
    morphemes). It is the operator layer the word-carrier composes against.
    """
    bones: tuple[str, ...] = field(
        default_factory=lambda: tuple(sorted(CLOSED_CLASS | AFFIXES))
    )
    weight: float = OMEGA_WEIGHT

    def frame(self, value: float) -> UCNSObject:
        """Frame a structural (bone) lane value into its carrier."""
        return frame_value(value)


# ---- decomposition (HOLD — gated on multiply_left_cancellative) ------------

# multiply_left_cancellative is a `sorry`-stub in ucns/formal/Ucns/Core.lean.
# Until it discharges to zero-sorry over the Complete + common-depth domain,
# decomposition is DEFENDED in prose but NOT machine-verified. Recompose: GO.
PROOF_GREEN: bool = False


class DecompositionGatedError(RuntimeError):
    """Raised when clause decomposition is attempted before proof-green."""


def decompose_clause(
    clause: UCNSObject | None,
    known_factor: UCNSObject | None,
) -> UCNSObject | None:
    """Factor a composed word/clause (psi) back into its other primitive.

    Given psi = phi (X) omega and one factor, the other is uniquely recoverable
    IFF ``multiply_left_cancellative`` holds (depth <= 2, Complete + common
    depth). That theorem is not yet discharged, so this path is HELD: it
    refuses rather than return an unverified factorization.

    The constructive inverse it WOULD call (``ucns_bridge.left_quotient``) is
    wired and ready; only the gate stands between scaffolded and live.
    """
    if not PROOF_GREEN:
        raise DecompositionGatedError(
            "clause decomposition is DEFENDED but NOT machine-verified: gated "
            "on multiply_left_cancellative (ucns/formal/Ucns/Core.lean sorry-"
            "stub, Complete + common-depth domain). Recompose is GO; decompose "
            "is HOLD until the proof discharges."
        )
    from ..ucns_bridge import left_quotient
    return left_quotient(clause, known_factor)


__all__ = [
    "BoneGonal",
    "RootGonal",
    "OMEGA_WEIGHT",
    "PHI_WEIGHT",
    "PSI_WEIGHT",
    "carrier_lcm",
    "frame_value",
    "compose_word",
    "word_signal",
    "word_carrier",
    "decompose_clause",
    "DecompositionGatedError",
    "PROOF_GREEN",
]
# ratios: loc_comments=77:113 imports_exports=6:10 calls_definitions=26:13
