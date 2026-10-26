# 19:13
"""UCNS-kit protocol interfaces. No implementations — frame-independent contracts."""
from __future__ import annotations
from typing import Protocol, Iterable


class RingState(Protocol):
    """A ring of N coherence-prime nodes.

    Frame-bound implementations decide what a 'node' is.
    hmmm: Frame A = UCNS cell per node; Frame B = entire ring as one
          UCNSObject; Frame C = parallel tensor + UCNS audit.
          Frame choice is upstream of this interface.
    """

    n: int

    def inject(self, signal) -> None: ...

    def nodes(self) -> Iterable: ...

    def apply_rule(self, rule: "PropagationRule") -> None: ...

    def serialize(self) -> bytes: ...

    @classmethod
    def restore(cls, data: bytes) -> "RingState": ...


class PropagationRule(Protocol):
    def apply(self, node, neighbors) -> object:
        pass


class CoherenceMeasure(Protocol):
    def measure(self, ring: RingState) -> float:
        pass


class RewardMechanism(Protocol):
    """Apply a reward signal to a ring state.

    hmmm: R1 = bandit-over-UCNS-arms; R2 = discrete anchor promotion
          (invalid with Frame C — no anchors in primary state);
          R3 = separate numerical control plane.
          Mechanism choice is upstream of this interface.
    """

    def apply_reward(self, state, outcome: float) -> None:
        pass


class Serializer(Protocol):
    def to_bytes(self, state) -> bytes:
        pass

    def from_bytes(self, data: bytes):
        pass
# 19:13
