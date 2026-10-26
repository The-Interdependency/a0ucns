# ratios: loc_comments=55:48 imports_exports=6:5 calls_definitions=8:11
# === MODULE_BUILD ===
# id: fiq_events
#   module_name: events
#   module_kind: schema
#   summary: FIQ_TRANSFER / FIQ_BUFFERED / FIQ_BLOCKED event dataclasses; blake2b prev_hash chain
#   owner: Erin Spencer
#   public_surface: FIQ_TRANSFER, FIQ_BUFFERED, FIQ_BLOCKED, AuditEvent, chain_hash, verify_chain
#   internal_surface: _digest
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.fiq_audit_chain_appends_holds
#   rollout: default_enabled
#   rollback: revert file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: fiq_events_boundaries
#   summary: FIQ_TRANSFER / FIQ_BUFFERED / FIQ_BLOCKED event dataclasses; blake2b prev_hash chain
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: fiq_events
#   summary: FIQ_TRANSFER / FIQ_BUFFERED / FIQ_BLOCKED event dataclasses; blake2b prev_hash chain
#   exposes: FIQ_TRANSFER, FIQ_BUFFERED, FIQ_BLOCKED, AuditEvent, chain_hash, verify_chain
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: fiq_audit_chain_appends
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.fiq_audit_chain_appends_holds
# === END CONTRACTS ===
"""Fiq event dataclasses + audit-chain hash helper."""
from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Union


def _digest(payload: dict, prev_hash: str) -> str:
    # Exclude `this_hash` from the digest input — otherwise the hash includes itself (circular).
    payload = {k: v for k, v in payload.items() if k != "this_hash"}
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.blake2b(prev_hash.encode("utf-8") + blob, digest_size=16).hexdigest()


@dataclass
class _BaseEvent:
    event_type: str
    gate_a: str
    gate_b: str
    support: str
    tick_ms: int
    prev_hash: str = "0" * 32
    this_hash: str = ""
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    payload: dict = field(default_factory=dict)

    def seal(self) -> "_BaseEvent":
        self.this_hash = _digest(asdict(self), self.prev_hash)
        return self


@dataclass
class FIQ_TRANSFER(_BaseEvent):
    """Audited motion completed: source emitted, target absorbed."""
    flux: float = 0.0

    def __post_init__(self):
        self.event_type = "FIQ_TRANSFER"


@dataclass
class FIQ_BUFFERED(_BaseEvent):
    """Source emitted but target attention did not fire; queued."""
    buffer_expires_ms: int = 0

    def __post_init__(self):
        self.event_type = "FIQ_BUFFERED"


@dataclass
class FIQ_BLOCKED(_BaseEvent):
    """Gate refused — one of the χ indicators returned 0."""
    reason: str = ""
    failing_indicator: str = ""   # 'route' | 'audit' | 'support' | 'attention' | other

    def __post_init__(self):
        self.event_type = "FIQ_BLOCKED"


AuditEvent = Union[FIQ_TRANSFER, FIQ_BUFFERED, FIQ_BLOCKED]


def chain_hash(event: AuditEvent, prev_hash: str) -> str:
    """Compute the blake2b prev-hash chain digest for `event`."""
    return _digest(asdict(event), prev_hash)


def verify_chain(events: list[AuditEvent]) -> bool:
    """True iff every event's prev_hash matches the previous event's this_hash."""
    if not events:
        return True
    prev = "0" * 32
    for ev in events:
        if ev.prev_hash != prev:
            return False
        expected = chain_hash(ev, prev)
        if ev.this_hash != expected:
            return False
        prev = ev.this_hash
    return True
# ratios: loc_comments=55:48 imports_exports=6:5 calls_definitions=8:11
