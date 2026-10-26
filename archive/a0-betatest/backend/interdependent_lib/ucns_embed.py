# ratios: loc_comments=92:81 imports_exports=8:4 calls_definitions=35:8
# === MODULE_BUILD ===
# id: il_ucns_embed
#   module_name: ucns_embed
#   module_kind: adapter
#   summary: build a UCNS-native embedding of text as unit-circle phase streams on the 157-gonal carrier — one angle per lane derived from the ZFAE three-core gonal weights (omega 0.8 structural / phi 0.4 content / psi 1.0 = phi carrier-LCM omega via ucns_bridge.multiply), plus a chirality/face bit per lane, keyed by a canonical blake2b hash. This is the a0p-native "embedding" surface (phase streams over a prime carrier, unit-norm by construction — NOT a dense float vector). It composes psi through the real morphology so decompose stays proof-gated; it degrades gracefully when the ucns package / a0_safe facade is absent (no hard ucns import).
#   owner: Erin Spencer
#   public_surface: UCNSNativeEmbedding, embed_text, phase_compose, UCNS_CARRIER_ARITY, EMBED_LANES
#   internal_surface: _lane_values, _bone_skeleton
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.ucns_embed_deterministic_holds
#   rollout: default_enabled
#   rollback: revert; the training view loses its UCNS-native embedding readout
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: il_ucns_embed_boundaries
#   summary: pure text -> unit-circle phase-stream embedding; no io, no network
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: il_ucns_embed
#   summary: UCNS-native (unit-circle phase-stream) embedding of text
#   exposes: UCNSNativeEmbedding, embed_text, phase_compose, UCNS_CARRIER_ARITY, EMBED_LANES
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: ucns_embed_deterministic
#   given: the same text embedded twice, and two different texts
#   then: embed_text is deterministic (equal angle_bits + hash), unit-norm by
#         construction, and distinct texts yield distinct canonical hashes
#   class: correctness
#   call: a0p_skills.contracts.ucns_embed_deterministic_holds
# === END CONTRACTS ===
"""UCNS-native embedding: text -> unit-circle phase streams on the 157-gonal carrier.

A "UCNS-native embedding" here is the a0p-native phase-stream form (mirroring
``ucns.embedding.UCNEmbedding`` and ``ucns_cache`` primitive streams): a value is
expressed as angles on the unit circle over a prime carrier, unit-norm by
construction, rather than as a dense float vector. Each lane's angle blends the
three gonal cores with the canonical weights (phi 0.4 + omega 0.8 + psi 1.0),
where psi = phi carrier-LCM omega is composed through ``zfae.morphology`` (the
real UCNS multiply / recompose path — decomposition stays proof-gated). No hard
dependency on the ``ucns`` package: if its ``a0_safe`` facade is missing the
carrier-LCM degrades to identity and psi contributes 0, but the embedding is
still deterministic and unit-norm.
"""
from __future__ import annotations
import hashlib
import math
import re
from dataclasses import dataclass
from typing import Optional

from .zfae.morphology import (
    BoneGonal, compose_word, word_signal,
    OMEGA_WEIGHT, PHI_WEIGHT, PSI_WEIGHT,
)
from .zfae.closed_tokens import strip_affixes


UCNS_CARRIER_ARITY = 157   # the prime carrier (157-gonal); the phase "disk"
EMBED_LANES = 53           # payload width d=53 (matches the three-core payload)
_TWO16 = 65536
_TOKEN_RE = re.compile(r"[a-z0-9']+")
_BONES = frozenset(BoneGonal().bones)   # closed-class + affix bone tokens (omega source)


def _lane_values(seed: bytes) -> tuple[float, ...]:
    """Deterministic EMBED_LANES floats in [0, 1) from a blake2b digest of ``seed``."""
    digest = hashlib.blake2b(seed, digest_size=EMBED_LANES).digest()
    return tuple(b / 256.0 for b in digest)


def _bone_skeleton(text: str) -> str:
    """The structural (omega) skeleton: bone tokens PLUS the bound-affix material.

    Whole closed-class / standalone-affix tokens contribute directly. For an
    ordinary inflected/prefixed word (``reopened``, ``running``) whose bone is a
    *bound* morpheme, ``strip_affixes`` peels it to its root; the removed
    prefix/suffix characters are the structural material and are emitted so omega
    reflects them too (previously such words contributed nothing). This uses the
    existing deterministic structural approximation — not the proof-gated
    morphology decompose path — so it stays recompose-only.
    """
    units: list[str] = []
    for t in _TOKEN_RE.findall(text.lower()):
        if t in _BONES:
            units.append(t)
            continue
        root = strip_affixes(t)
        if root and root != t:
            idx = t.find(root)
            if idx >= 0:
                pre, suf = t[:idx], t[idx + len(root):]
                if pre:
                    units.append(pre)   # bound prefix material
                if suf:
                    units.append(suf)   # bound suffix material
            else:
                units.append("aff")     # affixes peeled but root not contiguous
    return " ".join(units)


