# ratios: loc_comments=49:100 imports_exports=4:5 calls_definitions=26:6
# === MODULE_BUILD ===
# id: pcea_kernel
#   module_name: kernel
#   module_kind: engine
#   summary: PCEA cross-cut — "this state, last state" kernel runtime encryption operating on Tensor payloads at any layer of the layered model
#   owner: a0p maintainer
#   public_surface: kernel_step, kernel_invert, kernel_chain, grid_project, QUANT_SCALE, QUANT_OFFSET
#   internal_surface: _quantize, _dequantize
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.pcea_kernel_round_trip_holds
#   rollout: default_enabled
#   rollback: revert file from git
#   boundary_contract: PCEA inverts via keys (last_state), not via UCNS inverse operations — synced from upstream PCEA repo
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: pcea_kernel_boundaries
#   summary: PCEA cross-cut — "this state, last state" kernel runtime encryption operating on Tensor payloads at any layer of the layered model
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: pcea_kernel
#   summary: PCEA cross-cut — "this state, last state" kernel runtime encryption operating on Tensor payloads at any layer of the layered model
#   exposes: kernel_step, kernel_invert, kernel_chain, grid_project, QUANT_SCALE, QUANT_OFFSET
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""PCEA kernel cross-cut.

Per the upstream PCEA boundary contract:
    "PCEA decrypt/invert via keys, not via UCNS inverse operations."
    "Security rests on key management (last_state synchronization),
     not on any assumption that arithmetic inversion is hard."

This module bridges PCEA's integer-sequence cipher to the float-tensor
layered model (PCNA → PCTA → PTCA → Core). Any layer can call
`kernel_step(this, last)` to encrypt a state-Tensor against the prior
state-Tensor. `kernel_invert` recovers the original IFF the caller
supplies the same `last` Tensor — i.e. holds the key.

Quantisation is bit-exact (SCALE=2^28, OFFSET=2^29) so the float
Tensor ↔ integer state round-trip is lossless within our payload
range. Encrypted Tensors may have payload values outside the
deterministic constructor's [-0.5, +0.5] range — that's expected.
"""
from __future__ import annotations
from typing import Sequence

from .cipher import encrypt_state, decrypt_state
from ..pcna.tensor import Tensor, TENSOR_DIM

# === CONTRACTS ===
# id: pcea_kernel_round_trip
#   given: kernel_step(t, prev) then kernel_invert(enc, prev) using the same `prev`
#   then: the recovered Tensor equals the original t exactly
#   class: correctness
#   call: a0p_skills.contracts.pcea_kernel_round_trip_holds
# === END CONTRACTS ===

# === CONTRACTS ===
# id: pcea_kernel_advances_state
#   given: kernel_step(t, prev1) and kernel_step(t, prev2) for prev1 != prev2
#   then: the two encrypted Tensors differ — last_state keying is real
#   class: correctness
#   call: a0p_skills.contracts.pcea_kernel_advances_state_holds
# === END CONTRACTS ===

# === CONTRACTS ===
# id: pcea_kernel_layer_cross_cut
#   given: kernel_step applied to aggregates from PCTA Circle, PTCA Seed, PTCA Core
#   then: each layer's aggregate round-trips through kernel_step / kernel_invert
#   class: correctness
#   call: a0p_skills.contracts.pcea_kernel_layer_cross_cut_holds
# === END CONTRACTS ===


# Quantisation parameters — chosen so:
#   - all positions stay non-negative (PCEA requires this)
#   - SCALE × max_payload + OFFSET < 2^30 (well inside double-precision mantissa)
#   - round-trip is bit-exact for Tensors already on the 1/SCALE grid
QUANT_SCALE: int = 1 << 28   # 268_435_456
QUANT_OFFSET: int = 1 << 29  # 536_870_912


def _quantize(t: Tensor) -> list[int]:
    """Map a Tensor's float payload to non-negative integers for PCEA."""
    return [round(v * QUANT_SCALE) + QUANT_OFFSET for v in t.payload]


def _dequantize(ints: Sequence[int]) -> Tensor:
    """Inverse of _quantize. Bit-exact within the int range we use."""
    if len(ints) != TENSOR_DIM:
        raise ValueError(
            f"_dequantize requires a width-{TENSOR_DIM} sequence; got {len(ints)}"
        )
    return Tensor([(i - QUANT_OFFSET) / QUANT_SCALE for i in ints])


def grid_project(t: Tensor) -> Tensor:
    """Project a Tensor onto the 1/QUANT_SCALE quantisation grid.

    Idempotent: `grid_project(grid_project(t)) == grid_project(t)`.

    `kernel_step` and `kernel_invert` operate on the grid. The round-trip
    `kernel_invert(kernel_step(t, prev), prev) == grid_project(t)` holds
    bit-exactly; the recovered Tensor equals the original IFF the
    original was already on the grid.

    This is a deliberate consequence of PCEA being an integer cipher:
    the float bridge has finite precision, currently 2^-28 ~ 3.73e-9.
    """
    return _dequantize(_quantize(t))


def kernel_step(this_t: Tensor, last_t: Tensor) -> Tensor:
    """PCEA encrypt — produce an encrypted-state Tensor keyed against `last_t`.

    Pure function. No global state. `last_t` is the entire key — losing
    `last_t` means kernel_invert cannot recover the original.
    """
    if not isinstance(this_t, Tensor) or not isinstance(last_t, Tensor):
        raise TypeError("kernel_step requires Tensor inputs")
    this_ints = _quantize(this_t)
    last_ints = _quantize(last_t)
    enc = encrypt_state(this_ints, last_ints)
    return _dequantize(enc)


def kernel_invert(enc_t: Tensor, last_t: Tensor) -> Tensor:
    """PCEA decrypt — recover the original Tensor given the same `last_t`.

    Per the PCEA boundary contract: inversion is via the key (`last_t`),
    not via UCNS inverse operations.
    """
    if not isinstance(enc_t, Tensor) or not isinstance(last_t, Tensor):
        raise TypeError("kernel_invert requires Tensor inputs")
    enc_ints = _quantize(enc_t)
    last_ints = _quantize(last_t)
    dec = decrypt_state(enc_ints, last_ints)
    return _dequantize(dec)


def kernel_chain(states: Sequence[Tensor], initial_last: Tensor) -> list[Tensor]:
    """Encrypt a state sequence — each step keyed against the prior plaintext.

    This is the "runtime" pattern: at each network heartbeat tick, the
    new state is encrypted against the immediately-prior plaintext
    state. The returned list is the ciphertext sequence; replaying
    requires the original plaintext sequence (the keys).
    """
    if not isinstance(initial_last, Tensor):
        raise TypeError("initial_last must be a Tensor")
    out: list[Tensor] = []
    last = initial_last
    for s in states:
        if not isinstance(s, Tensor):
            raise TypeError(f"states must be Tensors; got {type(s).__name__}")
        out.append(kernel_step(s, last))
        last = s
    return out


__all__ = [
    "QUANT_SCALE",
    "QUANT_OFFSET",
    "grid_project",
    "kernel_step",
    "kernel_invert",
    "kernel_chain",
]
# ratios: loc_comments=49:100 imports_exports=4:5 calls_definitions=26:6
