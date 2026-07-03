# ratios: loc_comments=229:108 imports_exports=14:4 calls_definitions=59:15
# === MODULE_BUILD ===
# id: zfae_inference_engine
#   module_name: inference
#   module_kind: engine
#   summary: a0(ZFAE) inference engine — native deterministic symbolic/state engine; no LLM dependency; returns {assistantText, nextSnapshot, trace}
#   owner: a0p maintainer
#   public_surface: A0ZFAEInferenceEngine, InferenceResult, MISSING_NATIVE_MESSAGE
#   internal_surface: _coerce_snapshot, _coerce_rings, _energy_or_none, _make_trace, _memory_count
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_engine_native_only_holds
#   rollout: default_enabled
#   rollback: detach chat route from engine and revert
#   no_llm_assertion: this module MUST NOT import from interdependent_lib.providers or any LLM SDK; CONTRACTS pin the assertion
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_inference_engine_boundaries
#   summary: a0(ZFAE) inference engine — native deterministic symbolic/state engine; no LLM dependency; returns {assistantText, nextSnapshot, trace}
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_inference_engine
#   summary: a0(ZFAE) inference engine — native deterministic symbolic/state engine; no LLM dependency; returns {assistantText, nextSnapshot, trace}
#   exposes: A0ZFAEInferenceEngine, InferenceResult, MISSING_NATIVE_MESSAGE
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_engine_native_only
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_engine_native_only_holds
# === END CONTRACTS ===
# === CONTRACTS ===
# id: zfae_engine_route_a_emits_decode
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_engine_emits_pcea_digest_and_tensors_holds
# === END CONTRACTS ===
"""a0(ZFAE) — native inference engine. Deterministic symbolic/state pipeline.

Pipeline (all pure functions, no external calls):

  raw_prompt
      └─► _parser.parse_semantic   →  SemanticFeatures
              └─► _intent.select_intent      →  IntentLabel
                      └─► _transition.bind_features_to_rings(Φ,Ψ,Ω)
                              └─► _transition.advance_zfae_state (PCEA kernel cross-cut)
                                      └─► _decoder.render          →  assistantText
                                              └─► _transition.snapshot_after → nextSnapshot
                                                      └─► _make_trace → trace

If at any point the decoder is missing or the engine is incomplete,
the engine returns the canonical missing-native message verbatim. It
NEVER substitutes another model's output. This is enforced both
behaviourally and at module-import scope (CONTRACTS pin the no-LLM
import assertion).
"""
from __future__ import annotations
import hashlib
import struct
from dataclasses import dataclass
from typing import Any, TypedDict

from ..pcna.tensor import Tensor
from ._parser import SemanticFeatures, parse_semantic
from ._intent import IntentLabel, select_intent, INTENT_LABELS
from ._decoder import TemplateGrammarDecoder, MISSING_DECODER_MESSAGE
from ._transition import (
    bind_features_to_rings,
    advance_zfae_state,
    snapshot_after,
    ZFAE_RING_NAMES,
)


MISSING_NATIVE_MESSAGE: str = (
    "a0(zfae) cannot perform inference yet: missing native decoder/model/policy."
)


class InferenceResult(TypedDict):
    assistantText: str
    nextSnapshot: dict
    trace: dict


def _energy_or_none(t: Any) -> float | None:
    if isinstance(t, Tensor):
        return float(t.energy())
    if isinstance(t, dict) and isinstance(t.get("payload"), (list, tuple)):
        payload = t["payload"]
        s = 0.0
        for v in payload:
            s += float(v) * float(v)
        return s ** 0.5
    if isinstance(t, (list, tuple)) and t and all(isinstance(v, (int, float)) for v in t):
        s = 0.0
        for v in t:
            s += float(v) * float(v)
        return s ** 0.5
    return None


def _memory_count(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, dict):
        if "entries" in value and isinstance(value["entries"], (list, tuple)):
            return len(value["entries"])
        return len(value)
    if isinstance(value, (list, tuple)):
        return len(value)
    return 0


def _coerce_rings(rings: Any) -> dict[str, Any]:
    """Accept rings as dict or None; return a normalised dict (may be empty)."""
    if isinstance(rings, dict):
        return rings
    return {}


def _coerce_snapshot(snap: Any) -> dict:
    if isinstance(snap, dict):
        return snap
    return {}


def _payload_or_none(t: Any) -> list[float] | None:
    """Return a Tensor's full 53-wide payload as a list — no scalar collapse."""
    if isinstance(t, Tensor):
        return list(t.payload)
    return None


