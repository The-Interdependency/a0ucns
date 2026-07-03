# ratios: loc_comments=140:109 imports_exports=7:5 calls_definitions=54:9
# === MODULE_BUILD ===
# id: zfae_gonal_inscription
#   module_name: gonal_inscription
#   module_kind: engine
#   summary: ZFAE Native Decoder Route A — Gonal Inscription. A per-agent PrivateGonal (secret phase + permutation, seeded at instantiation) inscribes the continuous Φ/Ψ/Ω tensor field onto polygon vertices to compose a deterministic glyph stream; includes the hash-whitened 53→32 bridge
#   owner: Erin Spencer
#   public_surface: PrivateGonal, inscribe_text, whiten_payload, whitened_indices, BRIDGE_IN_WIDTH, BRIDGE_OUT_WIDTH, DEFAULT_INSCRIBE_LENGTH
#   internal_surface: _WHITEN_SCALE
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_gonal_inscription_deterministic_holds
#   rollout: default_enabled
#   rollback: decoder falls back to Route B (template compositor) when no PrivateGonal present
#   no_llm_assertion: pure mathematical inscription; MUST NOT import any provider/LLM SDK
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_gonal_inscription_boundaries
#   summary: pure deterministic inscription; no IO, no globals, no LLM
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_gonal_inscription
#   summary: continuous-tensor → glyph inscription through a per-agent PrivateGonal
#   exposes: PrivateGonal, inscribe_text, whiten_payload, whitened_indices
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_gonal_inscription_deterministic
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_gonal_inscription_deterministic_holds
# === END CONTRACTS ===
"""ZFAE Native Decoder — Route A (Gonal Inscription).

Route B (``_decoder.py``) composes assistantText from a fixed fragment pool
conditioned on scalar energies. Route A is the continuous-field decoder: it
takes the FULL 53-wide Φ/Ψ/Ω tensors (no scalar collapse) and inscribes them,
angle-by-angle, onto the vertices of a per-agent **PrivateGonal**.

A PrivateGonal is a 157-position circular carrier with:
  - ``phase`` — a secret rotation offset (seeded at agent instantiation),
  - ``perm``  — a secret bijection of the 157 vertex indices.

``advance(public, pcea_digest)`` rotates the gonal deterministically between
emission steps; ``inscribe(angle) → vertex_idx`` maps a continuous angle to a
permuted vertex. The character at that vertex is the emitted glyph.

Determinism: every step is blake2b-seeded from the PCEA ciphertext digest, so
identical state → identical inscription. No randomness, no IO, no LLM.
"""
from __future__ import annotations
import hashlib
import math
import struct
from dataclasses import dataclass

from ..gonal.registry import get_default
from .morphology import (
    compose_word, word_signal, word_carrier,
    OMEGA_WEIGHT, PHI_WEIGHT, PSI_WEIGHT,
)


BRIDGE_IN_WIDTH: int = 53
BRIDGE_OUT_WIDTH: int = 32
DEFAULT_INSCRIBE_LENGTH: int = 48

# Fixed-point scale used only to serialise floats into the whitening buffer.
# Deterministic; the exact value is immaterial as long as it is constant.
_WHITEN_SCALE: int = 1 << 20


def whiten_payload(payload: list[float], digest_seed: bytes) -> bytes:
    """Hash-whitened 53→32 bridge.

    Compress the 53-wide continuous payload (plus a state-bound digest seed)
    down to a uniform 32-byte digest.

    CONCESSION: blake2b is used here as a stand-in for a UCNS-native whitening
    of the continuous 53-wide payload into a uniform field. A true UCNS-native
    53→32 whitening — one that preserves the substrate's algebraic structure
    rather than hashing it away — remains OPEN RESEARCH. This candidate bridge
    resists trivial keystream-reuse but is NOT claimed to be IND-CPA secure.
    """
    buf = bytearray()
    for i in range(BRIDGE_IN_WIDTH):
        v = float(payload[i]) if i < len(payload) else 0.0
        buf += struct.pack("<i", int(round(v * _WHITEN_SCALE)))
    buf += digest_seed
    return hashlib.blake2b(bytes(buf), digest_size=BRIDGE_OUT_WIDTH).digest()


