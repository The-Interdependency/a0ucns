# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 10:37
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 3:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: docs
#   module_name: docs
#   module_kind: service
#   summary: Docs service — personal document RAG with ChromaDB.
#   owner: hmmm
#   public_surface: none
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
# id: docs_boundaries
#   summary: Docs service — personal document RAG with ChromaDB.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: docs
#   summary: Docs service — personal document RAG with ChromaDB.
#   exposes: none
# === END CAPABILITIES ===
# services/docs/__init__.py
"""Docs service — personal document RAG with ChromaDB.

Thin facade: DocsService lives here, RAGManager/VectorRAG are re-exported
from the canonical implementations in src/.
"""

from .service import DocsService, DocChunk, IndexResult
from src.rag_manager import RAGManager
from src.rag_vector import VectorRAG

__all__ = [
    "DocsService",
    "DocChunk",
    "IndexResult",
    "RAGManager",
    "VectorRAG",
]
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 10:37
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 3:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
