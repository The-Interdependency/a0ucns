# ratios: loc_comments=53:54 imports_exports=6:3 calls_definitions=11:6
# === MODULE_BUILD ===
# id: theta_microkernel
#   module_name: theta_microkernel
#   module_kind: engine
#   summary: Θ microkernel — hosts the canon carrier disk via private loader; public callers get CarrierDisk or CarrierDiskUnavailable, never inline canon material
#   owner: Erin Spencer
#   public_surface: ThetaMicrokernel, get_carrier_disk, carrier_disk_signature_only
#   internal_surface: _CANON_DISK_CACHE, _PUBLIC_FALLBACK_ENABLED
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.theta_carrier_disk_access_holds
#   rollout: default_enabled
#   rollback: detach callers
#   doctrine: per user spec — disk is canonical point zero; lives in Θ; bounded drift via fiq motion canon
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: theta_microkernel_boundaries
#   summary: Θ microkernel — hosts the canon carrier disk via private loader; public callers get CarrierDisk or CarrierDiskUnavailable, never inline canon material
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: theta_microkernel
#   summary: Θ microkernel — hosts the canon carrier disk via private loader; public callers get CarrierDisk or CarrierDiskUnavailable, never inline canon material
#   exposes: ThetaMicrokernel, get_carrier_disk, carrier_disk_signature_only
#   boundaries: auth:none, storage:read, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: theta_carrier_disk_access
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.theta_carrier_disk_access_holds
# === END CONTRACTS ===
"""Θ microkernel — hosts the canon carrier disk.

Public callers obtain a CarrierDisk through this microkernel. The
microkernel attempts to load the canon disk via the private loader;
if `A0P_CARRIER_DISK_PATH` is unset and `A0P_ALLOW_PUBLIC_FIXTURE` is
truthy, it degrades to the public fixture. Otherwise it raises.

Public callers must never assume canon. Always check `disk.signature().is_canon`.
"""
from __future__ import annotations
import os
from typing import Optional

from ..gonal.disk_protocol import CarrierDisk, CarrierDiskUnavailable
from ..gonal.public_fixture import build_public_fixture_disk
from ._theta_private_loader import load_canon_disk


_CANON_DISK_CACHE: Optional[CarrierDisk] = None
_PUBLIC_FALLBACK_ENV: str = "A0P_ALLOW_PUBLIC_FIXTURE"


class ThetaMicrokernel:
    """The Θ microkernel — single point of carrier-disk access."""

    def __init__(self, *, allow_public_fixture: bool | None = None):
        """`allow_public_fixture=None` consults the env var; otherwise overrides."""
        if allow_public_fixture is None:
            allow_public_fixture = (
                os.environ.get(_PUBLIC_FALLBACK_ENV, "").lower() in ("1", "true", "yes")
            )
        self._allow_public_fixture = bool(allow_public_fixture)
        self._disk: Optional[CarrierDisk] = None

    def carrier_disk(self) -> CarrierDisk:
        """Return the active CarrierDisk. Canon if configured; public fixture if allowed; else raise."""
        if self._disk is not None:
            return self._disk
        try:
            self._disk = load_canon_disk()
            return self._disk
        except CarrierDiskUnavailable:
            if not self._allow_public_fixture:
                raise
            self._disk = build_public_fixture_disk()
            return self._disk

    def is_canon(self) -> bool:
        try:
            return self.carrier_disk().signature().is_canon
        except CarrierDiskUnavailable:
            return False


def get_carrier_disk() -> CarrierDisk:
    """Module-level convenience — uses a shared microkernel instance."""
    global _CANON_DISK_CACHE
    if _CANON_DISK_CACHE is not None:
        return _CANON_DISK_CACHE
    mk = ThetaMicrokernel()
    _CANON_DISK_CACHE = mk.carrier_disk()
    return _CANON_DISK_CACHE


def carrier_disk_signature_only() -> dict:
    """Return ONLY the public signature (counts + is_canon). No positions."""
    try:
        disk = get_carrier_disk()
        sig = disk.signature()
        return {
            "arity": sig.arity,
            "l_count": sig.l_count,
            "n_count": sig.n_count,
            "p_count": sig.p_count,
            "x_count": sig.x_count,
            "is_canon": sig.is_canon,
        }
    except CarrierDiskUnavailable as e:
        return {"error": str(e), "available": False}
# ratios: loc_comments=53:54 imports_exports=6:3 calls_definitions=11:6
