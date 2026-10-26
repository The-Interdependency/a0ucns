# ratios: loc_comments=33:42 imports_exports=3:1 calls_definitions=10:8
# === MODULE_BUILD ===
# id: pcna_memory_core
#   module_name: memory_core
#   module_kind: engine
#   summary: dual prime-ring memory — LT N=19, ST N=17, plus volatile sub-agent caches
#   owner: a0p maintainer
#   public_surface: MemoryCore
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: pcna_memory_core_boundaries
#   summary: dual prime-ring memory — LT N=19, ST N=17, plus volatile sub-agent caches
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: pcna_memory_core
#   summary: dual prime-ring memory — LT N=19, ST N=17, plus volatile sub-agent caches
#   exposes: MemoryCore
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""MemoryCore — persistent activation state, two prime rings (N=19 LT, N=17 ST)."""
from __future__ import annotations
from collections import deque
from ..ptca.primes import first_n_primes


class MemoryCore:
    def __init__(self):
        self.lt_primes = first_n_primes(19)  # long-term ring
        self.st_primes = first_n_primes(17)  # short-term ring
        self.lt: deque = deque(maxlen=19)
        self.st: deque = deque(maxlen=17)
        self.sub: dict[str, list[str]] = {}

    def push_lt(self, item: str) -> None:
        self.lt.append(item)

    def push_st(self, item: str) -> None:
        self.st.append(item)

    def spawn_sub(self, sub_id: str) -> None:
        self.sub[sub_id] = []

    def push_sub(self, sub_id: str, item: str) -> None:
        if sub_id not in self.sub:
            self.spawn_sub(sub_id)
        self.sub[sub_id].append(item)

    def merge_sub(self, sub_id: str) -> list[str]:
        items = self.sub.pop(sub_id, [])
        for it in items:
            self.push_st(it)
        return items

    def snapshot(self) -> dict:
        return {
            "lt": list(self.lt),
            "st": list(self.st),
            "sub_keys": list(self.sub.keys()),
            "lt_capacity": self.lt.maxlen,
            "st_capacity": self.st.maxlen,
        }

# === CONTRACTS ===
# id: pcna_memory_core_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=33:42 imports_exports=3:1 calls_definitions=10:8
