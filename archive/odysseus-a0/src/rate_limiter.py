# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 32:42
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 3:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 12:4
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: rate_limiter
#   module_name: rate_limiter
#   module_kind: hmmm
#   summary: Generic in-memory rate limiter — sliding window, keyed by IP.
#   owner: hmmm
#   public_surface: RateLimiter
#   internal_surface: none
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   tests: hmmm
#   rollout: hmmm
#   rollback: hmmm
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: rate_limiter_boundaries
#   summary: Generic in-memory rate limiter — sliding window, keyed by IP.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: rate_limiter
#   summary: Generic in-memory rate limiter — sliding window, keyed by IP.
#   exposes: RateLimiter
# === END CAPABILITIES ===
# src/rate_limiter.py
"""Generic in-memory rate limiter — sliding window, keyed by IP."""

import threading
import time
from typing import Dict, List


class RateLimiter:
    """Sliding-window rate limiter.

    Usage:
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        if not limiter.check(ip):
            raise HTTPException(429, "Too many requests")
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self._log: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        self._last_cleanup = time.monotonic()
        self._cleanup_interval = max(window_seconds * 2, 120)

    def check(self, key: str) -> bool:
        """Return True if the request is allowed, False if rate-limited."""
        now = time.monotonic()
        with self._lock:
            self._maybe_cleanup(now)
            timestamps = self._log.get(key, [])
            cutoff = now - self.window
            timestamps = [t for t in timestamps if t > cutoff]
            if len(timestamps) >= self.max_requests:
                self._log[key] = timestamps
                return False
            timestamps.append(now)
            self._log[key] = timestamps
            return True

    def _maybe_cleanup(self, now: float) -> None:
        """Periodically purge stale entries."""
        if now - self._last_cleanup < self._cleanup_interval:
            return
        self._last_cleanup = now
        cutoff = now - self.window
        stale = [k for k, v in self._log.items() if not v or v[-1] <= cutoff]
        for k in stale:
            del self._log[k]
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 32:42
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 3:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 12:4
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
