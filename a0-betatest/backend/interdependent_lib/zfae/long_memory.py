# ratios: loc_comments=25:52 imports_exports=4:3 calls_definitions=5:2
# === MODULE_BUILD ===
# id: zfae_long_memory
#   module_name: long_memory
#   module_kind: service
#   summary: a0 long-term memory canon — folds the repo's living spec (every MODULE_BUILD block) into a cached deterministic summary the ZFAE engine carries on every inference, so the agent "queries itself"
#   owner: Erin Spencer
#   public_surface: canon_summary, reset_cache
#   internal_surface: _CANON_CACHE
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.module_imports_cleanly_holds
#   rollout: default_enabled
#   rollback: revert file; engine carries an empty canon
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_long_memory_boundaries
#   summary: reads the living spec once and caches a deterministic digest; no writes, no network
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_long_memory
#   summary: cached living-spec canon summary for ZFAE long-term memory
#   exposes: canon_summary, reset_cache
#   boundaries: auth:none, storage:read, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_long_memory_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
"""a0 long-term memory canon.

The living spec (every ``MODULE_BUILD`` block in the repo) IS the agent's
self-description. This module folds that spec into a small, cached, JSON-safe
summary — ``{module_count, canon_digest, source}`` — that the ZFAE engine
attaches to every inference's ``state["memory_long_canon"]``. The canon digest
feeds the Gonal Inscription entropy, so the agent's output is conditioned on
its own current definition: it queries itself.

The scan is computed once and cached (deterministic for a given repo state).
"""
from __future__ import annotations
import hashlib
from typing import Optional

_CANON_CACHE: Optional[dict] = None


def canon_summary() -> dict:
    """Return the cached living-spec canon summary. Deterministic per repo state."""
    global _CANON_CACHE
    if _CANON_CACHE is not None:
        return dict(_CANON_CACHE)
    try:
        from living_spec import scan_repo_blocks  # type: ignore
        mods = scan_repo_blocks()
        names = sorted(str(m.get("module_name", "")) for m in mods)
        digest = hashlib.blake2b("|".join(names).encode("utf-8"), digest_size=16).hexdigest()
        _CANON_CACHE = {
            "module_count": len(mods),
            "canon_digest": digest,
            "source": "living_spec",
        }
    except Exception:
        _CANON_CACHE = {"module_count": 0, "canon_digest": "0" * 32, "source": "unavailable"}
    return dict(_CANON_CACHE)


def reset_cache() -> None:
    """Drop the cached canon (e.g. after a hot-reload during development)."""
    global _CANON_CACHE
    _CANON_CACHE = None


__all__ = ["canon_summary", "reset_cache"]
# ratios: loc_comments=25:52 imports_exports=4:3 calls_definitions=5:2