@dataclass(frozen=True)
class UCNSNativeEmbedding:
    """A unit-circle phase-stream embedding over the 157-gonal carrier.

    ``angle_bits[i]`` is the lane-i angle quantized to 16 bits (0..65535 == a full
    turn); ``chirality[i]`` in {+1, -1} is the Mobius face of that lane's phase.
    Unit-norm holds by construction (every lane sits on the unit circle).
    """
    angle_bits: tuple[int, ...]
    chirality: tuple[int, ...]
    carrier: int
    lanes: int
    canonical_hash: str

    def similarity(self, other: "UCNSNativeEmbedding") -> float:
        """Mean cos(delta-angle) across lanes; 1.0 == identical phases."""
        if self.lanes != other.lanes or not self.lanes:
            return 0.0
        acc = 0.0
        for a, b in zip(self.angle_bits, other.angle_bits):
            acc += math.cos(2.0 * math.pi * (a - b) / _TWO16)
        return acc / self.lanes

    def coherence(self) -> float:
        """Phase coherence |(1/n) sum e^{i*theta}| in [0,1] — how aligned the lane
        phases are. This is the meaningful psi/word surface (the frame-composed
        word_signal is structurally ~0), and it is UCNS-native (unit circle)."""
        if not self.lanes:
            return 0.0
        c = s = 0.0
        for a in self.angle_bits:
            th = 2.0 * math.pi * a / _TWO16
            c += math.cos(th); s += math.sin(th)
        return math.hypot(c / self.lanes, s / self.lanes)

    def as_dict(self) -> dict:
        return {
            "carrier": self.carrier, "lanes": self.lanes,
            "canonical_hash": self.canonical_hash,
            "angle_bits": list(self.angle_bits), "chirality": list(self.chirality),
        }


def embed_text(text: str) -> UCNSNativeEmbedding:
    """Embed ``text`` as a UCNS-native unit-circle phase stream.

    phi = content signature (whole text); omega = structural signature (bone
    skeleton); psi_i = word_signal(compose_word(phi_i, omega_i)) via the real
    carrier-LCM. angle_i = 2*pi * frac(0.4*phi_i + 0.8*omega_i + 1.0*psi_i).
    """
    text = text or ""
    phi = _lane_values(text.encode("utf-8"))
    omega = _lane_values(_bone_skeleton(text).encode("utf-8"))
    angle_bits: list[int] = []
    chirality: list[int] = []
    for i in range(EMBED_LANES):
        psi = word_signal(compose_word(phi[i], omega[i]))
        frac = (PHI_WEIGHT * phi[i] + OMEGA_WEIGHT * omega[i] + PSI_WEIGHT * psi) % 1.0
        angle = 2.0 * math.pi * frac
        angle_bits.append(int(round(frac * _TWO16)) & 0xFFFF)
        chirality.append(1 if math.sin(angle) >= 0.0 else -1)
    return UCNSNativeEmbedding(
        angle_bits=tuple(angle_bits), chirality=tuple(chirality),
        carrier=UCNS_CARRIER_ARITY, lanes=EMBED_LANES,
        canonical_hash=hashlib.blake2b(text.encode("utf-8"), digest_size=16).hexdigest(),
    )


def phase_compose(a: UCNSNativeEmbedding, b: UCNSNativeEmbedding) -> UCNSNativeEmbedding:
    """Compose two embeddings by the unit-circle product (⊠ = multiplyFuel): add
    lane angles mod one turn. This is the recompose-only session-folding operator
    used to build the chapter-scale gonol; there is no inverse here."""
    n = min(a.lanes, b.lanes)
    ab = tuple((a.angle_bits[i] + b.angle_bits[i]) & 0xFFFF for i in range(n))
    ch = tuple(1 if math.sin(2.0 * math.pi * v / _TWO16) >= 0.0 else -1 for v in ab)
    h = hashlib.blake2b((a.canonical_hash + b.canonical_hash).encode("utf-8"),
                        digest_size=16).hexdigest()
    return UCNSNativeEmbedding(angle_bits=ab, chirality=ch, carrier=a.carrier,
                              lanes=n, canonical_hash=h)


__all__ = ["UCNSNativeEmbedding", "embed_text", "phase_compose",
           "UCNS_CARRIER_ARITY", "EMBED_LANES"]
# ratios: loc_comments=92:81 imports_exports=8:4 calls_definitions=35:8
