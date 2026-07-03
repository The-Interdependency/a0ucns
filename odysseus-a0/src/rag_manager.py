# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 28:50
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 5:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 10:9
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: rag_manager
#   module_name: rag_manager
#   module_kind: hmmm
#   summary: rag_manager.py
#   owner: hmmm
#   public_surface: RAGManager
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
# id: rag_manager_boundaries
#   summary: rag_manager.py
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: rag_manager
#   summary: rag_manager.py
#   exposes: RAGManager
# === END CAPABILITIES ===
"""
rag_manager.py

A thin wrapper around VectorRAG for backward compatibility and additional features.
"""

import logging
from typing import List, Dict, Any

# Try to import from different possible locations
try:
    from rag_vector import VectorRAG
except ImportError:
    try:
        from .rag_vector import VectorRAG
    except ImportError:
        from src.rag_vector import VectorRAG

logger = logging.getLogger(__name__)

class RAGManager:
    """
    A manager class that wraps VectorRAG for backward compatibility.
    Most methods delegate directly to VectorRAG.
    """
    
    def __init__(self, persist_directory: str = "data/chroma"):
        """Initialize the RAGManager with VectorRAG."""
        self.vector_rag = VectorRAG(persist_directory=persist_directory)
        logger.info("RAGManager initialized as wrapper for VectorRAG")
    
    # Delegate all methods to VectorRAG
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for documents - delegates to VectorRAG."""
        return self.vector_rag.search(query, k)
    
    def index_personal_documents(self, directory: str) -> Dict[str, Any]:
        """Index documents - delegates to VectorRAG."""
        return self.vector_rag.index_personal_documents(directory)
    
    def retrieve(self, query: str, k: int = 5) -> List[str]:
        """Retrieve relevant chunks - delegates to VectorRAG."""
        return self.vector_rag.retrieve(query, k)
    
    def rebuild_index(self) -> bool:
        """Rebuild index - delegates to VectorRAG."""
        return self.vector_rag.rebuild_index()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stats - delegates to VectorRAG."""
        return self.vector_rag.get_stats()
    
    def add_document(self, text: str, metadata: Dict[str, Any]) -> bool:
        """Add single document - delegates to VectorRAG."""
        return self.vector_rag.add_document(text, metadata)
    
    def add_documents_batch(self, docs: List[tuple]) -> Dict[str, Any]:
        """Add documents in batch - delegates to VectorRAG."""
        return self.vector_rag.add_documents_batch(docs)
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 28:50
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 5:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 10:9
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
