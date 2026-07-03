# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 33:46
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 5:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 9:1
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: rag_singleton
#   module_name: rag_singleton
#   module_kind: hmmm
#   summary: RAG singleton instance for the application.
#   owner: hmmm
#   public_surface: get_rag_manager
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
# id: rag_singleton_boundaries
#   summary: RAG singleton instance for the application.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: rag_singleton
#   summary: RAG singleton instance for the application.
#   exposes: get_rag_manager
# === END CAPABILITIES ===
"""
RAG singleton instance for the application.
"""
import os
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

rag_instance = None
_last_attempt = 0.0
_RETRY_INTERVAL = 30  # seconds between re-init attempts


def get_rag_manager():
    """Lazy ChromaDB-backed VectorRAG initializer.

    Returns the VectorRAG instance on first successful init, None if ChromaDB
    isn't reachable / available. Failed init attempts are throttled to once
    per _RETRY_INTERVAL seconds so a missing ChromaDB doesn't busy-retry on
    every request — callers (personal-doc routes etc.) get None back and
    return a clean 503 to the user instead.

    Historical note: this used to be hardcoded to ``return None`` with a
    comment about chromadb 1.4.1 / pydantic 2.12 being mutually incompatible.
    That compat issue is resolved in current pinned versions
    (chromadb 1.5.x + pydantic 2.13.x), so the real initializer is back.
    """
    global rag_instance, _last_attempt

    if rag_instance is not None:
        return rag_instance

    now = time.monotonic()
    if now - _last_attempt < _RETRY_INTERVAL:
        return None  # too soon to retry — last attempt failed

    _last_attempt = now

    try:
        from src.rag_vector import VectorRAG

        base_dir = Path(__file__).parent.parent
        persist_dir = os.path.join(base_dir, "data", "rag")

        rag_instance = VectorRAG(persist_directory=persist_dir)
        if not rag_instance.healthy:
            logger.warning("VectorRAG created but not healthy, will retry later")
            rag_instance = None
        else:
            logger.info("Initialized VectorRAG with ChromaDB")

    except ImportError as e:
        logger.warning(f"VectorRAG not available: {e}")
        rag_instance = None
    except Exception as e:
        logger.error(f"Failed to initialize RAG: {e}")
        rag_instance = None

    return rag_instance
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 33:46
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 5:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 9:1
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
