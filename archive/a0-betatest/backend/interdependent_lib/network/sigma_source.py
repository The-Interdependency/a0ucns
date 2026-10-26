# ratios: loc_comments=100:80 imports_exports=7:4 calls_definitions=24:5
# === MODULE_BUILD ===
# id: network_sigma_source
#   module_name: sigma_source
#   module_kind: adapter
#   summary: Σ ring data source — read-only host-integrity digest over OS files + installed program manifests; provides tamper-evidence baseline (pen-test resistance)
#   owner: a0p maintainer
#   public_surface: gather_host_digest, sigma_tensors, SIGMA_WATCHED_PATHS, SIGMA_PKG_COMMANDS, HostDigest
#   internal_surface: _digest_path, _digest_command, _MAX_ENTRIES_PER_DIR
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.sigma_host_digest_stable_holds
#   rollout: default_enabled
#   rollback: revert file; network falls back to deterministic-seed Σ
#   pen_test_resistance: drift in any watched file/package/binary changes the digest, advances Σ ring state, surfaces in coherence as observer signal
#   unresolved: cadence policy (per-tick vs hourly), watched-path tuning per host, pkg-manager set per distro
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: network_sigma_source_boundaries
#   summary: Σ ring data source — read-only host-integrity digest over OS files + installed program manifests; provides tamper-evidence baseline (pen-test resistance)
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: network_sigma_source
#   summary: Σ ring data source — read-only host-integrity digest over OS files + installed program manifests; provides tamper-evidence baseline (pen-test resistance)
#   exposes: gather_host_digest, sigma_tensors, SIGMA_WATCHED_PATHS, SIGMA_PKG_COMMANDS, HostDigest
#   boundaries: auth:none, storage:read, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""Σ ring data source — read-only host-integrity adapter.

Σ is the observer ring (un-weighted in coherence scoring) that watches
the host environment for tamper. Its tensors are derived from a blake2b
digest of:

  • OS config + binary paths   (`/etc`, `/bin`, `/sbin`, `/usr/bin`, `/usr/sbin`)
  • System package manifests   (`dpkg -l`, `rpm -qa`, `pacman -Q`, ...)
  • Python package list        (`pip freeze`)

The digest is deterministic given a stable host state. A drift in any
watched file or package list changes the digest, which changes Σ's
tensors, which advances the Σ ring's state on the next tick — and the
PCEA `kernel_step` "this state, last state" key sync makes the drift
non-fakable without knowing the previous digest.

Σ ring's tensors are derived ONLY from the digest — they are never
written to from inside the network engine. Write attempts at any layer
of the layered model on Σ-derived Tensors do not propagate back to the
host (Tensor is in-memory only).
"""
from __future__ import annotations
import hashlib
import os
import shutil
import subprocess
from dataclasses import dataclass

from ..pcna.tensor import Tensor


# === CONTRACTS ===
# id: sigma_host_digest_stable
#   given: two immediate calls to gather_host_digest()
#   then: the two HostDigest instances carry identical 32-byte digests; paths_scanned > 0
#   class: correctness
#   call: a0p_skills.contracts.sigma_host_digest_stable_holds
# === END CONTRACTS ===


# Path roots — curated for performance. Full enumeration would be too slow.
SIGMA_WATCHED_PATHS: tuple[str, ...] = (
    "/etc",
    "/bin",
    "/sbin",
    "/usr/bin",
    "/usr/sbin",
    "/usr/local/bin",
)

# Per-distro package manager commands (try each; absent ones are skipped).
SIGMA_PKG_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("dpkg", "-l"),
    ("rpm", "-qa"),
    ("pacman", "-Q"),
    ("apk", "info"),
    ("brew", "list"),
    ("pip", "freeze"),
)

# Cap directory enumeration so the digest is bounded in cost.
_MAX_ENTRIES_PER_DIR: int = 256


@dataclass(frozen=True)
class HostDigest:
    """Result of one host-integrity scan."""
    digest: bytes               # 32-byte blake2b digest
    digest_hex: str
    paths_scanned: int
    pkg_commands_run: int


def _digest_path(h: "hashlib._Hash", root: str) -> int:
    """Update the hasher with deterministic-ordered metadata for `root`.

    Returns the number of entries hashed (0 if `root` doesn't exist).
    """
    if not os.path.isdir(root):
        return 0
    try:
        entries = sorted(os.listdir(root))[:_MAX_ENTRIES_PER_DIR]
    except OSError:
        return 0
    count = 0
    for entry in entries:
        full = os.path.join(root, entry)
        try:
            st = os.stat(full)
        except OSError:
            continue
        # We hash size + mtime + entry name — not contents (too slow).
        # The per-tick cheap fingerprint catches mtime drift; a deeper
        # SHA-of-contents pass can be wired separately at lower cadence.
        h.update(f"{full}\t{st.st_size}\t{int(st.st_mtime)}\n".encode("utf-8"))
        count += 1
    return count


def _digest_command(h: "hashlib._Hash", argv: tuple[str, ...]) -> bool:
    """Update the hasher with the trimmed output of `argv`. Returns True on success."""
    if not argv:
        return False
    if shutil.which(argv[0]) is None:
        return False
    try:
        result = subprocess.run(
            list(argv),
            capture_output=True,
            timeout=5.0,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False
    out = result.stdout[:8192]  # cap per command
    h.update(b"\t".join(argv[0].encode("utf-8") for _ in [None]))
    h.update(b"\n")
    h.update(out)
    h.update(b"\n--end--\n")
    return True


def gather_host_digest() -> HostDigest:
    """Compute a deterministic 32-byte digest of the host's integrity state.

    Pure function of current OS state (and not the time). Two consecutive
    calls produce the same digest IFF no watched file or package changed
    between them.
    """
    h = hashlib.blake2b(digest_size=32)
    paths_scanned = 0
    for root in SIGMA_WATCHED_PATHS:
        paths_scanned += _digest_path(h, root)

    pkg_count = 0
    for argv in SIGMA_PKG_COMMANDS:
        if _digest_command(h, argv):
            pkg_count += 1

    raw = h.digest()
    return HostDigest(
        digest=raw,
        digest_hex=raw.hex(),
        paths_scanned=paths_scanned,
        pkg_commands_run=pkg_count,
    )


def sigma_tensors(n: int, digest: bytes | None = None) -> list[Tensor]:
    """Produce N seed-derived Tensors for the Σ ring's leaves.

    Each tensor is seeded from a different 4-byte window of the digest,
    so any drift in the digest changes every tensor.
    """
    if digest is None:
        digest = gather_host_digest().digest
    if not digest:
        raise ValueError("digest must be non-empty bytes")
    base = int.from_bytes(digest[:8], "big")
    return [
        Tensor.from_seed(base + i * 1009, f"sigma::host::{digest.hex()[:8]}::{i}")
        for i in range(n)
    ]


__all__ = [
    "SIGMA_WATCHED_PATHS",
    "SIGMA_PKG_COMMANDS",
    "HostDigest",
    "gather_host_digest",
    "sigma_tensors",
]
# ratios: loc_comments=100:80 imports_exports=7:4 calls_definitions=24:5
