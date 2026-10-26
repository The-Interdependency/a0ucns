# ratios: loc_comments=86:63 imports_exports=10:1 calls_definitions=33:10
# === MODULE_BUILD ===
# id: theta_private_loader
#   module_name: _theta_private_loader
#   module_kind: adapter
#   summary: loads the canon CarrierDisk from Θ's private path; raises CarrierDiskUnavailable if not configured; NEVER falls back
#   owner: Erin Spencer
#   public_surface: load_canon_disk, CANON_DISK_ENV
#   internal_surface: _decrypt_and_parse, _validate_canon_invariants
#   auth_boundary: admin
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: true
#   tests: a0p_skills.contracts.theta_loader_refuses_no_disk_holds
#   rollout: default_enabled
#   rollback: unset A0P_CARRIER_DISK_PATH; Θ degrades to public-fixture mode
#   security_note: this module NEVER holds canon position data inline; NEVER synthesises a fallback; NEVER logs disk contents
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: theta_private_loader_boundaries
#   summary: loads the canon CarrierDisk from Θ's private path; raises CarrierDiskUnavailable if not configured; NEVER falls back
#   auth_boundary: admin
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: true
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: theta_private_loader
#   summary: loads the canon CarrierDisk from Θ's private path; raises CarrierDiskUnavailable if not configured; NEVER falls back
#   exposes: load_canon_disk, CANON_DISK_ENV
#   boundaries: auth:admin, storage:read, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: theta_loader_refuses_no_disk
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.theta_loader_refuses_no_disk_holds
# === END CONTRACTS ===
"""Private canon disk loader. Trust boundary for the Θ microkernel.

The canon disk lives outside committed source. This loader reads it
from `A0P_CARRIER_DISK_PATH` (a JSON file containing the
position→class arrangement). If the env var is unset or the file is
absent/invalid, the loader raises `CarrierDiskUnavailable` — it
NEVER constructs a fallback arrangement.

Per the security boundary (canon disk = private key material):
  - The arrangement is not committed.
  - The arrangement is not logged.
  - The arrangement is not transmitted over /api.
  - Public consumers see only public counts via `CarrierDisk.signature()`.
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass
from pathlib import Path

from ..gonal.classes import ClassTag
from ..gonal.disk_protocol import CarrierDisk, CarrierDiskUnavailable, DiskSignature
from ..gonal.faces import ARITY
from ..gonal.adjacency import hard_invariant_holds


CANON_DISK_ENV: str = "A0P_CARRIER_DISK_PATH"


@dataclass(frozen=True)
class _CanonSignature:
    arity: int
    l_count: int
    n_count: int
    p_count: int
    x_count: int
    is_canon: bool = True


class _CanonDisk:
    """Loaded canon disk. Holds the arrangement in memory; never serialises it."""

    __slots__ = ("_class_map",)

    def __init__(self, class_map: tuple[ClassTag, ...]):
        if len(class_map) != ARITY:
            raise CarrierDiskUnavailable(
                f"canon disk has wrong arity ({len(class_map)} != {ARITY})"
            )
        self._class_map = class_map

    def class_at(self, k: int) -> ClassTag:
        return self._class_map[k % ARITY]

    def positions_of(self, tag: ClassTag) -> tuple[int, ...]:
        return tuple(k for k, t in enumerate(self._class_map) if t == tag)

    def signature(self) -> DiskSignature:
        from collections import Counter
        c = Counter(self._class_map)
        return _CanonSignature(
            arity=ARITY,
            l_count=c.get(ClassTag.L, 0),
            n_count=c.get(ClassTag.N, 0),
            p_count=c.get(ClassTag.P, 0),
            x_count=c.get(ClassTag.X, 0),
            is_canon=True,
        )

    def __repr__(self) -> str:
        # Deliberately NOT showing arrangement.
        s = self.signature()
        return f"<CanonDisk arity={s.arity} L={s.l_count} N={s.n_count} P={s.p_count} X={s.x_count}>"


def _decrypt_and_parse(path: Path) -> tuple[ClassTag, ...]:
    """Read and parse the private disk file. Format: JSON list of 157 single-char class tags."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise CarrierDiskUnavailable(f"cannot read canon disk: {e}") from e
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise CarrierDiskUnavailable(f"canon disk is not valid JSON: {e}") from e
    if not isinstance(data, list) or len(data) != ARITY:
        raise CarrierDiskUnavailable(
            f"canon disk must be a list of {ARITY} class tags"
        )
    out: list[ClassTag] = []
    for i, v in enumerate(data):
        try:
            out.append(ClassTag(v))
        except ValueError:
            raise CarrierDiskUnavailable(
                f"canon disk position {i}: {v!r} is not a valid ClassTag"
            )
    return tuple(out)


def _validate_canon_invariants(disk: CarrierDisk) -> None:
    """Hard invariants must hold; otherwise the file is corrupted or not canon."""
    if not hard_invariant_holds(disk):
        raise CarrierDiskUnavailable(
            "canon disk fails hard invariant (L-L or N-N adjacency present)"
        )


def load_canon_disk() -> CarrierDisk:
    """Load the canon disk from `A0P_CARRIER_DISK_PATH`.

    Raises `CarrierDiskUnavailable` if the env var is unset, the file is
    missing, malformed, or fails hard invariants. NEVER returns a
    synthesised fallback.
    """
    env_path = os.environ.get(CANON_DISK_ENV)
    if not env_path:
        raise CarrierDiskUnavailable(
            f"canon disk not configured: env var {CANON_DISK_ENV} is unset"
        )
    path = Path(env_path).expanduser()
    if not path.is_file():
        raise CarrierDiskUnavailable(
            f"canon disk file not found at {path}"
        )
    class_map = _decrypt_and_parse(path)
    disk = _CanonDisk(class_map)
    _validate_canon_invariants(disk)
    return disk
# ratios: loc_comments=86:63 imports_exports=10:1 calls_definitions=33:10