def whitened_indices(whitened: bytes, n: int, count: int) -> list[int]:
    """Expand a 32-byte whitened digest into ``count`` indices in range(n).

    blake2b 4-byte slice mod n; re-hashes with a counter when more than 8
    indices are needed (a 32-byte digest yields 8 four-byte slices).
    """
    out: list[int] = []
    ctr = 0
    while len(out) < count:
        block = whitened if ctr == 0 else hashlib.blake2b(
            whitened + ctr.to_bytes(2, "little"), digest_size=BRIDGE_OUT_WIDTH,
        ).digest()
        for off in range(0, BRIDGE_OUT_WIDTH, 4):
            if len(out) >= count:
                break
            (raw,) = struct.unpack("<I", block[off:off + 4])
            out.append(raw % n)
        ctr += 1
    return out


@dataclass(frozen=True)
class PrivateGonal:
    """A per-agent secret gonal: a public 157-arrangement rotated by a secret
    ``phase`` and re-indexed by a secret ``perm``. Immutable — ``advance``
    returns a new instance."""

    arrangement: tuple[str, ...]
    phase: int
    perm: tuple[int, ...]

    @property
    def n(self) -> int:
        return len(self.arrangement)

    @classmethod
    def from_seed(cls, seed_bytes: bytes, arrangement: list[str] | None = None) -> "PrivateGonal":
        """Derive a deterministic PrivateGonal from a secret seed.

        The arrangement (vertex characters) is the public default 157-gonal;
        the secrecy lives entirely in ``phase`` and ``perm`` derived from the
        per-agent seed.

        SEAM INVARIANT (canon): position 0 is SPACE/ZERO — the Möbius twist
        point, seam and origin, the only always-known character. Private
        rotations and permutations may obscure every *nonzero* glyph position
        but MUST NOT move or hide position 0. So ``perm[0] == 0`` always, and
        both the permutation and the phase rotation act only on positions
        1..n-1 (the nonzero ring).
        """
        arr = tuple(arrangement) if arrangement is not None else tuple(get_default())
        n = len(arr)
        # The phase rotates the nonzero ring (n-1 positions); the seam is fixed.
        phase = int.from_bytes(
            hashlib.blake2b(seed_bytes + b"::phase", digest_size=8).digest(), "big",
        ) % (n - 1)
        # Deterministic Fisher–Yates over the NONZERO positions 1..n-1 only;
        # position 0 (SPACE/ZERO) stays fixed (perm[0] == 0).
        perm = list(range(n))
        state = hashlib.blake2b(seed_bytes + b"::perm", digest_size=8).digest()
        for i in range(n - 1, 1, -1):
            state = hashlib.blake2b(state, digest_size=8).digest()
            j = 1 + int.from_bytes(state, "big") % i
            perm[i], perm[j] = perm[j], perm[i]
        return cls(arrangement=arr, phase=phase, perm=tuple(perm))

    def advance(self, public: int, pcea_digest: str) -> "PrivateGonal":
        """Rotate the gonal deterministically against a public counter + the
        PCEA ciphertext digest. Returns a new PrivateGonal (immutable).

        The rotation advances the nonzero ring only (mod n-1); the seam at
        position 0 is never displaced."""
        h = hashlib.blake2b(
            f"{self.phase}:{int(public)}:{pcea_digest}".encode("utf-8"), digest_size=8,
        ).digest()
        new_phase = (self.phase + int.from_bytes(h, "big")) % (self.n - 1)
        return PrivateGonal(arrangement=self.arrangement, phase=new_phase, perm=self.perm)

    def inscribe(self, angle: float) -> int:
        """Map a continuous angle (any real) to a permuted vertex index.

        Landing on the seam (base position 0) emits SPACE/ZERO unconditionally —
        it is never rotated or permuted away. Every other angle rotates within,
        and permutes across, the 156 nonzero positions only."""
        frac = (float(angle) / (2.0 * math.pi)) % 1.0
        base = int(frac * self.n) % self.n
        if base == 0:
            return self.perm[0]  # == 0 — the seam: SPACE/ZERO
        rotated = ((base - 1 + self.phase) % (self.n - 1)) + 1
        return self.perm[rotated]

    def char_at(self, vertex_idx: int) -> str:
        return self.arrangement[vertex_idx % self.n]


