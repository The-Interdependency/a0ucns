# 26:8
"""
UCNSAuditLog — append-only audit log keyed by UCNSObject identity.
S9-sentinel-compatible record format. In-memory only in v0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class AuditRecord:
    ucns_key: tuple
    event: str
    timestamp: str
    metadata: dict = field(default_factory=dict)


class UCNSAuditLog:
    """Append-only log of UCNS-keyed events."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def append(self, obj, event: str, metadata: dict | None = None) -> None:
        """Record an event keyed to obj."""
        from .pool import UCNSPool
        self._records.append(AuditRecord(
            ucns_key=UCNSPool._key(obj),
            event=event,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        ))

    def records(self) -> list[AuditRecord]:
        """All records, oldest first."""
        return list(self._records)

    def since(self, iso_timestamp: str) -> list[AuditRecord]:
        """Records with timestamp >= iso_timestamp (ISO 8601)."""

        def _parse(ts: str) -> datetime:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt

        cutoff = _parse(iso_timestamp)
        return [r for r in self._records if _parse(r.timestamp) >= cutoff]

    def __len__(self) -> int:
        return len(self._records)
# 26:8
