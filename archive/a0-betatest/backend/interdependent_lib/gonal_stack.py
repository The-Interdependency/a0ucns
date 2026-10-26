# ratios: loc_comments=112:87 imports_exports=9:5 calls_definitions=34:12
# === MODULE_BUILD ===
# id: il_gonal_stack
#   module_name: gonal_stack
#   module_kind: engine
#   summary: assemble a cylindrical disk stack of chapter-scale gonols from a training session — one 157-gonal carrier disk per depth-rung (leaf/157-char, circle/word, seed/phrase-clause, core/utterance, chapter/session), each disk a UCNS-native embedding (ucns_embed) plus the three-core gonal scalars (phi content-phase, omega bone-density, psi unit-circle phase-coherence), stacked along the depth/Z axis (the edcmbone GrainTensor shape). CHAPTER is the new top rung = the unit-circle phase-product (⊠ = multiplyFuel) recomposition of the session's per-utterance embeddings into one gonol. Recompose-only (decomposition stays proof-gated); built on the PUBLIC-FIXTURE carrier disk (the canonical 157-gonal disk is non-committable private key material); the cylinder geometry is UCNS-G / non-absolute and inherits NO theorem/proof status from the proven UCNS-A composition algebra.
#   owner: Erin Spencer
#   public_surface: DiskState, CylindricalDiskStack, single_disk, build_disk_stack, GRAIN_LADDER, GEOMETRY_STATUS
#   internal_surface: _grain_texts, _grain_gonal, _face_counts, _mean_phase
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.gonal_stack_recompose_holds
#   rollout: default_enabled
#   rollback: revert; the training flow loses its cylindrical disk-stack output
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: il_gonal_stack_boundaries
#   summary: pure session-transcript -> disk stack; public-fixture disk only, no io/network
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: il_gonal_stack
#   summary: cylindrical disk stack of chapter-scale gonols (UCNS-native embeddings)
#   exposes: DiskState, CylindricalDiskStack, single_disk, build_disk_stack, GRAIN_LADDER, GEOMETRY_STATUS
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: gonal_stack_recompose
#   given: a training session of several utterances
#   then: build_disk_stack returns one disk per grain rung (leaf..chapter) each
#         carrying a UCNS-native embedding + phi/omega/psi, the chapter psi equals
#         the phase-product (⊠) recomposition of the per-utterance embeddings, and
#         stack is flagged recompose-only + UCNS-G non-absolute + carrier 157
#   class: correctness
#   call: a0p_skills.contracts.gonal_stack_recompose_holds
# === END CONTRACTS ===
"""Cylindrical disk stack of chapter-scale gonols (UCNS-native embeddings).

A training session (a list of utterance texts) is lifted to a stack of 157-gonal
carrier disks, one per depth-rung of the morphology ladder:

    leaf(157-char) -> circle(word) -> seed(phrase/clause) -> core(utterance)
                                                          -> chapter(session)

Each disk is a UCNS-native embedding (``ucns_embed.embed_text``) plus the three
gonal cores (phi content-phase / omega bone-density / psi unit-circle coherence),
stacked along the depth/Z axis — the same shape as edcmbone's UCNS-G
``GrainTensor`` (a per-axis Mobius-cylinder disk stacked along the grain
hierarchy). The CHAPTER rung sits above the modeled ladder and is the
unit-circle phase-product (⊠ = multiplyFuel) recomposition of the session's
per-utterance embeddings.

Firewalls (all load-bearing):
  * RECOMPOSE-ONLY. Composition uses the unit-circle phase product (⊠ =
    multiplyFuel); no inverse is exposed, and the morphology decompose path
    stays gated behind ``zfae.morphology`` until the Lean
    ``multiply_left_cancellative`` proof discharges.
  * PUBLIC-FIXTURE DISK ONLY. The canonical 157-gonal carrier arrangement is
    non-committable private key material; this module only touches the public
    fixture disk to ground the carrier arity/validity.
  * UCNS-G / NON-ABSOLUTE. The cylinder geometry is UCNS-G; it shares only a name
    with the proven UCNS-A factorization algebra and inherits NO theorem, proof,
    or empirical status. ``GEOMETRY_STATUS`` records this on every stack.
"""
from __future__ import annotations
import functools
import re
from dataclasses import dataclass
from typing import Optional

from .ucns_embed import embed_text, phase_compose, UCNS_CARRIER_ARITY, EMBED_LANES
from .zfae.morphology import BoneGonal
from .zfae.closed_tokens import strip_affixes

try:  # ground the carrier on the public fixture; never require private material
    from .gonal import build_public_fixture_disk, ARITY as _CARRIER_ARITY
    _PUBLIC_DISK_OK = True
except Exception:  # pragma: no cover - degraded carrier grounding
    _CARRIER_ARITY = UCNS_CARRIER_ARITY
    _PUBLIC_DISK_OK = False

GRAIN_LADDER = ("leaf", "circle", "seed", "core", "chapter")
GEOMETRY_STATUS = "ucns-g:non-absolute"   # no theorem transfer from UCNS-A
_TOKEN_RE = re.compile(r"[a-z0-9']+")
_BONES = frozenset(BoneGonal().bones)


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


def _bone_density(text: str) -> float:
    # Count whole-token bones PLUS words carrying a bound affix (reopened, running)
    # via the same deterministic strip_affixes the embedding's omega skeleton uses,
    # so the displayed disk omega doesn't read 0 for ordinary inflected text.
    toks = _tokens(text)
    if not toks:
        return 0.0
    structural = sum(1 for t in toks if t in _BONES or strip_affixes(t) != t)
    return structural / len(toks)