def inscribe_text(
    gonal: PrivateGonal,
    phi53: list[float],
    psi53: list[float],
    omega53: list[float],
    pcea_digest: str,
    *,
    canon_digest: str = "",
    length: int = DEFAULT_INSCRIBE_LENGTH,
) -> tuple[str, dict]:
    """Compose a deterministic glyph stream by inscribing the Φ/Ψ/Ω field.

    For each emission step the whitened bridge selects a tensor lane; the
    Φ/Ψ/Ω values on that lane form an angle; the (advanced) gonal inscribes
    the angle to a vertex; the vertex character is emitted. Pure + deterministic.

    Returns ``(text, decode_meta)`` where ``decode_meta`` carries the first
    vertex, the final rotation and the digest prefix for the FIQ audit event.
    """
    seed = (pcea_digest + canon_digest).encode("utf-8")
    combined = [
        (phi53[i] if i < len(phi53) else 0.0)
        + (psi53[i] if i < len(psi53) else 0.0)
        + (omega53[i] if i < len(omega53) else 0.0)
        for i in range(BRIDGE_IN_WIDTH)
    ]
    whitened = whiten_payload(combined, seed)
    lanes = whitened_indices(whitened, BRIDGE_IN_WIDTH, length)

    chars: list[str] = []
    g = gonal
    first_vertex: int | None = None
    first_word_carrier: int | None = None
    seam_emissions = 0
    for i in range(length):
        lane = lanes[i]
        # Depth-ladder composition (Erin canon): omega (bones, 0.8) and phi
        # (roots, 0.4) are the primitive sources; psi (words, 1.0) is DERIVED as
        # the carrier-LCM of the two on this lane — never an independent input.
        phi_v = phi53[lane] if lane < len(phi53) else 0.0
        omega_v = omega53[lane] if lane < len(omega53) else 0.0
        word = compose_word(phi_v, omega_v)
        if first_word_carrier is None:
            first_word_carrier = word_carrier(word)
        psi_sig = word_signal(word)
        angle = 2.0 * math.pi * (
            PHI_WEIGHT * phi_v
            + OMEGA_WEIGHT * omega_v
            + PSI_WEIGHT * psi_sig
        )
        g = g.advance(i, pcea_digest)
        v = g.inscribe(angle)
        if first_vertex is None:
            first_vertex = v
        ch = g.char_at(v)
        # Landing on the seam (vertex 0 → SPACE/ZERO) is an emitted seam event,
        # NOT a deletion. Only NUL/control glyphs are skipped.
        if v == 0:
            seam_emissions += 1
            chars.append(" ")
        elif ch and ch != "\x00" and not ch.startswith("\x00"):
            chars.append(ch)

    # Spaces are seam events — preserved, never trimmed away.
    text = "".join(chars)
    if not text:
        text = "·"
    meta = {
        "vertex_idx": first_vertex if first_vertex is not None else -1,
        "rotation": g.phase,
        "pcea_digest_prefix": pcea_digest[:8],
        "glyph_count": len(chars),
        "word_carrier": first_word_carrier if first_word_carrier is not None else 1,
        "seam_emissions": seam_emissions,
    }
    return text, meta


__all__ = [
    "PrivateGonal",
    "inscribe_text",
    "whiten_payload",
    "whitened_indices",
    "BRIDGE_IN_WIDTH",
    "BRIDGE_OUT_WIDTH",
    "DEFAULT_INSCRIBE_LENGTH",
]
# ratios: loc_comments=140:109 imports_exports=7:5 calls_definitions=54:9