def _pcea_ciphertext_digest(ciphertexts: dict[str, Tensor]) -> str:
    """blake2b over the concatenated PCEA delta payloads (role-sorted).

    This is the state-bound entropy/RNG seed for deterministic Gonal
    Inscription generation — identical PCEA deltas → identical digest.
    """
    h = hashlib.blake2b(digest_size=16)
    for role in sorted(ciphertexts.keys()):
        h.update(role.encode("utf-8"))
        for v in ciphertexts[role].payload:
            h.update(struct.pack("<q", int(round(float(v) * (1 << 28)))))
    return h.hexdigest()


def _long_memory_canon() -> dict:
    """a0 long-term memory — the living-spec canon (cached, deterministic)."""
    from .long_memory import canon_summary
    return canon_summary()


def _intent_hash_short(features: SemanticFeatures, intent: IntentLabel) -> str:
    h = hashlib.blake2b(
        f"{intent}::{','.join(features.tokens)}".encode(), digest_size=4
    )
    return h.hexdigest()


def _lifted_path_meta(text: str) -> dict:
    """Lossless lifted traversal of a Route-A glyph stream over the carrier.

    Text is unchanged; this attaches the ordered lifted path (vertex = pos mod
    157), the count of full-revolution repeats, and the seam (SPACE/ZERO) events,
    plus a decode(encode)==text self-check. Off-carrier glyphs (shouldn't occur
    for Route A) degrade to ok=False rather than raising."""
    from ..gonal.lifted_path import encode_text_path, decode_text_path, ARITY, ORIGIN
    try:
        path = encode_text_path(text)
    except Exception as e:  # off-carrier glyph — never fatal
        return {"enabled": True, "ok": False, "error": str(e)}
    revolutions = sum(1 for i in range(1, len(path)) if path[i] - path[i - 1] == ARITY)
    seam_events = sum(1 for p in path if p % ARITY == ORIGIN)
    return {
        "enabled": True,
        "ok": decode_text_path(path) == text,
        "length": len(path),
        "revolutions": revolutions,
        "seam_events": seam_events,
        "path": path[:64],
    }


