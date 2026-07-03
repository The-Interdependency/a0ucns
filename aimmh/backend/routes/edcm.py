# ratios: loc_comments=147:9 imports_exports=6:5 calls_definitions=31:5
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import logging

from db import db
from models.edcm import EDCMMetrics, EDCMMetricsIngest, A0Config
from services.auth import get_current_user, get_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/edcm", tags=["edcm"])


@router.post("/ingest")
async def ingest_edcm_metrics(
    payload: EDCMMetricsIngest,
    current_user: dict = Depends(get_current_user)
):
    """Receive EDCM metrics from Agent Zero (stub receiver)"""
    uid = get_user_id(current_user)
    conversation = await db.conversations.find_one(
        {"id": payload.conversation_id, "user_id": uid},
        {"_id": 0}
    )

    messages = None
    if conversation:
        cursor = db.messages.find(
            {"conversation_id": payload.conversation_id, "user_id": uid},
            {"_id": 0}
        ).sort("timestamp", 1)
        try:
            messages = await cursor.to_list(length=None)
        except TypeError:
            messages = await cursor.to_list(length=2000)

    context_snapshot = {
        "global_context": conversation.get("global_context") if conversation else None,
        "model_roles": conversation.get("model_roles") if conversation else None,
        "context_mode": conversation.get("context_mode") if conversation else None
    }

    doc = {
        "user_id": uid,
        "conversation_id": payload.conversation_id,
        "constraint_mismatch_density": payload.metrics.constraint_mismatch_density,
        "fixation_coefficient": payload.metrics.fixation_coefficient,
        "escalation_gradient": payload.metrics.escalation_gradient,
        "context_drift_index": payload.metrics.context_drift_index,
        "load_saturation_index": payload.metrics.load_saturation_index,
        "source": payload.source,
        "metadata": payload.metrics.metadata,
        "timestamp": payload.timestamp or datetime.now(timezone.utc).isoformat()
    }

    if messages is not None:
        doc["conversation_snapshot"] = {
            "title": conversation.get("title") if conversation else None,
            "messages": messages,
            "context": context_snapshot
        }

    await db.edcm_metrics.insert_one(doc)
    return {"message": "EDCM metrics ingested", "conversation_id": payload.conversation_id}


@router.get("/metrics")
async def get_edcm_metrics(
    conversation_id: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Get EDCM metrics for dashboard"""
    uid = get_user_id(current_user)
    query = {"user_id": uid}
    if conversation_id:
        query["conversation_id"] = conversation_id

    metrics = await db.edcm_metrics.find(
        query, {"_id": 0}
    ).sort("timestamp", -1).limit(50).to_list(50)

    return {"metrics": metrics}


@router.get("/response-times")
async def get_response_times(current_user: dict = Depends(get_current_user)):
    """Get response time stats per model"""
    uid = get_user_id(current_user)

    pipeline = [
        {"$match": {"user_id": uid, "role": "assistant", "response_time_ms": {"$exists": True}}},
        {"$group": {
            "_id": "$model",
            "avg_ms": {"$avg": "$response_time_ms"},
            "min_ms": {"$min": "$response_time_ms"},
            "max_ms": {"$max": "$response_time_ms"},
            "count": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "model": "$_id",
            "avg_ms": {"$round": ["$avg_ms", 0]},
            "min_ms": 1,
            "max_ms": 1,
            "count": 1
        }}
    ]
    results = await db.messages.aggregate(pipeline).to_list(20)
    return {"response_times": results}


@router.get("/feedback-stats")
async def get_feedback_stats(current_user: dict = Depends(get_current_user)):
    """Get thumbs up/down stats per model"""
    uid = get_user_id(current_user)

    pipeline = [
        {"$match": {"user_id": uid, "role": "assistant", "feedback": {"$ne": None}}},
        {"$group": {
            "_id": {"model": "$model", "feedback": "$feedback"},
            "count": {"$sum": 1}
        }}
    ]
    raw = await db.messages.aggregate(pipeline).to_list(100)

    stats = {}
    for r in raw:
        model = r["_id"]["model"]
        fb = r["_id"]["feedback"]
        if model not in stats:
            stats[model] = {"model": model, "up": 0, "down": 0}
        stats[model][fb] = r["count"]

    return {"feedback_stats": list(stats.values())}


@router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """Aggregated dashboard data for EDCM + performance"""
    uid = get_user_id(current_user)

    # Latest EDCM metrics
    latest_edcm = await db.edcm_metrics.find(
        {"user_id": uid}, {"_id": 0}
    ).sort("timestamp", -1).limit(10).to_list(10)

    # Response times
    rt_pipeline = [
        {"$match": {"user_id": uid, "role": "assistant", "response_time_ms": {"$exists": True}}},
        {"$group": {
            "_id": "$model",
            "avg_ms": {"$avg": "$response_time_ms"},
            "min_ms": {"$min": "$response_time_ms"},
            "max_ms": {"$max": "$response_time_ms"},
            "count": {"$sum": 1}
        }},
        {"$project": {"_id": 0, "model": "$_id", "avg_ms": {"$round": ["$avg_ms", 0]}, "min_ms": 1, "max_ms": 1, "count": 1}}
    ]
    response_times = await db.messages.aggregate(rt_pipeline).to_list(20)

    # Feedback
    fb_pipeline = [
        {"$match": {"user_id": uid, "role": "assistant", "feedback": {"$ne": None}}},
        {"$group": {"_id": {"model": "$model", "feedback": "$feedback"}, "count": {"$sum": 1}}}
    ]
    fb_raw = await db.messages.aggregate(fb_pipeline).to_list(100)
    fb_stats = {}
    for r in fb_raw:
        model = r["_id"]["model"]
        fb = r["_id"]["feedback"]
        if model not in fb_stats:
            fb_stats[model] = {"model": model, "up": 0, "down": 0}
        fb_stats[model][fb] = r["count"]

    # Total conversations and messages
    total_convs = await db.conversations.count_documents({"user_id": uid})
    total_msgs = await db.messages.count_documents({"user_id": uid, "role": "assistant"})

    return {
        "edcm_metrics": latest_edcm,
        "response_times": response_times,
        "feedback_stats": list(fb_stats.values()),
        "total_conversations": total_convs,
        "total_messages": total_msgs
    }
# ratios: loc_comments=147:9 imports_exports=6:5 calls_definitions=31:5
