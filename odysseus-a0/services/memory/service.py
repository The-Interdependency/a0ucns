# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 74:61
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 6:3
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 31:11
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: service
#   module_name: service
#   module_kind: service
#   summary: Memory service — persistent memory storage and retrieval.
#   owner: hmmm
#   public_surface: Memory, MemorySearchResult, MemoryService
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
# id: service_boundaries
#   summary: Memory service — persistent memory storage and retrieval.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: service
#   summary: Memory service — persistent memory storage and retrieval.
#   exposes: Memory, MemorySearchResult, MemoryService
# === END CAPABILITIES ===
# services/memory/service.py
"""Memory service — persistent memory storage and retrieval."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import os

from .memory import MemoryManager
from .memory_vector import MemoryVectorStore
from src.memory_provider import MemoryRecord, NativeMemoryProvider


@dataclass
class Memory:
    """A stored memory."""
    id: str
    text: str
    timestamp: int
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemorySearchResult:
    """Result of memory search."""
    memories: List[Memory]
    query: str
    total: int


class MemoryService:
    """
    Memory storage and retrieval service.

    Usage:
        service = MemoryService()
        await service.remember("User prefers dark mode")
        results = await service.recall("preferences")
    """

    def __init__(self, data_dir: str = "data"):
        self.manager = MemoryManager(data_dir)
        self.vector_store = MemoryVectorStore(data_dir) if os.path.exists(
            os.path.join(data_dir, "memory_vectors")
        ) else None
        self.provider = NativeMemoryProvider(self.manager, self.vector_store)

    def _sync_provider(self) -> None:
        self.provider.memory_vector = self.vector_store

    @staticmethod
    def _to_memory(entry: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Memory:
        return Memory(
            id=entry.get("id", ""),
            text=entry.get("text", ""),
            timestamp=entry.get("timestamp", 0),
            session_id=entry.get("session_id"),
            metadata=metadata or {},
        )

    @staticmethod
    def _record_to_memory(record: MemoryRecord, metadata: Optional[Dict[str, Any]] = None) -> Memory:
        merged_metadata = dict(record.metadata)
        if metadata:
            merged_metadata.update(metadata)
        return Memory(
            id=record.id,
            text=record.text,
            timestamp=record.timestamp,
            session_id=record.session_id,
            metadata=merged_metadata,
        )

    async def remember(self, text: str, session_id: Optional[str] = None) -> Memory:
        """
        Store a new memory.

        Args:
            text: Memory content
            session_id: Optional session association

        Returns:
            Created Memory object
        """
        self._sync_provider()
        record = await self.provider.remember(text, session_id=session_id)
        return self._record_to_memory(record)

    async def recall(self, query: str, top_k: int = 5) -> MemorySearchResult:
        """
        Search memories.

        Args:
            query: Search query
            top_k: Max results

        Returns:
            MemorySearchResult with matching memories
        """
        self._sync_provider()
        results = await self.provider.recall(query, top_k=top_k)
        memories = [
            self._record_to_memory(hit.memory, metadata={"score": hit.score})
            if hit.score is not None
            else self._record_to_memory(hit.memory)
            for hit in results
        ]
        return MemorySearchResult(memories=memories, query=query, total=len(memories))

    def get_all(self, limit: int = 100) -> List[Memory]:
        """Get all memories."""
        records = self.manager.load_all()[:limit]
        return [self._to_memory(m) for m in records]

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        memories = self.manager.load_all()
        remaining = [m for m in memories if m.get("id") != memory_id]
        if len(remaining) == len(memories):
            return False

        self.manager.save(remaining)
        if self.vector_store and self.vector_store.healthy:
            self.vector_store.remove(memory_id)
        return True
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 74:61
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 6:3
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 31:11
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
