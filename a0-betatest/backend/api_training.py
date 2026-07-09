# ratios: loc_comments=51:73 imports_exports=8:5 calls_definitions=20:5
# === MODULE_BUILD ===
# id: api_training_routes
#   module_name: training
#   module_kind: route
#   summary: backend for the standalone Chat Training tab — turns the inference-engine chat-training loop into three inspectable readouts wired to the same primitives the ZFAE engine trains on. POST /api/training/readout lifts one turn (with optional prior) into its UCNS-native embedding (unit-circle phase streams on the 157-gonal carrier), its six-family EDCM projection (CM/DA/DRIFT/DVG/INT/TBF with 0.80/0.20 alert bands), and its three-core gonal disk (phi content-phase / omega bone-density / psi unit-circle coherence). POST /api/training/disk-stack folds a whole session of utterances into a cylindrical disk stack of chapter-scale gonols — one 157-gonal disk per depth-rung (leaf..chapter), the chapter rung being the ⊠ (unit-circle phase-product) recomposition of the per-utterance embeddings. Pure read-only computation over the request text; actual weight training stays on the existing /api/instances/{id}/train route. Recompose-only, public-fixture carrier, UCNS-G / non-absolute (no theorem transfer).
#   owner: Erin Spencer
#   public_surface: router
#   internal_surface: ReadoutBody, DiskStackBody
#   auth_boundary: bearer
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.api_training_readout_holds
#   rollout: default_enabled
#   rollback: revert + unmount from server.py; the Chat Training tab loses its readout/disk-stack endpoints
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: api_training_routes_boundaries
#   summary: REST endpoints computing embedding/EDCM/gonal readouts + disk stacks from request text
#   auth_boundary: bearer
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: api_training_routes
#   summary: UCNS-native embedding + EDCM projection + cylindrical gonal disk-stack readouts for the training tab
#   exposes: router
#   boundaries: auth:bearer, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: api_training_readout
#   given: the training router and a turn (with and without a prior)
#   then: /readout and /disk-stack handlers return the embedding + EDCM + gonal
#         disk / cylindrical stack shapes, flagged recompose-only + non-absolute
#   class: correctness
#   call: a0p_skills.contracts.api_training_readout_holds
# === END CONTRACTS ===
"""Chat Training tab backend: embedding + EDCM + cylindrical gonal disk-stack readouts.

Three primitives, one tab. Each POST is a pure, deterministic read over the
request text (no storage, no network) so the frontend can render the substrate a
training turn touches:

  * the UCNS-native embedding (``interdependent_lib.ucns_embed``) — unit-circle
    phase streams on the 157-gonal carrier;
  * the six-family EDCM projection (``interdependent_lib.edcm_readout``);
  * the three-core gonal disk / cylindrical stack
    (``interdependent_lib.gonal_stack``) — the chapter rung is the ⊠
    (phase-product) recomposition of the session.

Actual weight training (teacher distillation into the per-instance ZFAE
checkpoint) stays on the existing ``/api/instances/{id}/train`` route; this module
only exposes the inspectable readouts beside it. Firewalls inherited from the
underlying modules hold: recompose-only, public-fixture carrier, UCNS-G /
non-absolute (no theorem/proof transfer from UCNS-A).
"""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator

from auth import get_current_user
from interdependent_lib.ucns_embed import embed_text
from interdependent_lib.edcm_readout import readout
from interdependent_lib.gonal_stack import single_disk, build_disk_stack, GEOMETRY_STATUS


router = APIRouter(prefix="/api/training", tags=["training"])

_MAX_TURNS = 200
_MAX_CHARS = 20_000
# Explicit aggregate cap for a whole session (build_disk_stack joins + tokenizes +
# hashes it synchronously) — a small fixed limit, NOT _MAX_TURNS * _MAX_CHARS.
_MAX_SESSION_CHARS = 200_000


class ReadoutBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=False)
    text: str = Field(..., min_length=1, max_length=_MAX_CHARS)
    prev_text: Optional[str] = Field(None, max_length=_MAX_CHARS)
    grain: str = Field("turn", max_length=32)


class DiskStackBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=False)
    turns: list[str] = Field(..., min_length=1, max_length=_MAX_TURNS)
    agent_id: str = Field("local", min_length=1, max_length=64)

    @field_validator("turns")
    @classmethod
    def _bound_turn_text(cls, v: list[str]) -> list[str]:
        # Cap each turn AND the aggregate session text — the count cap alone lets a
        # few very large strings block the event loop when build_disk_stack joins /
        # tokenizes / hashes them synchronously. Mirrors ReadoutBody.text's cap.
        total = 0
        for t in v:
            if len(t) > _MAX_CHARS:
                raise ValueError(f"each turn must be <= {_MAX_CHARS} chars")
            total += len(t)
        if total > _MAX_SESSION_CHARS:
            raise ValueError(f"aggregate session text must be <= {_MAX_SESSION_CHARS} chars")
        return v


@router.post("/readout")
async def training_readout(body: ReadoutBody, user=Depends(get_current_user)):
    """One training turn -> UCNS-native embedding + EDCM projection + gonal disk.

    The three panels of the Chat Training tab for a single turn. ``prev_text``
    (the previous turn) sharpens the EDCM drift/divergence/turn-balance families;
    without it EDCM uses its no-prior handling.
    """
    emb = embed_text(body.text)
    edcm = readout(body.text, body.prev_text, grain=body.grain)
    disk = single_disk(body.text, grain=body.grain)
    return {
        "grain": body.grain,
        "embedding": emb.as_dict(),
        "coherence": round(emb.coherence(), 6),
        "edcm": edcm.as_dict(),
        "disk": disk.as_dict(),
        "geometry_status": GEOMETRY_STATUS,
        "recompose_only": True,
    }


@router.post("/disk-stack")
async def training_disk_stack(body: DiskStackBody, user=Depends(get_current_user)):
    """A whole session -> a cylindrical disk stack of chapter-scale gonols.

    One 157-gonal disk per depth-rung (leaf/circle/seed/core/chapter); the chapter
    rung is the ⊠ (unit-circle phase-product) recomposition of every utterance's
    embedding. Recompose-only, public-fixture carrier, UCNS-G / non-absolute.
    """
    stack = build_disk_stack(body.turns, agent_id=body.agent_id)
    return stack.as_dict()


__all__ = ["router"]
# ratios: loc_comments=51:73 imports_exports=8:5 calls_definitions=20:5
