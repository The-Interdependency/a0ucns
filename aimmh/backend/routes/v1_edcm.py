# ratios: loc_comments=72:6 imports_exports=8:3 calls_definitions=23:3
"""V1 EDCM endpoints — Energy-Dissonance Circuit Model."""

import uuid
from fastapi import APIRouter, Depends
from db import db
from models.v1 import EdcmBoneReport, EdcmEvalRequest
from services.auth import get_current_user, get_user_id
from services.edcm import evaluate_edcm
from services.events import build_provenance, build_sentinel_context, emit_event

router = APIRouter(prefix="/api/v1/edcm", tags=["edcm"])


@router.post("/eval", response_model=EdcmBoneReport)
async def eval_edcm(
    request: EdcmEvalRequest,
    current_user: dict = Depends(get_current_user),
):
    """Evaluate EDCM metrics on a thread window."""
    user_id = get_user_id(current_user)

    # Get turns from thread
    turns = await db.messages.find(
        {"thread_id": request.thread_id, "user_id": user_id},
        {"_id": 0},
    ).sort("timestamp", 1).to_list(500)

    window_w = 32
    if request.context and request.context.get("window"):
        window_w = request.context["window"].get("W", 32)

    report = evaluate_edcm(
        turns=turns,
        goal_text=request.goal_text or "",
        declared_constraints=request.declared_constraints,
        window_w=window_w,
    )
    report["thread_id"] = request.thread_id
    report["provenance"] = build_provenance(model="edcm")
    report["sentinel_context"] = build_sentinel_context(window_w=window_w)

    # Emit metric event
    await emit_event(
        "metric",
        request.thread_id,
        "system:edcm",
        {
            "snapshot_id": report["snapshot_id"],
            "metrics": {k: v["value"] for k, v in report["metrics"].items()},
            "alert_count": len(report["alerts"]),
        },
    )

    return EdcmBoneReport(**report)


@router.get("/metrics/{thread_id}")
async def get_metrics(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get latest EDCM metrics for a thread (from event log)."""
    from services.events import get_events
    events = await get_events(thread_id, event_types=["metric"], limit=50)
    metric_events = [e for e in events if e.get("payload", {}).get("snapshot_id")]
    return {
        "thread_id": thread_id,
        "metric_snapshots": metric_events[-10:],
        "provenance": build_provenance(model="edcm"),
    }


@router.get("/alerts/{thread_id}")
async def get_alerts(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get alerts from latest EDCM eval for a thread."""
    user_id = get_user_id(current_user)
    turns = await db.messages.find(
        {"thread_id": thread_id, "user_id": user_id},
        {"_id": 0},
    ).sort("timestamp", 1).to_list(500)

    report = evaluate_edcm(turns)
    report["thread_id"] = thread_id

    return {
        "thread_id": thread_id,
        "alerts": report["alerts"],
        "metric_summary": {k: v["value"] for k, v in report["metrics"].items()},
        "provenance": build_provenance(model="edcm"),
    }
# ratios: loc_comments=72:6 imports_exports=8:3 calls_definitions=23:3
