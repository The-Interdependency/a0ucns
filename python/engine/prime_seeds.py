# 116:28
"""
PrimeSeedLayer — 7 independent PTCACore instances seeded from sigma tensor slices.

PRIME_SEEDS = [3, 5, 7, 11, 13, 17, 19]

Each core is parameterized by its prime N, initialized from a sigma tensor
slice at boot, and propagates on every heartbeat tick (task_type="prime_seeds_tick").

  N=17  → seed_s (short-term) — merged into pcna.memory_s on every tick
  N=19  → seed_l (long-term)  — promoted into pcna.memory_l when zeta bandit decides

Bandit domain: "prime_seeds"
  arm "tick_active" — rewarded with avg seed coherence after each tick cycle
  arm "lt_promote"  — rewarded with LT coherence when promotion fires;
                       bandit accumulates signal and decides future promotions

Injection context (for zeta prompt composition):
  LT (N=19) → prompt cache prefix  (stable, promoted explicitly/bandit)
  ST (N=17) → after cache          (volatile, merged every tick)
  sub-agent seeds → volatile       (not persisted, not injected into cache)
"""

import time
import numpy as np
from .ptca_core import PTCACore

PRIME_SEEDS: list[int] = [3, 5, 7, 11, 13, 17, 19]
_SEED_N_ST = 17
_SEED_N_LT = 19


class PrimeSeedLayer:
    """Seven independent prime-seed PTCA cores, tick-driven by the heartbeat."""

    def __init__(self) -> None:
        self.cores: dict[int, PTCACore] = {
            n: PTCACore(
                name=f"seed_{n}",
                symbol=f"S{n}",
                role="prime_seed",
                n=n,
                seed=n,
            )
            for n in PRIME_SEEDS
        }
        self.tick_count: int = 0
        self.last_lt_promotion: float | None = None
        self.created_at: float = time.time()

    # ------------------------------------------------------------------
    # Boot
    # ------------------------------------------------------------------

    def boot(self) -> None:
        """Inject sigma tensor slices into each core at startup.

        Sigma tensor is shape [n_sigma, 4] (angle, log_size, depth, type).
        For each prime seed N: take the first min(N, n_sigma) rows, average
        across the 4 feature dims to get a [rows] hub signal, pad to [N],
        then inject into the core's phase-0 dim-0 layer.
        """
        try:
            from .sigma import get_sigma
            sig = get_sigma()
            if sig.tensor is None or sig.n == 0:
                print("[prime_seeds] boot: sigma not ready, using fresh tensors")
                return
            for n, core in self.cores.items():
                rows = min(n, sig.tensor.shape[0])
                slice_means = sig.tensor[:rows, :].mean(axis=1)
                signal = np.zeros(n, dtype=np.float64)
                signal[:rows] = np.clip(slice_means, 0.0, 1.0)
                core.inject(signal)
            print(
                f"[prime_seeds] booted {len(self.cores)} cores from sigma"
                f" (sigma_n={sig.n})"
            )
        except Exception as exc:
            print(f"[prime_seeds] boot error — fresh tensors retained: {exc}")

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------

    def tick(self) -> dict:
        """Propagate all 7 seeds; merge ST→memory_s; zeta bandit decides LT→memory_l."""
        from ..main import get_pcna
        from ..services.bandit import ensure_arm, update_arm_stats

        pcna = get_pcna()

        for core in self.cores.values():
            core.propagate(steps=5)

        st = self.cores[_SEED_N_ST]
        lt = self.cores[_SEED_N_LT]

        # ST always merges into memory_s
        pcna.memory_s.absorb(st.tensor)

        # LT promotion: bandit arms accumulate signal; promote when bandit
        # has positive avg_reward AND LT coherence exceeds ST coherence.
        arms = pcna.bandit_state.setdefault("prime_seeds", [])
        ensure_arm(arms, "lt_promote")
        ensure_arm(arms, "tick_active")

        promoted = False
        lt_arm = next((a for a in arms if a["arm_id"] == "lt_promote"), None)
        if lt_arm:
            coherence_edge = lt.ring_coherence > st.ring_coherence
            # First pull (pulls==0) treated as explore → promote once to seed LT.
            first_pull = lt_arm.get("pulls", 0) == 0
            bandit_positive = lt_arm.get("avg_reward", 0.0) > 0.0
            if coherence_edge and (first_pull or bandit_positive):
                pcna.memory_l.absorb(lt.tensor)
                update_arm_stats(lt_arm, reward=lt.ring_coherence)
                self.last_lt_promotion = time.time()
                promoted = True

        tick_arm = next((a for a in arms if a["arm_id"] == "tick_active"), None)
        if tick_arm:
            avg_coh = float(np.mean([c.ring_coherence for c in self.cores.values()]))
            update_arm_stats(tick_arm, reward=avg_coh)

        self.tick_count += 1
        return {
            "tick": self.tick_count,
            "lt_promoted": promoted,
            "st_coherence": round(st.ring_coherence, 4),
            "lt_coherence": round(lt.ring_coherence, 4),
            "avg_coherence": round(
                float(np.mean([c.ring_coherence for c in self.cores.values()])), 4
            ),
        }

    # ------------------------------------------------------------------
    # Zeta injection context
    # ------------------------------------------------------------------

    def memory_context(self) -> dict:
        """Return ST and LT tensor summaries for zeta prompt composition.

        Callers:
          LT dict → inject into prompt cache prefix (stable, high-reward).
          ST dict → inject after cache (volatile, recent).
        """
        st = self.cores[_SEED_N_ST]
        lt = self.cores[_SEED_N_LT]
        return {
            "lt": {
                "n": lt.n,
                "ring_coherence": round(lt.ring_coherence, 4),
                "hub_mean": round(float(lt.tensor[:, :, :, 6].mean()), 4),
                "tensor_mean": round(float(lt.tensor.mean()), 4),
            },
            "st": {
                "n": st.n,
                "ring_coherence": round(st.ring_coherence, 4),
                "hub_mean": round(float(st.tensor[:, :, :, 6].mean()), 4),
                "tensor_mean": round(float(st.tensor.mean()), 4),
            },
        }

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def state(self) -> dict:
        return {
            "cores": {str(n): c.state() for n, c in self.cores.items()},
            "tick_count": self.tick_count,
            "last_lt_promotion": self.last_lt_promotion,
            "uptime_s": round(time.time() - self.created_at, 1),
        }


_prime_seeds = PrimeSeedLayer()


def get_prime_seeds() -> PrimeSeedLayer:
    return _prime_seeds
# 116:28
