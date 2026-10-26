# ratios: loc_comments=51:62 imports_exports=6:3 calls_definitions=14:8
# === MODULE_BUILD ===
# id: carrier_public_fixture
#   module_name: public_fixture
#   module_kind: experiment
#   summary: public fixture disk generator — binary-order rule per user spec; deterministic, committable, satisfies hard invariants, NOT the canon
#   owner: Erin Spencer
#   public_surface: build_public_fixture_disk, PublicFixtureDisk
#   internal_surface: _PUBLIC_L_STEP, _PUBLIC_N_STEP, _origin_class
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.carrier_public_fixture_is_valid_and_distinct_holds
#   rollout: default_enabled
#   rollback: revert file
#   security_note: this generator and its parameters are PUBLIC; they do NOT reproduce the canon disk
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: carrier_public_fixture_boundaries
#   summary: public fixture disk generator — binary-order rule per user spec; deterministic, committable, satisfies hard invariants, NOT the canon
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: carrier_public_fixture
#   summary: public fixture disk generator — binary-order rule per user spec; deterministic, committable, satisfies hard invariants, NOT the canon
#   exposes: build_public_fixture_disk, PublicFixtureDisk
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: carrier_public_fixture_is_valid_and_distinct
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.carrier_public_fixture_is_valid_and_distinct_holds
# === END CONTRACTS ===
"""Public fixture disk — binary-order rule, obviously-not-canon.

Public rule (committable, auditable):
  • L slots at positions {0, 3, 6, ..., 78} — origin + 26 upper L, step 3 from 0.
  • N slots at positions {79, 87, 95, ..., 151} — step 8 starting at 79, 10 positions.
  • Remaining lower-arc positions split: P at first 32, X at last 36.
  • Remaining upper-arc positions: all X (52 slots).

This passes the public hard invariants (no L-L, no N-N adjacent) and the
class counts match the public spec. The specific step values (3 and 8)
are PUBLIC and DIFFERENT from the canon disk's step values.
"""
from __future__ import annotations
from dataclasses import dataclass

from .classes import ClassTag
from .disk_protocol import CarrierDisk, DiskSignature
from .faces import ARITY, UPPER_ARC_RANGE, LOWER_ARC_RANGE, ORIGIN

_PUBLIC_L_STEP: int = 3   # PUBLIC — see security_note
_PUBLIC_N_STEP: int = 8   # PUBLIC — see security_note


@dataclass(frozen=True)
class _Signature:
    arity: int
    l_count: int
    n_count: int
    p_count: int
    x_count: int
    is_canon: bool = False


class PublicFixtureDisk:
    """Concrete CarrierDisk implementation for public testing — binary-order rule."""

    __slots__ = ("_class_map",)

    def __init__(self) -> None:
        class_map: list[ClassTag] = [ClassTag.X] * ARITY

        # L positions: origin + step 3 across upper arc → 27 positions total.
        l_positions = [k for k in range(0, UPPER_ARC_RANGE[1] + 1, _PUBLIC_L_STEP)]
        # Cap to canon count (1 origin + 26 upper = 27)
        l_positions = l_positions[:27]
        for k in l_positions:
            class_map[k] = ClassTag.L

        # Upper-arc remaining slots → X (already X by default).

        # N positions: step 8 starting at 79 → 10 positions.
        n_positions = [k for k in range(LOWER_ARC_RANGE[0], LOWER_ARC_RANGE[1] + 1, _PUBLIC_N_STEP)]
        n_positions = n_positions[:10]
        for k in n_positions:
            class_map[k] = ClassTag.N

        # Lower-arc remaining: first 32 P, last 36 X.
        n_set = set(n_positions)
        lower_remaining = [k for k in range(LOWER_ARC_RANGE[0], LOWER_ARC_RANGE[1] + 1) if k not in n_set]
        for k in lower_remaining[:32]:
            class_map[k] = ClassTag.P
        for k in lower_remaining[32:32 + 36]:
            class_map[k] = ClassTag.X

        self._class_map = tuple(class_map)

    def class_at(self, k: int) -> ClassTag:
        return self._class_map[k % ARITY]

    def positions_of(self, tag: ClassTag) -> tuple[int, ...]:
        return tuple(k for k, t in enumerate(self._class_map) if t == tag)

    def signature(self) -> DiskSignature:
        from collections import Counter
        c = Counter(self._class_map)
        return _Signature(
            arity=ARITY,
            l_count=c.get(ClassTag.L, 0),
            n_count=c.get(ClassTag.N, 0),
            p_count=c.get(ClassTag.P, 0),
            x_count=c.get(ClassTag.X, 0),
            is_canon=False,
        )


def build_public_fixture_disk() -> CarrierDisk:
    """Return a deterministic public-fixture CarrierDisk.

    The disk satisfies all public structural invariants (correct counts,
    no L-L adjacent, no N-N adjacent) and is obviously NOT the canon disk.
    """
    return PublicFixtureDisk()
# ratios: loc_comments=51:62 imports_exports=6:3 calls_definitions=14:8