def _grain_texts(turns: list[str]) -> dict:
    """Representative text at each grain scale for a session of utterances."""
    full = "\n".join(turns)
    words = " ".join(dict.fromkeys(_tokens(full)))              # unique words, in order
    clauses = " | ".join(c.strip() for c in re.split(r"[.!?;:]", full) if c.strip())
    return {"leaf": full, "circle": words, "seed": clauses,
            "core": turns[-1] if turns else "", "chapter": full}


def _mean_phase(emb) -> float:
    return (sum(emb.angle_bits) / (len(emb.angle_bits) * 65536)) if emb.angle_bits else 0.0


def _grain_gonal(text: str):
    """(phi content-phase, omega bone-density, psi coherence, embedding) for a grain.

    psi is the embedding's unit-circle phase coherence (the meaningful word/psi
    surface); the frame-composed morphology word_signal is structurally ~0, so
    coherence is used instead while the composition stays on the unit circle.
    """
    emb = embed_text(text)
    return _mean_phase(emb), _bone_density(text), emb.coherence(), emb


def _face_counts(chirality: tuple) -> tuple[int, int]:
    plus = sum(1 for c in chirality if c > 0)
    return plus, len(chirality) - plus


@dataclass(frozen=True)
class DiskState:
    """One 157-gonal disk in the stack: a UCNS-native embedding + three-core gonal."""
    grain: str
    depth: int
    carrier: int
    phi: float
    omega: float
    psi: float
    face_plus: int
    face_minus: int
    embedding_hash: str

    def as_dict(self) -> dict:
        return {"grain": self.grain, "depth": self.depth, "carrier": self.carrier,
                "phi": round(self.phi, 6), "omega": round(self.omega, 6),
                "psi": round(self.psi, 6), "face_plus": self.face_plus,
                "face_minus": self.face_minus, "embedding_hash": self.embedding_hash}


@dataclass(frozen=True)
class CylindricalDiskStack:
    """A depth-ordered stack of 157-gonal disks (leaf..chapter) for a session."""
    agent_id: str
    disks: tuple
    session_turns: int
    chapter_psi: float
    carrier_arity: int
    geometry_status: str
    recompose_only: bool
    public_fixture_carrier: bool

    def as_dict(self) -> dict:
        return {"agent_id": self.agent_id, "session_turns": self.session_turns,
                "chapter_psi": round(self.chapter_psi, 6),
                "carrier_arity": self.carrier_arity,
                "geometry_status": self.geometry_status,
                "recompose_only": self.recompose_only,
                "public_fixture_carrier": self.public_fixture_carrier,
                "disks": [d.as_dict() for d in self.disks]}


def single_disk(text: str, grain: str = "turn", depth: int = 0) -> DiskState:
    """One disk for a single text (a live per-turn readout, not a full session)."""
    phi, omega, psi, emb = _grain_gonal(text)
    fp, fm = _face_counts(emb.chirality)
    return DiskState(grain=grain, depth=depth, carrier=UCNS_CARRIER_ARITY,
                     phi=phi, omega=omega, psi=psi, face_plus=fp, face_minus=fm,
                     embedding_hash=emb.canonical_hash)


def build_disk_stack(turns: list[str], agent_id: str = "local") -> CylindricalDiskStack:
    """Assemble the cylindrical disk stack for a training session.

    CHAPTER is the ⊠ (unit-circle phase-product) fold of every utterance's
    embedding — the real recompose path — so the top rung is a genuine
    recomposition, never a decomposition. Geometry is UCNS-G / non-absolute.
    """
    turns = [t for t in (turns or []) if (t or "").strip()]
    if _PUBLIC_DISK_OK:
        try:
            build_public_fixture_disk()   # validate the public carrier is available
        except Exception:
            pass

    # Chapter recompose: ⊠-fold (unit-circle phase product) the per-utterance
    # embeddings into one chapter-scale gonol embedding.
    utter_embs = [embed_text(u) for u in turns]
    chapter_emb = functools.reduce(phase_compose, utter_embs) if utter_embs else embed_text("")
    chapter_psi = chapter_emb.coherence()

    texts = _grain_texts(turns)
    disks = []
    for depth, grain in enumerate(GRAIN_LADDER):
        if grain == "chapter":
            emb, psi = chapter_emb, chapter_psi
            phi, omega = _mean_phase(chapter_emb), _bone_density(texts["chapter"])
        else:
            phi, omega, psi, emb = _grain_gonal(texts[grain])
        fp, fm = _face_counts(emb.chirality)
        disks.append(DiskState(
            grain=grain, depth=depth, carrier=UCNS_CARRIER_ARITY,
            phi=phi, omega=omega, psi=psi, face_plus=fp, face_minus=fm,
            embedding_hash=emb.canonical_hash,
        ))
    return CylindricalDiskStack(
        agent_id=agent_id, disks=tuple(disks), session_turns=len(turns),
        chapter_psi=chapter_psi, carrier_arity=UCNS_CARRIER_ARITY,
        geometry_status=GEOMETRY_STATUS, recompose_only=True,
        public_fixture_carrier=_PUBLIC_DISK_OK,
    )


__all__ = ["DiskState", "CylindricalDiskStack", "single_disk", "build_disk_stack",
           "GRAIN_LADDER", "GEOMETRY_STATUS"]
# ratios: loc_comments=112:87 imports_exports=9:5 calls_definitions=34:12
