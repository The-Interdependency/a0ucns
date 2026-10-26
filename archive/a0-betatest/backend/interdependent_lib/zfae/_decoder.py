# ratios: loc_comments=195:72 imports_exports=7:4 calls_definitions=43:13
# === MODULE_BUILD ===
# id: zfae_template_decoder
#   module_name: _decoder
#   module_kind: engine
#   summary: native energy-conditioned decoder — composes assistantText as a deterministic function of (intent, features, Φ/Ψ/Ω/θ/σ energy state); RNG seeded from blake2b(state) so identical state → identical text; render() retained as named single-sentence fallback; no LLM dependency
#   owner: Erin Spencer
#   public_surface: TemplateGrammarDecoder, decode, render, MISSING_DECODER_MESSAGE
#   internal_surface: _TEMPLATES, _format_keywords, _format_energy
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_decoder_native_only_holds
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_template_decoder_boundaries
#   summary: native template/grammar decoder — emits assistantText from (intent, features, state) using a small fixed grammar; no LLM dependency
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_template_decoder
#   summary: native template/grammar decoder — emits assistantText from (intent, features, state) using a small fixed grammar; no LLM dependency
#   exposes: TemplateGrammarDecoder, render, MISSING_DECODER_MESSAGE
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_decoder_native_only
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_decoder_native_only_holds
# === END CONTRACTS ===
"""Native template / grammar decoder for a0(zfae).

Route B energy-conditioned compositor — emits text as a function of the
Φ/Ψ/Ω/θ/σ energy state, not a fixed string per intent.

Determinism contract (preserved): the RNG used to select & order fragments
is seeded from a blake2b digest of the state itself, so identical state →
identical text. No I/O, no globals, no LLM.

`render(intent, features, state)` is kept as the named fallback voice.
`decode()` composes; if composition cannot find any fragment for `intent`
it returns `render(...)` so a single template-style sentence still ships.
"""
from __future__ import annotations
import hashlib
import json
import random
from ._intent import IntentLabel
from ._parser import SemanticFeatures


MISSING_DECODER_MESSAGE: str = (
    "a0(zfae) cannot perform inference yet: missing native decoder/model/policy."
)


# Energy-conditioned fragment pool — each intent has multiple lexical
# units; the energy state selects/orders them. ALL units are local; the
# words never come from an external model.
_FRAGMENTS: dict[IntentLabel, dict[str, list[str]]] = {
    "acknowledge": {
        "open":  ["acknowledged.", "received.", "online.", "the channel holds."],
        "energy":["Φ-energy reads {phi_e}, Ψ {psi_e}, Ω {omega_e}.",
                  "coherence {coherence} on the σ-baseline.",
                  "the gate Θ measures {theta_e}; observer Σ at {sigma_e}."],
        "close": ["ready.", "ready to receive intent.", "awaiting next tick."],
    },
    "describe_state": {
        "open":  ["state at tick {tick}:", "tick {tick} —", "snapshot tick {tick}."],
        "energy":["Φ {phi_e} · Ψ {psi_e} · Ω {omega_e}.",
                  "Θ gate {theta_e}, Σ observer {sigma_e}.",
                  "memory-L holds {ml_count}, memory-S {ms_count}.",
                  "coherence total {coherence}."],
        "close": ["state stable.", "no drift detected.", "carrying forward."],
    },
    "answer_question": {
        "open":  ["the prompt parses as a {qword_phrase} question with load {load}.",
                  "reading {qword_phrase}, semantic load {load}."],
        "energy":["keywords routed to Φ at {phi_e}: {keywords}.",
                  "modulated Ψ at {psi_e}, Ω carrying {omega_e}.",
                  "Σ observer reports {sigma_e}; gate Θ {theta_e}."],
        "close": ["this is a deterministic state summary, not a generative answer.",
                  "for discursive prose, ask a BYOK comparison."],
    },
    "reflect_memory": {
        "open":  ["reflection requested.", "looking back —"],
        "energy":["memory-L holds {ml_count}, memory-S {ms_count}.",
                  "last intent fingerprint {last_intent_hash}.",
                  "coherence at {coherence}; Σ {sigma_e}."],
        "close": ["full reflection lives in the trace field.",
                  "see trace for the chain."],
    },
    "echo_with_analysis": {
        "open":  ["parsed: {token_count} tokens, {keyword_count} keywords ({keywords}).",
                  "input: {token_count} tokens, {keyword_count} keywords."],
        "energy":["bound to Φ at {phi_e}.",
                  "Ψ now at {psi_e}, Ω at {omega_e}.",
                  "coherence advanced to {coherence}."],
        "close": ["state advanced.", "tick recorded."],
    },
    "ask_clarification": {
        "open":  ["semantic load is low ({load}) and no clear keywords surface.",
                  "this prompt does not carry enough signal ({load})."],
        "energy":["Φ remains at {phi_e}; nothing routes."],
        "close": ["could you specify the subject or add more tokens?",
                  "a0(zfae) is keyword-bound at this stage."],
    },
    "negation_received": {
        "open":  ["negation detected (tokens: {negation_tokens}).",
                  "the prompt carries a negation: {negation_tokens}."],
        "energy":["recording in memory-S as a directive boundary.",
                  "no outward action taken; Σ {sigma_e}."],
        "close": ["state preserved.", "the no is heard."],
    },
    "low_signal": {
        "open":  ["empty prompt.", "no tokens received."],
        "energy":["Φ at {phi_e}; nothing to bind."],
        "close": ["send a token sequence to update Φ/Ψ/Ω."],
    },
}


