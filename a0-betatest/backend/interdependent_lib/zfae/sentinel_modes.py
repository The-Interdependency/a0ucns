# ratios: loc_comments=43:54 imports_exports=2:4 calls_definitions=10:3
# === MODULE_BUILD ===
# id: zfae_sentinel_modes
#   module_name: sentinel_modes
#   module_kind: schema
#   summary: per-agent sentinel mode resolution — observe/flag/off — with canonical defaults (7 flag + 6 observe + 0 off; flags = S1 S2 S3 S4 S8 S9 S12)
#   owner: Erin Spencer
#   public_surface: SENTINEL_MODES_DEFAULT, validate_modes, resolve_modes, bulk_set
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.sentinel_modes_default_holds
#   rollout: default_enabled
#   rollback: revert file; all sentinels treated as flag
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_sentinel_modes_boundaries
#   summary: pure validation + merge; no IO
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_sentinel_modes
#   summary: defaults + per-agent override + bulk transitions for sentinel modes
#   exposes: SENTINEL_MODES_DEFAULT, validate_modes, resolve_modes, bulk_set
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
"""Per-agent sentinel-mode defaults and resolution.

Defaults (7 flag + 6 observe + 0 off):
  flag    S1 S2 S3 S4 S8 S9 S12
  observe S5 S6 S7 S10 S11 S13

hmmm: the dict below is canon; the previous "6 flag + 7 observe" label was a
docstring drift bug (now corrected). The alternative reading — drop S3 to
observe so the count actually equals 6 flag — is a behavioural change that
needs Erin's ratification and is NOT applied here. Flag for review;
do not silently rebalance.
"""
from __future__ import annotations
from .sentinels import SentinelMode, all_names


SENTINEL_MODES_DEFAULT: dict[str, SentinelMode] = {
    "S1":  SentinelMode.FLAG,
    "S2":  SentinelMode.FLAG,
    "S3":  SentinelMode.FLAG,
    "S4":  SentinelMode.FLAG,
    "S5":  SentinelMode.OBSERVE,
    "S6":  SentinelMode.OBSERVE,
    "S7":  SentinelMode.OBSERVE,
    "S8":  SentinelMode.FLAG,
    "S9":  SentinelMode.FLAG,
    "S10": SentinelMode.OBSERVE,
    "S11": SentinelMode.OBSERVE,
    "S12": SentinelMode.FLAG,
    "S13": SentinelMode.OBSERVE,
}


def validate_modes(modes: dict[str, str]) -> dict[str, SentinelMode]:
    """Coerce string values to SentinelMode; reject unknown keys/values."""
    valid_keys = set(all_names())
    out: dict[str, SentinelMode] = {}
    for k, v in modes.items():
        if k not in valid_keys:
            raise ValueError(f"unknown sentinel name {k!r}; expected one of S1..S13")
        try:
            out[k] = SentinelMode(v)
        except ValueError:
            raise ValueError(f"sentinel {k}: mode {v!r} not in {[m.value for m in SentinelMode]}")
    return out


def resolve_modes(agent_modes: dict[str, str] | None) -> dict[str, SentinelMode]:
    """Merge defaults with agent's partial override. Missing keys keep defaults."""
    resolved = dict(SENTINEL_MODES_DEFAULT)
    if agent_modes:
        resolved.update(validate_modes(agent_modes))
    return resolved


def bulk_set(mode: str) -> dict[str, SentinelMode]:
    """Set ALL 13 sentinels to one mode."""
    try:
        m = SentinelMode(mode)
    except ValueError:
        raise ValueError(f"bulk mode {mode!r} not in {[m.value for m in SentinelMode]}")
    return {name: m for name in all_names()}


__all__ = [
    "SENTINEL_MODES_DEFAULT",
    "validate_modes", "resolve_modes", "bulk_set",
]

# === CONTRACTS ===
# id: zfae_sentinel_modes_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===

# ratios: loc_comments=43:54 imports_exports=2:4 calls_definitions=10:3
