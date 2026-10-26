# ratios: loc_comments=50:51 imports_exports=7:5 calls_definitions=19:4
# === MODULE_BUILD ===
# id: carrier_registry
#   module_name: registry
#   module_kind: service
#   summary: three-gonal registry — default (EXAMPLE_157), mirror (mirror_of default), private (per-agent built via build_gonal from spec); resolves an agent's per-core gonal triplet
#   owner: Erin Spencer
#   public_surface: GonalName, get_default, get_mirror, get_private, get_gonal, GONAL_NAMES, PRIVATE_GONAL_SPEC_ENV
#   internal_surface: _DEFAULT_CACHE, _MIRROR_CACHE
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.carrier_registry_three_gonals_holds
#   rollout: default_enabled
#   rollback: revert file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: carrier_registry_boundaries
#   summary: reads gonal spec from env path for private; default and mirror are public
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: carrier_registry
#   summary: per-agent three-gonal triplet resolver — phi/default, psi/mirror, omega/private
#   exposes: GonalName, get_default, get_mirror, get_private, get_gonal
#   boundaries: auth:none, storage:read, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
"""Three-gonal registry.

Per the user-pinned canon:
  phi   core → default gonal  (EXAMPLE_157)
  psi   core → mirror gonal   (mirror_of(EXAMPLE_157))
  omega core → private gonal  (per-agent, built from A0P_GONAL_SPEC_PATH or per-agent spec)
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Literal, Optional

from .gonal import GonalSpec, build_gonal, validate_gonal, EXAMPLE_157
from .mirror import mirror_of


GonalName = Literal["default", "mirror", "private"]
GONAL_NAMES: tuple[GonalName, ...] = ("default", "mirror", "private")

PRIVATE_GONAL_SPEC_ENV: str = "A0P_GONAL_SPEC_PATH"

_DEFAULT_CACHE: Optional[list[str]] = None
_MIRROR_CACHE: Optional[list[str]] = None


def get_default() -> list[str]:
    """The public default arrangement (EXAMPLE_157)."""
    global _DEFAULT_CACHE
    if _DEFAULT_CACHE is None:
        _DEFAULT_CACHE = list(EXAMPLE_157)
    return list(_DEFAULT_CACHE)


def get_mirror() -> list[str]:
    """The public mirror of the default (position-reflection)."""
    global _MIRROR_CACHE
    if _MIRROR_CACHE is None:
        _MIRROR_CACHE = mirror_of(get_default())
    return list(_MIRROR_CACHE)


def get_private(spec_path: Optional[str] = None) -> list[str]:
    """Build the private gonal from a JSON spec file. Raises if no path or invalid."""
    path = spec_path or os.environ.get(PRIVATE_GONAL_SPEC_ENV)
    if not path:
        raise FileNotFoundError(
            f"private gonal requested but {PRIVATE_GONAL_SPEC_ENV} not set"
        )
    p = Path(path).expanduser()
    if not p.is_file():
        raise FileNotFoundError(f"private gonal spec not found at {p}")
    spec_data = json.loads(p.read_text(encoding="utf-8"))
    spec = GonalSpec(**spec_data)
    arrangement = build_gonal(spec)
    report = validate_gonal(arrangement, spec)
    if not report["valid"]:
        raise ValueError(f"private gonal spec invalid: {report['violations']}")
    return arrangement


def get_gonal(name: GonalName, private_spec_path: Optional[str] = None) -> list[str]:
    """Resolve a gonal by name. `private` requires a spec path (env or arg)."""
    if name == "default":
        return get_default()
    if name == "mirror":
        return get_mirror()
    if name == "private":
        return get_private(private_spec_path)
    raise ValueError(f"unknown gonal name {name!r}; expected one of {GONAL_NAMES}")


__all__ = [
    "GonalName", "GONAL_NAMES", "PRIVATE_GONAL_SPEC_ENV",
    "get_default", "get_mirror", "get_private", "get_gonal",
]

# === CONTRACTS ===
# id: carrier_registry_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===

# ratios: loc_comments=50:51 imports_exports=7:5 calls_definitions=19:4
