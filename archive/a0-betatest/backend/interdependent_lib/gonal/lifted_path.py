# ratios: loc_comments=42:75 imports_exports=3:8 calls_definitions=13:7
# === MODULE_BUILD ===
# id: gonal_lifted_path
#   module_name: lifted_path
#   module_kind: engine
#   summary: lossless lifted text traversal over the 157-gonal carrier — encode_text_path lifts a string to an ordered, strictly-monotonic path on the universal cover (vertex = pos mod 157); a repeated character costs a full 157-step revolution; SPACE is the seam at ORIGIN (vertex 0); the digit "0" is an ordinary glyph vertex; decode_text_path is the exact inverse (decode(encode(text)) == text over the carrier alphabet)
#   owner: Erin Spencer
#   public_surface: encode_text_path, decode_text_path, vertex_of_char, char_of_vertex, is_seam_event, path_vertices, CarrierCharError, ARITY, ORIGIN
#   internal_surface: _ARRANGEMENT, _VERTEX_OF_CHAR
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.gonal_lifted_path_round_trip_holds
#   rollout: default_enabled
#   rollback: revert file from git
#   no_llm_assertion: pure deterministic carrier traversal; MUST NOT import any provider/LLM SDK
#   hmmm: the carrier alphabet is the public default 157-gonal (EXAMPLE_157); characters outside it raise CarrierCharError — losslessness is over the carrier alphabet, not arbitrary Unicode
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: gonal_lifted_path_boundaries
#   summary: pure deterministic lifted traversal over the public carrier; no IO, no globals, no LLM
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: gonal_lifted_path
#   summary: lossless encode/decode of text as an ordered lifted traversal over the 157-gonal carrier
#   exposes: encode_text_path, decode_text_path, vertex_of_char, char_of_vertex, is_seam_event
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: gonal_lifted_path_round_trip
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.gonal_lifted_path_round_trip_holds
# === END CONTRACTS ===
"""Lossless lifted text traversal over the 157-gonal carrier.

The carrier is a 157-vertex ring (``ARITY = 157``) whose ``ORIGIN`` (vertex 0)
is the Möbius seam — SPACE/ZERO, the only always-known character. A **lifted
path** is an ordered, strictly-increasing sequence of positions on the universal
cover ``Z``; the vertex a position sits over is ``pos % ARITY``.

Encoding walks the carrier forward one character at a time:

  - each step advances by ``delta in [1, ARITY]`` to land on the target glyph's
    vertex,
  - ``delta == ARITY`` exactly when the target vertex equals the previous one —
    a **repeated character requires a full 157-step revolution** to be emitted
    again on the cover (so the path stays strictly monotonic and distinguishes
    the second 'a' in "aa" from the first),
  - SPACE maps to the seam (vertex 0) — an emitted **seam event**, never a
    deletion,
  - the digit ``"0"`` is an ordinary glyph at its own vertex, NOT the seam.

Decoding maps each lifted position back through ``pos % ARITY`` to its glyph, so
``decode_text_path(encode_text_path(text)) == text`` for any text over the
carrier alphabet.
"""
from __future__ import annotations

from .faces import ARITY, ORIGIN
from .registry import get_default


# The public carrier alphabet — position 0 is SPACE (the seam), per canon.
_ARRANGEMENT: tuple[str, ...] = tuple(get_default())
_VERTEX_OF_CHAR: dict[str, int] = {ch: i for i, ch in enumerate(_ARRANGEMENT)}


class CarrierCharError(ValueError):
    """Raised when a character is not present on the 157-gonal carrier."""


def vertex_of_char(ch: str) -> int:
    """The carrier vertex a single character sits on. SPACE → ORIGIN (0)."""
    if not isinstance(ch, str) or len(ch) != 1:
        raise CarrierCharError(f"expected a single character, got {ch!r}")
    v = _VERTEX_OF_CHAR.get(ch)
    if v is None:
        raise CarrierCharError(f"character {ch!r} is not on the 157-gonal carrier")
    return v


def char_of_vertex(vertex: int) -> str:
    """The glyph at a carrier vertex (vertex is taken mod ARITY)."""
    return _ARRANGEMENT[int(vertex) % ARITY]


def is_seam_event(pos: int) -> bool:
    """True iff a lifted position sits over the seam (SPACE/ZERO at ORIGIN)."""
    return int(pos) % ARITY == ORIGIN


def encode_text_path(text: str) -> list[int]:
    """Lift ``text`` to an ordered, strictly-monotonic path on the cover.

    Returns one lifted position per character. ``pos % ARITY`` is the glyph's
    vertex; the running difference is the per-step delta in ``[1, ARITY]``
    (``ARITY`` marks a repeated character — a full revolution).
    """
    path: list[int] = []
    prev_abs = ORIGIN  # start at the seam/origin on the cover
    for ch in text:
        target = vertex_of_char(ch)
        prev_vertex = prev_abs % ARITY
        # delta in [1, ARITY]; equals ARITY iff target == prev_vertex (repeat).
        delta = ((target - prev_vertex - 1) % ARITY) + 1
        prev_abs += delta
        path.append(prev_abs)
    return path


def decode_text_path(path: list[int] | tuple[int, ...]) -> str:
    """Exact inverse of :func:`encode_text_path` over the carrier alphabet."""
    return "".join(char_of_vertex(pos) for pos in path)


def path_vertices(path: list[int] | tuple[int, ...]) -> list[int]:
    """The carrier vertices a lifted path visits (``pos % ARITY`` per step)."""
    return [int(pos) % ARITY for pos in path]


__all__ = [
    "encode_text_path",
    "decode_text_path",
    "vertex_of_char",
    "char_of_vertex",
    "is_seam_event",
    "path_vertices",
    "CarrierCharError",
    "ARITY",
    "ORIGIN",
]
# ratios: loc_comments=42:75 imports_exports=3:8 calls_definitions=13:7
