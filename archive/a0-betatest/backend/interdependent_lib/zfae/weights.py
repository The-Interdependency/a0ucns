# ratios: loc_comments=194:87 imports_exports=8:2 calls_definitions=71:25
# === MODULE_BUILD ===
# id: zfae_weight_bank
#   module_name: weights
#   module_kind: engine
#   summary: A0ZFAEWeightBank — three-core (phi, psi, omega) safetensors load/save, per-core checkpoint digest, training-step counter, seeds-touched tracking; exposes canonical 1_223_187 scalar count
#   owner: Erin Spencer
#   public_surface: A0ZFAEWeightBank, WEIGHT_SHAPE, WEIGHT_COUNT, WEIGHT_COUNT_PER_CORE, WEIGHT_COUNT_TOTAL, CORE_NAMES
#   internal_surface: _compute_digest, _coerce_metadata
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: write
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_weight_bank_loads_407729_holds, a0p_skills.contracts.zfae_weight_bank_three_core_total_holds
#   rollout: default_enabled
#   rollback: rebuild from seed_init; lose training progress
#   canon_metrics: zfae_weight_count, zfae_weight_count_total, zfae_checkpoint_digest, zfae_training_step, zfae_last_loss, zfae_seeds_touched
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_weight_bank_boundaries
#   summary: three-core (phi, psi, omega) safetensors load/save with per-core checkpoint digest
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: write
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_weight_bank
#   summary: three-core (phi, psi, omega) safetensors load/save with per-core checkpoint digest
#   exposes: A0ZFAEWeightBank, WEIGHT_SHAPE, WEIGHT_COUNT, WEIGHT_COUNT_PER_CORE, WEIGHT_COUNT_TOTAL, CORE_NAMES
#   boundaries: auth:none, storage:write, network:none, user_data:write
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_weight_bank_loads_407729
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_weight_bank_loads_407729_holds
# === END CONTRACTS ===

# === CONTRACTS ===
# id: zfae_weight_bank_three_core_total
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_weight_bank_three_core_total_holds
# === END CONTRACTS ===

