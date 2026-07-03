# ratios: loc_comments=21:0 imports_exports=4:1 calls_definitions=2:2
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

from db import db


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def append_audit_event(
    collection: str,
    event_type: str,
    actor_user_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
):
    await db[collection].insert_one(
        {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "actor_user_id": actor_user_id,
            "payload": payload or {},
            "created_at": _iso_now(),
        }
    )
# ratios: loc_comments=21:0 imports_exports=4:1 calls_definitions=2:2