@dataclass
class A0ZFAEInferenceEngine:
    """Native a0(ZFAE) inference engine — symbolic/state, no LLM.

    Public method: ``infer(**kwargs) -> InferenceResult``.

    The engine is stateless across calls — all state flows in through
    `zfaeSnapshot` and out through `nextSnapshot`. Callers are
    responsible for persisting the snapshot between turns.
    """

    decoder: TemplateGrammarDecoder = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.decoder is None:
            self.decoder = TemplateGrammarDecoder()

    # ---- public ------------------------------------------------------------
    def infer(
        self,
        *,
        rawPrompt: str = "",
        transcript: list | tuple | None = None,
        memoryL: Any = None,
        memoryS: Any = None,
        zfaeSnapshot: Any = None,
        rings: Any = None,
        phi: Any = None,
        psi: Any = None,
        omega: Any = None,
        edcmbone: Any = None,
        edcm: Any = None,
        gonal_seed: bytes | None = None,
        lifted_path_trace: bool = False,
        **_ignored,
    ) -> InferenceResult:
        """Run one a0(zfae) inference step. Pure, deterministic.

        If the decoder is somehow absent at runtime (mis-configuration,
        partial revert), returns the canonical missing-native message —
        does NOT fall back to any other source.
        """
        if self.decoder is None:
            return InferenceResult(
                assistantText=MISSING_NATIVE_MESSAGE,
                nextSnapshot={},
                trace={"error": "decoder_missing"},
            )

        # 1. Parse → SemanticFeatures
        features = parse_semantic(rawPrompt or "")

        # 2. Select intent
        intent = select_intent(features)

        # 3. Bind features into Φ/Ψ/Ω
        bound = bind_features_to_rings(
            features, intent, phi=phi, psi=psi, omega=omega,
        )

        # 4. Apply PCEA kernel cross-cut against the prior snapshot's Φ/Ψ/Ω
        prior = _coerce_snapshot(zfaeSnapshot)
        last_state: dict[str, Tensor] = {}
        for role in ZFAE_RING_NAMES:
            prev = prior.get(role)
            if isinstance(prev, (list, tuple)) and len(prev) == 53:
                last_state[role] = Tensor(list(prev))
        ciphertexts = advance_zfae_state(bound, last_state=last_state)

        # 4b. PCEA ciphertext digest — state-bound deterministic generation seed.
        pcea_digest = _pcea_ciphertext_digest(ciphertexts)

        # 5. Build the slot state for the decoder
        ring_dict = _coerce_rings(rings)
        ring_energies = {
            name: _energy_or_none(ring_dict.get(name)) for name in
            ("phi", "psi", "omega", "theta", "sigma")
        }
        state = {
            "tick_number": int(prior.get("tick", 0)) + 1,
            "phi_energy": _energy_or_none(bound.get("phi")) or ring_energies.get("phi"),
            "psi_energy": _energy_or_none(bound.get("psi")) or ring_energies.get("psi"),
            "omega_energy": _energy_or_none(bound.get("omega")) or ring_energies.get("omega"),
            "theta_energy": ring_energies.get("theta"),
            "sigma_energy": ring_energies.get("sigma"),
            "coherence_total": (
                (edcm or {}).get("total") if isinstance(edcm, dict) else None
            ),
            "memory_l_count": _memory_count(memoryL),
            "memory_s_count": _memory_count(memoryS),
            "last_intent_hash": prior.get("intent_hash") or "—",
            "intent": intent,
            # ---- continuous tensor conditioning (no scalar collapse) ----------
            "pcea_ciphertext_digest": pcea_digest,
            "phi_v53": _payload_or_none(bound.get("phi")),
            "psi_v53": _payload_or_none(bound.get("psi")),
            "omega_v53": _payload_or_none(bound.get("omega")),
            # ---- a0 long-term memory canon (the agent queries itself) ---------
            "memory_long_canon": _long_memory_canon(),
        }

        # 5b. Seed the per-agent PrivateGonal (Route A — Gonal Inscription).
        if gonal_seed:
            from .gonal_inscription import PrivateGonal
            gonal = PrivateGonal.from_seed(bytes(gonal_seed))
            state["private_gonal"] = gonal.advance(state["tick_number"], pcea_digest)

        # 6. Decode native (Route A if a PrivateGonal is present, else Route B).
        text = self.decoder.decode(intent, features, state)

        # 6b. Optional lossless lifted traversal of the Route-A glyph stream.
        if lifted_path_trace and state.get("private_gonal") is not None:
            state["_lifted_path"] = _lifted_path_meta(text)

        # 7. nextSnapshot
        next_snap = snapshot_after(
            features,
            intent,
            bound,
            ciphertexts,
            prior_snapshot=prior,
            tick_number=state["tick_number"],
            extras={
                "memory_l_count": state["memory_l_count"],
                "memory_s_count": state["memory_s_count"],
                "intent_hash_short": _intent_hash_short(features, intent),
            },
        )

        # 8. Trace
        trace = self._make_trace(features, intent, state, bound, ciphertexts, transcript)

        return InferenceResult(
            assistantText=text,
            nextSnapshot=next_snap,
            trace=trace,
        )

    # ---- internals ---------------------------------------------------------
    def _make_trace(
        self,
        features: SemanticFeatures,
        intent: IntentLabel,
        state: dict,
        bound: dict[str, Tensor],
        ciphertexts: dict[str, Tensor],
        transcript: Any,
    ) -> dict:
        """Build a JSON-friendly trace of what the engine did. Inspectable."""
        return {
            "engine": "a0(zfae)",
            "deterministic": True,
            "uses_llm": False,
            "intent": intent,
            "intent_label_set": list(INTENT_LABELS),
            "features": features.to_dict(),
            "state_slots": {k: v for k, v in state.items() if k != "intent"},
            "ring_payload_heads": {
                role: list(t.payload[:3]) for role, t in bound.items()
            },
            "ciphertext_payload_heads": {
                role: list(t.payload[:3]) for role, t in ciphertexts.items()
            },
            "transcript_turn_count": (
                len(transcript) if isinstance(transcript, (list, tuple)) else 0
            ),
            "decoder": (
                "gonal_inscription_v1" if state.get("private_gonal") is not None
                else "template_grammar_v1"
            ),
            "pcea_ciphertext_digest_prefix": str(state.get("pcea_ciphertext_digest", ""))[:12],
            "memory_long_canon": state.get("memory_long_canon"),
            "zfae_decode": state.get("_route_a_meta"),
            "lifted_path": state.get("_lifted_path"),
        }


# Singleton convenience — callers can `from .inference import ENGINE` instead of
# constructing per call. The engine is stateless across calls, so a shared
# instance is fine.
ENGINE: A0ZFAEInferenceEngine = A0ZFAEInferenceEngine()


def infer(**kwargs) -> InferenceResult:
    """Module-level convenience that delegates to the singleton ENGINE."""
    return ENGINE.infer(**kwargs)


__all__ = [
    "A0ZFAEInferenceEngine",
    "InferenceResult",
    "MISSING_NATIVE_MESSAGE",
    "ENGINE",
    "infer",
]
# ratios: loc_comments=229:108 imports_exports=14:4 calls_definitions=59:15
