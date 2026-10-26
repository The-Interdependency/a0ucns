# ratios: loc_comments=30:45 imports_exports=4:1 calls_definitions=6:5
# === MODULE_BUILD ===
# id: ptca_instance
#   module_name: instance
#   module_kind: engine
#   summary: PTCA engine — binds the canon stratified [N,7,7,53] PrimeTensor with sentinel channels + lineage hashing
#   owner: a0p maintainer
#   public_surface: PTCAInstance
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: ptca_instance_boundaries
#   summary: PTCA engine — binds the canon stratified [N,7,7,53] PrimeTensor with sentinel channels + lineage hashing
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: ptca_instance
#   summary: PTCA engine — binds the canon stratified [N,7,7,53] PrimeTensor with sentinel channels + lineage hashing
#   exposes: PTCAInstance
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""PTCAInstance — the main engine class binding tensor + sentinels + provenance.

The instance carries N prime nodes; the standard research seed is N=157
(used by the three PTCA cores configured by PCNA: phi / psi / omega).
"""
from __future__ import annotations
from .tensor import PrimeTensor
from .sentinels import SentinelChannel
from .provenance import hash_state


class PTCAInstance:
    def __init__(self, n_primes: int = 157, label: str = "phi", seed: int = 0):
        self.label = label
        self.tensor = PrimeTensor(n_primes)
        if seed:
            self.tensor.seed_from_int(seed)
        self.channels: dict[str, SentinelChannel] = {}
        self.lineage: list[str] = []

    def register(self, channel: SentinelChannel) -> None:
        self.channels[channel.name] = channel

    def push(self, channel_name: str, payload: dict) -> str:
        if channel_name not in self.channels:
            self.channels[channel_name] = SentinelChannel(name=channel_name)
        msg = self.channels[channel_name].push(payload)
        h = hash_state({"ch": channel_name, "seq": msg.seq, "p": payload},
                       op="push", parents=self.lineage[-1:])
        self.lineage.append(h)
        return h

    def snapshot(self) -> dict:
        return {
            "label": self.label,
            "tensor": self.tensor.summary(),
            "channels": {k: len(v) for k, v in self.channels.items()},
            "lineage_head": self.lineage[-1] if self.lineage else None,
            "lineage_depth": len(self.lineage),
        }

# === CONTRACTS ===
# id: ptca_instance_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=30:45 imports_exports=4:1 calls_definitions=6:5
