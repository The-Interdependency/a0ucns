# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 39:49
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 4:2
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 11:3
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: chroma_client
#   module_name: chroma_client
#   module_kind: hmmm
#   summary: chroma_client.py
#   owner: hmmm
#   public_surface: get_chroma_client, reset_client
#   internal_surface: _port_open
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
# id: chroma_client_boundaries
#   summary: chroma_client.py
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: chroma_client
#   summary: chroma_client.py
#   exposes: get_chroma_client, reset_client
# === END CAPABILITIES ===
"""
chroma_client.py

Singleton ChromaDB HTTP client.
Connects to a ChromaDB instance running as a standalone service.
"""

import os
import socket
import logging

logger = logging.getLogger(__name__)

_client = None

# A short connect probe so an unreachable ChromaDB fails fast instead of
# blocking on the OS connection timeout (~30-60s, WinError 10060 on Windows),
# which otherwise stalls app startup. Tunable via CHROMADB_CONNECT_TIMEOUT.
_CONNECT_TIMEOUT = float(os.getenv("CHROMADB_CONNECT_TIMEOUT", "2.0"))


def _port_open(host: str, port: int, timeout: float = None) -> bool:
    """Return True if a TCP connection to host:port succeeds within timeout."""
    try:
        with socket.create_connection((host, port), timeout=timeout or _CONNECT_TIMEOUT):
            return True
    except OSError:
        return False


def get_chroma_client():
    """Get or create the singleton ChromaDB HTTP client.

    Raises RuntimeError with a clear install hint if the `chromadb` package
    is not installed — it's an optional dependency (RAG + memory vectors).
    """
    global _client
    if _client is not None:
        return _client

    try:
        import chromadb
    except ImportError as e:
        raise RuntimeError(
            "ChromaDB integration is not installed. Install the optional "
            "dependency with: pip install chromadb-client"
        ) from e

    host = os.getenv("CHROMADB_HOST", "localhost")
    port = int(os.getenv("CHROMADB_PORT", "8100"))

    if not _port_open(host, port):
        raise RuntimeError(
            f"ChromaDB is not reachable at {host}:{port}. Start the ChromaDB "
            f"service (e.g. `docker compose up chromadb`) or set CHROMADB_HOST / "
            f"CHROMADB_PORT to point at a running instance."
        )

    client = chromadb.HttpClient(host=host, port=port)

    # Health check before caching — if the port is open but the service isn't
    # healthy yet (e.g. still starting), don't poison the singleton with a dead
    # client; leave _client unset so the next call retries.
    client.heartbeat()
    _client = client
    logger.info(f"ChromaDB connected: {host}:{port}")
    return _client


def reset_client():
    """Reset the singleton (e.g. after config change)."""
    global _client
    _client = None
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 39:49
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 4:2
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 11:3
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
