# ratios: loc_comments=26:56 imports_exports=3:3 calls_definitions=1:12
# === MODULE_BUILD ===
# id: carrier_disk_protocol
#   module_name: disk_protocol
#   module_kind: schema
#   summary: CarrierDisk Protocol — what any disk implementation (public fixture or private canon) must provide; CarrierDiskUnavailable error type
#   owner: Erin Spencer
#   public_surface: CarrierDisk, CarrierDiskUnavailable, DiskSignature
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.carrier_disk_protocol_holds
#   rollout: default_enabled
#   rollback: revert file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: carrier_disk_protocol_boundaries
#   summary: CarrierDisk Protocol — what any disk implementation (public fixture or private canon) must provide; CarrierDiskUnavailable error type
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: carrier_disk_protocol
#   summary: CarrierDisk Protocol — what any disk implementation (public fixture or private canon) must provide; CarrierDiskUnavailable error type
#   exposes: CarrierDisk, CarrierDiskUnavailable, DiskSignature
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: carrier_disk_protocol
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.carrier_disk_protocol_holds
# === END CONTRACTS ===
"""CarrierDisk Protocol.

This module never holds canon position data. It only defines the shape
that consumers of `theta_microkernel.carrier_disk()` depend on.
"""
from __future__ import annotations
from typing import Protocol, runtime_checkable
from .classes import ClassTag


class CarrierDiskUnavailable(RuntimeError):
    """Raised when no canon disk is configured and no public-fixture fallback is in scope.

    This MUST be raised — never silently synthesised.
    """


@runtime_checkable
class CarrierDisk(Protocol):
    """Any 157-arrangement (canon OR public fixture) must satisfy this surface."""

    def class_at(self, k: int) -> ClassTag:
        """Return the class tag for position k ∈ [0, 157)."""
        ...

    def positions_of(self, tag: ClassTag) -> tuple[int, ...]:
        """Return all positions whose class is `tag`, in ascending order."""
        ...

    def signature(self) -> "DiskSignature":
        """Public summary — counts only; never the arrangement itself."""
        ...


class DiskSignature(Protocol):
    """Public summary of a disk.

    Only counts may be exposed. Specific positions are PRIVATE for the canon disk.
    """
    @property
    def arity(self) -> int: ...
    @property
    def l_count(self) -> int: ...
    @property
    def n_count(self) -> int: ...
    @property
    def p_count(self) -> int: ...
    @property
    def x_count(self) -> int: ...
    @property
    def is_canon(self) -> bool:
        """True iff this is the private canon disk (theta_microkernel-loaded)."""
        ...
# ratios: loc_comments=26:56 imports_exports=3:3 calls_definitions=1:12