# === CONTRACTS ===
# id: zfae_weight_bank_persists_gonal_seed
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_weight_bank_persists_gonal_seed_holds
# === END CONTRACTS ===
"""A0ZFAEWeightBank — persistent three-core (phi, psi, omega) weight bank.

Each core is a (157, 53, 7, 7) ndarray. The bank's total scalar count is
1,223,187 = 3 × 407,729. Cores are checkpoint-digested independently; the
combined digest is the blake2b of phi||psi||omega bytes.

Seeds touched per core are tracked in metadata via integer bitsets stored
as JSON arrays of touched seed indices (0..156).
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Optional

import numpy as np
from safetensors.numpy import load_file, save_file

from .weight_init import (
    WEIGHT_SHAPE,
    WEIGHT_COUNT,
    WEIGHT_COUNT_PER_CORE,
    WEIGHT_COUNT_TOTAL,
    CORE_NAMES,
    GONAL_SEED_WIDTH,
    seed_initial_three_core,
    seed_initial_gonal,
    default_metadata,
)


def _compute_digest(weights: np.ndarray) -> str:
    """blake2b digest of weight bytes — checkpoint integrity."""
    return hashlib.blake2b(weights.tobytes(), digest_size=16).hexdigest()


def _coerce_metadata(meta: dict | None, agent_id: str) -> dict[str, str]:
    """safetensors metadata must be str→str; coerce all values."""
    m = dict(meta or default_metadata(agent_id))
    return {str(k): str(v) for k, v in m.items()}


class A0ZFAEWeightBank:
    """Per-agent ZFAE three-core weight bank with safetensors persistence."""

    def __init__(
        self,
        agent_id: str,
        cores: dict[str, np.ndarray] | None = None,
        metadata: dict[str, str] | None = None,
        last_loss: float | None = None,
        gonal_seed: np.ndarray | None = None,
    ):
        self.agent_id = agent_id
        if cores is None:
            cores = seed_initial_three_core(agent_id)
        if set(cores.keys()) != set(CORE_NAMES):
            raise ValueError(
                f"cores keys {sorted(cores.keys())} != canon {list(CORE_NAMES)}"
            )
        coerced: dict[str, np.ndarray] = {}
        for name in CORE_NAMES:
            arr = cores[name]
            if arr.shape != WEIGHT_SHAPE:
                raise ValueError(
                    f"core {name!r} shape {arr.shape} != canon {WEIGHT_SHAPE}"
                )
            if arr.size != WEIGHT_COUNT_PER_CORE:
                raise ValueError(
                    f"core {name!r} size {arr.size} != canon {WEIGHT_COUNT_PER_CORE}"
                )
            coerced[name] = arr.astype(np.float32, copy=False)
        self._cores: dict[str, np.ndarray] = coerced
        self._metadata: dict[str, str] = _coerce_metadata(metadata, agent_id)
        # 4th persisted tensor — private-gonal seed (Route A inscription entropy).
        if gonal_seed is None:
            gonal_seed = seed_initial_gonal(agent_id)
        gs = np.asarray(gonal_seed, dtype=np.float32).reshape(-1)
        if gs.size != GONAL_SEED_WIDTH:
            gs = seed_initial_gonal(agent_id)
        self._gonal_seed: np.ndarray = gs.astype(np.float32, copy=False)
        self._last_loss: float | None = (
            None if last_loss is None or not (last_loss == last_loss and last_loss != float("inf") and last_loss != float("-inf"))
            else float(last_loss)
        )

    # ---- canonical metric accessors -----------------------------------------
    @property
    def zfae_weight_count(self) -> int:
        """Total scalar count across all three cores (1_223_187)."""
        return int(sum(c.size for c in self._cores.values()))

    @property
    def zfae_weight_count_per_core(self) -> int:
        return WEIGHT_COUNT_PER_CORE

    @property
    def zfae_weight_count_total(self) -> int:
        return self.zfae_weight_count

    @property
    def zfae_checkpoint_digest(self) -> str:
        """Combined digest over phi||psi||omega."""
        h = hashlib.blake2b(digest_size=16)
        for name in CORE_NAMES:
            h.update(self._cores[name].tobytes())
        return h.hexdigest()

    def zfae_core_digest(self, core: str) -> str:
        if core not in CORE_NAMES:
            raise ValueError(f"unknown core {core!r}; expected one of {CORE_NAMES}")
        return _compute_digest(self._cores[core])

    @property
    def zfae_training_step(self) -> int:
        return int(self._metadata.get("training_step", "0"))

    @property
    def zfae_last_loss(self) -> float | None:
        return self._last_loss

    @property
    def weights(self) -> np.ndarray:
        """Phi core only — back-compat property for legacy callers."""
        return self._cores["phi"]

    def core(self, name: str) -> np.ndarray:
        if name not in CORE_NAMES:
            raise ValueError(f"unknown core {name!r}; expected one of {CORE_NAMES}")
        return self._cores[name]

    @property
    def cores(self) -> dict[str, np.ndarray]:
        return dict(self._cores)

    @property
    def gonal_seed(self) -> np.ndarray:
        """The per-agent private-gonal seed vector (width 53)."""
        return self._gonal_seed

    @property
    def gonal_seed_bytes(self) -> bytes:
        """Raw bytes of the private-gonal seed — passed to PrivateGonal.from_seed."""
        return self._gonal_seed.tobytes()

    @property
    def metadata(self) -> dict[str, str]:
        return dict(self._metadata)

    def seeds_touched(self, core: str) -> set[int]:
        if core not in CORE_NAMES:
            raise ValueError(f"unknown core {core!r}; expected one of {CORE_NAMES}")
        try:
            arr = json.loads(self._metadata.get(f"seeds_touched_{core}_idx", "[]"))
            return set(int(i) for i in arr)
        except (json.JSONDecodeError, ValueError, TypeError):
            return set()

    @property
    def total_seeds_touched(self) -> int:
        return sum(len(self.seeds_touched(c)) for c in CORE_NAMES)

    @property
    def all_seeds_touched(self) -> bool:
        """True iff every (core, seed) pair has been touched (157 × 3 = 471)."""
        return all(len(self.seeds_touched(c)) == WEIGHT_SHAPE[0] for c in CORE_NAMES)

    # ---- mutation ----------------------------------------------------------
    def apply_update(self, delta: np.ndarray, loss: float, core: str = "phi") -> str:
        """Add `delta` to `core` weights, bump training_step, update last_loss; return new combined digest."""
        if core not in CORE_NAMES:
            raise ValueError(f"unknown core {core!r}; expected one of {CORE_NAMES}")
        if delta.shape != WEIGHT_SHAPE:
            raise ValueError(f"delta shape {delta.shape} != {WEIGHT_SHAPE}")
        self._cores[core] = (self._cores[core] + delta.astype(np.float32, copy=False)).astype(np.float32)
        step = self.zfae_training_step + 1
        self._metadata["training_step"] = str(step)
        self._last_loss = float(loss)
        # Update seeds_touched for nonzero rows in delta
        touched_now = self.seeds_touched(core)
        for s in range(WEIGHT_SHAPE[0]):
            if np.any(delta[s] != 0):
                touched_now.add(s)
        self._metadata[f"seeds_touched_{core}_idx"] = json.dumps(sorted(touched_now))
        self._metadata[f"seeds_touched_{core}"] = str(len(touched_now))
        return self.zfae_checkpoint_digest

    def record_teacher(self, teacher_model_id: str) -> None:
        """Append a teacher_model_id to the metadata's `teacher_models_seen` list."""
        try:
            seen = json.loads(self._metadata.get("teacher_models_seen", "[]"))
        except json.JSONDecodeError:
            seen = []
        if teacher_model_id not in seen:
            seen.append(teacher_model_id)
            self._metadata["teacher_models_seen"] = json.dumps(seen)

    # ---- persistence -------------------------------------------------------
    @classmethod
    def load(cls, path: str | Path, agent_id: str) -> "A0ZFAEWeightBank":
        """Load weight bank from a safetensors file. Raises FileNotFoundError if absent.

        Accepts both the new three-core format ({phi, psi, omega} tensors) and the
        legacy single-core format ({weights} tensor; the other two cores are
        re-seeded deterministically from the agent_id).
        """
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"ZFAE checkpoint not found: {path}")
        tensors = load_file(str(path))
        sidecar = path.with_suffix(".meta.json")
        meta: dict[str, str] = {}
        last_loss: float | None = None
        if sidecar.is_file():
            try:
                d = json.loads(sidecar.read_text(encoding="utf-8"))
                meta = {str(k): str(v) for k, v in (d.get("metadata") or {}).items()}
                ll = d.get("last_loss")
                last_loss = float(ll) if isinstance(ll, (int, float)) else None
            except (json.JSONDecodeError, ValueError):
                pass
        if all(c in tensors for c in CORE_NAMES):
            cores = {c: tensors[c] for c in CORE_NAMES}
        elif "weights" in tensors:
            # Legacy single-core checkpoint: phi from file, psi/omega from seed.
            seeded = seed_initial_three_core(agent_id)
            cores = {"phi": tensors["weights"], "psi": seeded["psi"], "omega": seeded["omega"]}
        else:
            raise ValueError(f"checkpoint missing core tensors: {path}")
        gonal_seed = tensors.get("gonal_seed")
        return cls(agent_id, cores=cores, metadata=meta, last_loss=last_loss, gonal_seed=gonal_seed)

    def save(self, path: str | Path) -> str:
        """Save weight bank to safetensors + sidecar metadata JSON. Returns combined digest."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tensors = dict(self._cores)
        tensors["gonal_seed"] = self._gonal_seed
        save_file(tensors, str(path), metadata=self._metadata)
        sidecar = path.with_suffix(".meta.json")
        sidecar.write_text(
            json.dumps({"metadata": self._metadata, "last_loss": self._last_loss}, indent=2),
            encoding="utf-8",
        )
        return self.zfae_checkpoint_digest

    @classmethod
    def fresh(cls, agent_id: str) -> "A0ZFAEWeightBank":
        """Fresh three-core weight bank — deterministic seed init, training_step=0."""
        return cls(agent_id)


__all__ = [
    "A0ZFAEWeightBank",
    "WEIGHT_SHAPE",
    "WEIGHT_COUNT",
    "WEIGHT_COUNT_PER_CORE",
    "WEIGHT_COUNT_TOTAL",
    "CORE_NAMES",
]
# ratios: loc_comments=194:87 imports_exports=8:2 calls_definitions=71:25
