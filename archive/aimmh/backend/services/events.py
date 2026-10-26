# ratios: loc_comments=90:10 imports_exports=6:5 calls_definitions=13:7
"""Append-only event engine aligned to spec.md v1.0.2-S9.

Every interaction is an append-only event. No destructive edits.
Corrections are new events referencing prior IDs.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from db import db

COLLECTION = "events"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return f"sha256:{hashlib.sha256(raw.encode()).hexdigest()}"


async def emit_event(
    event_type: str,
    thread_id: str,
    actor_id: str,
    payload: Dict[str, Any],
    refs: Optional[List[str]] = None,
) -> dict:
    """Append a single immutable event to the event stream."""
    event = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "ts": _iso_now(),
        "thread_id": thread_id,
        "actor_id": actor_id,
        "event_type": event_type,
        "refs": refs or [],
        "payload": payload,
        "hash": _hash_payload(payload),
        "sig": None,
    }
    await db[COLLECTION].insert_one(event)
    # Return without _id
    event.pop("_id", None)
    return event


async def get_events(
    thread_id: str,
    event_types: Optional[List[str]] = None,
    limit: int = 500,
) -> List[dict]:
    """Retrieve events for a thread, optionally filtered by type."""
    query: Dict[str, Any] = {"thread_id": thread_id}
    if event_types:
        query["event_type"] = {"$in": event_types}
    cursor = db[COLLECTION].find(query, {"_id": 0}).sort("ts", 1).limit(limit)
    return await cursor.to_list(limit)


async def get_events_since(
    thread_id: str,
    since_event_id: str,
    limit: int = 500,
) -> List[dict]:
    """Get events after a given event_id (for polling)."""
    anchor = await db[COLLECTION].find_one(
        {"event_id": since_event_id}, {"_id": 0, "ts": 1}
    )
    if not anchor:
        return await get_events(thread_id, limit=limit)

    cursor = (
        db[COLLECTION]
        .find(
            {"thread_id": thread_id, "ts": {"$gt": anchor["ts"]}},
            {"_id": 0},
        )
        .sort("ts", 1)
        .limit(limit)
    )
    return await cursor.to_list(limit)


def build_provenance(model: str = "", build: str = "v1.0.2-S9") -> dict:
    """Standard provenance block (S1) attached to every response."""
    return {
        "ts": _iso_now(),
        "model": model,
        "build": build,
        "hash": "",
    }


def build_sentinel_context(
    window_type: str = "turns",
    window_w: int = 32,
    retrieval_mode: str = "none",
    risk_score: float = 0.0,
    evidence_events: Optional[List[str]] = None,
) -> dict:
    """Standard sentinel context block (S5-S9)."""
    return {
        "S5_context": {
            "window": {"type": window_type, "W": window_w},
            "retrieval_mode": retrieval_mode,
        },
        "S6_identity": {"actor_map_version": "v1", "confidence": 1.0},
        "S7_memory": {"store_allowed": True, "retention": "permanent"},
        "S8_risk": {"score": risk_score, "flags": []},
        "S9_audit": {
            "evidence_events": evidence_events or [],
            "retrieval_log": [],
        },
    }
# ratios: loc_comments=90:10 imports_exports=6:5 calls_definitions=13:7