def _format_keywords(kws: tuple[str, ...]) -> str:
    return ", ".join(kws[:6]) if kws else "(none)"


def _is_v53(v) -> bool:
    """True iff v is a 53-wide numeric payload (the continuous conditioning signal)."""
    return (
        isinstance(v, (list, tuple)) and len(v) == 53
        and all(isinstance(x, (int, float)) for x in v)
    )


def _format_energy(value: float | None, default: str = "—") -> str:
    return default if value is None else f"{float(value):+.4f}"


def _slots(features: SemanticFeatures, state: dict) -> dict:
    return {
        "coherence": _format_energy(state.get("coherence_total")),
        "tick":      state.get("tick_number", 0),
        "phi_e":     _format_energy(state.get("phi_energy")),
        "psi_e":     _format_energy(state.get("psi_energy")),
        "omega_e":   _format_energy(state.get("omega_energy")),
        "theta_e":   _format_energy(state.get("theta_energy")),
        "sigma_e":   _format_energy(state.get("sigma_energy")),
        "ml_count":  state.get("memory_l_count", 0),
        "ms_count":  state.get("memory_s_count", 0),
        "last_intent_hash": state.get("last_intent_hash", "—"),
        "token_count":  features.token_count,
        "keyword_count": len(features.keywords),
        "keywords":     _format_keywords(features.keywords),
        "qword_phrase": " ".join(features.question_words) or "non-WH",
        "load":         f"{features.semantic_load:.3f}",
        "negation_tokens": ", ".join(
            t for t in features.tokens if t in
            {"no","not","never","none","neither","nor","without"}
        ) or "(implicit)",
    }


def _state_seed(state: dict) -> int:
    """Deterministic per-tick seed.

    Prefer the PCEA ciphertext digest if the engine exposed it on `state`;
    otherwise fall back to a blake2b of the full state dict. Either path is
    state-bound — identical state always returns the same seed."""
    digest_source = state.get("pcea_ciphertext_digest") or json.dumps(
        state, sort_keys=True, default=str,
    )
    if isinstance(digest_source, str):
        digest_source = digest_source.encode("utf-8")
    return int.from_bytes(
        hashlib.blake2b(digest_source, digest_size=8).digest(), "big",
    )


def _bucket(value: float | None) -> int:
    """Map an energy value (≈ [-1, 1]) to a 0..3 bucket — state-driven selection."""
    if value is None:
        return 0
    v = float(value)
    if v < -0.25: return 0
    if v < 0.0:   return 1
    if v < 0.25:  return 2
    return 3


def _pick(rng: random.Random, choices: list[str]) -> str:
    return choices[rng.randrange(len(choices))] if choices else ""


def decode(
    intent: IntentLabel,
    features: SemanticFeatures,
    state: dict,
) -> str:
    """Energy-conditioned native decode.

    The Φ/Ψ/Ω/θ/σ energies + intent + features jointly determine which
    fragments are selected AND their ordering. Sampling is seeded from
    ``state`` itself, so the output is a deterministic function of state.
    Falls back to `render(...)` for unknown intents.
    """
    pool = _FRAGMENTS.get(intent)
    if not pool:
        return render(intent, features, state)

    # ---- Route A — Gonal Inscription (continuous tensor field → glyphs) -----
    gonal = state.get("private_gonal")
    phi = state.get("phi_v53")
    psi = state.get("psi_v53")
    omega = state.get("omega_v53")
    if gonal is not None and _is_v53(phi) and _is_v53(psi) and _is_v53(omega):
        from .gonal_inscription import inscribe_text
        digest = state.get("pcea_ciphertext_digest") or format(_state_seed(state), "016x")
        mlc = state.get("memory_long_canon")
        canon = str(mlc.get("canon_digest", "")) if isinstance(mlc, dict) else ""
        text, meta = inscribe_text(gonal, phi, psi, omega, digest, canon_digest=canon)
        state["_route_a_meta"] = {"intent": intent, "route": "A", **meta}
        return text

    # ---- Route B — energy-conditioned template compositor (fallback) --------
    rng = random.Random(_state_seed(state))
    slots = _slots(features, state)

    # Bucket-driven fragment count: more open energy → richer composition.
    phi_b = _bucket(state.get("phi_energy"))
    omega_b = _bucket(state.get("omega_energy"))
    n_energy = max(1, min(len(pool.get("energy", [])), 1 + (phi_b + omega_b) // 2))

    opener  = _pick(rng, pool.get("open", []) or [""])
    energies = pool.get("energy", [])
    chosen: list[str] = []
    pool_copy = list(energies)
    while pool_copy and len(chosen) < n_energy:
        chosen.append(pool_copy.pop(rng.randrange(len(pool_copy))))
    closer  = _pick(rng, pool.get("close", []) or [""])

    parts = [opener, *chosen, closer]
    try:
        text = " ".join(p.format(**slots) for p in parts if p)
    except (KeyError, IndexError):
        return render(intent, features, state)
    return text.strip()


def render(
    intent: IntentLabel,
    features: SemanticFeatures,
    state: dict,
) -> str:
    """Pure render fallback — single-sentence-per-intent voice. Preserved
    deliberately as the named native fallback when composition declines."""
    _LEGACY_TEMPLATES = {
        "acknowledge": "Acknowledged. a0(zfae) is online. Σ-baseline holds; coherence={coherence}.",
        "describe_state": "State at tick {tick}: Φ {phi_e}, Ψ {psi_e}, Ω {omega_e}.",
        "answer_question": "a0(zfae) parses this as a {qword_phrase} question with load {load}.",
        "reflect_memory": "Reflection request received. Memory-L holds {ml_count} entries.",
        "echo_with_analysis": "Parsed: {token_count} tokens, {keyword_count} keywords ({keywords}).",
        "ask_clarification": "Prompt has low semantic load ({load}) and no clear keywords.",
        "negation_received": "Negation detected (tokens: {negation_tokens}).",
        "low_signal": "Empty prompt. a0(zfae) cannot bind features without input.",
    }
    if intent not in _LEGACY_TEMPLATES:
        return MISSING_DECODER_MESSAGE
    return _LEGACY_TEMPLATES[intent].format(**_slots(features, state))


class TemplateGrammarDecoder:
    """OO façade over `decode` — kept tiny for clarity and easy testing."""

    def __init__(self) -> None:
        pass

    def decode(
        self,
        intent: IntentLabel,
        features: SemanticFeatures,
        state: dict,
    ) -> str:
        return decode(intent, features, state)

    @property
    def known_intents(self) -> tuple[str, ...]:
        return tuple(_FRAGMENTS.keys())


__all__ = [
    "TemplateGrammarDecoder",
    "decode",
    "render",
    "MISSING_DECODER_MESSAGE",
]
# ratios: loc_comments=195:72 imports_exports=7:4 calls_definitions=43:13
