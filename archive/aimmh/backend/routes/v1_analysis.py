# ratios: loc_comments=277:20 imports_exports=14:7 calls_definitions=92:12
"""Transcript analysis — upload, parse with LLM, apply EDCM per turn, generate report."""

import uuid
import time
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from db import db
from services.auth import get_current_user, get_user_id
from services.edcm import (
    compute_cm, compute_da, compute_drift, compute_dvg,
    compute_int, compute_tbf, ALERT_HIGH
)
from services.events import build_provenance, emit_event
from services.llm import DEFAULT_REGISTRY, generate_response, reconcile_registry_developers

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---- Models ----

class AnalysisRequest(BaseModel):
    transcript_text: str
    model: str = "gpt-4o-mini"
    goal_text: Optional[str] = ""
    declared_constraints: Optional[List[str]] = None
    custom_prompt: Optional[str] = None


class TurnMetric(BaseModel):
    turn_index: int
    speaker: str
    content: str
    metrics: Dict[str, Any]
    flags: List[str] = Field(default_factory=list)


class AnalysisReport(BaseModel):
    analysis_id: str
    title: str
    created_at: str
    model_used: str
    turn_count: int
    turns: List[TurnMetric]
    summary_metrics: Dict[str, Any]
    flagged_turns: List[int]
    narrative_summary: str
    provenance: Dict[str, Any]


PARSE_PROMPT = """You are a transcript analysis engine. Parse the following transcript into a JSON array of turns.
Each turn is a speaker change. Output ONLY valid JSON, no markdown fences.

Format: [{"speaker": "Name", "content": "What they said"}, ...]

Rules:
- Detect speaker changes from labels like "Speaker A:", "John:", timestamps, or paragraph breaks
- If speakers are unnamed, use "Speaker 1", "Speaker 2", etc.
- Preserve the exact content of each turn
- Do not summarize or modify the content

Transcript:
{transcript}"""


async def _parse_transcript_with_llm(
    transcript: str, model: str, user: dict, registry: dict
) -> List[dict]:
    """Use an LLM to parse a raw transcript into structured turns."""
    import json as json_mod

    prompt = PARSE_PROMPT.replace("{transcript}", transcript[:15000])
    messages = [{"role": "user", "content": prompt}]

    full_response = ""
    async for chunk in generate_response(model, messages, f"parse_{uuid.uuid4().hex[:8]}", user, registry):
        full_response += chunk

    if full_response.startswith("[ERROR]"):
        raise HTTPException(status_code=502, detail=f"LLM parsing failed: {full_response}")

    # Clean response — strip markdown fences if present
    cleaned = full_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

    try:
        turns = json_mod.loads(cleaned)
        if not isinstance(turns, list):
            raise ValueError("Expected list")
        return turns
    except (json_mod.JSONDecodeError, ValueError):
        # Fallback: split by newlines and treat each as a turn
        lines = [line_text.strip() for line_text in transcript.split("\n") if line_text.strip()]
        turns = []
        for i, line in enumerate(lines):
            # Try to detect "Speaker: content" pattern
            if ":" in line:
                parts = line.split(":", 1)
                turns.append({"speaker": parts[0].strip(), "content": parts[1].strip()})
            else:
                turns.append({"speaker": f"Speaker {i + 1}", "content": line})
        return turns


def _compute_turn_metrics(
    turn: dict, all_turns: List[dict], turn_idx: int,
    goal_text: str, declared_constraints: List[str]
) -> Dict[str, Any]:
    """Compute EDCM metrics for a single turn in context."""
    content = turn.get("content", "")
    window = all_turns[max(0, turn_idx - 5):turn_idx + 1]

    metrics = {}
    metrics["CM"] = compute_cm(declared_constraints, content)
    metrics["DA"] = compute_da(window)
    metrics["DRIFT"] = compute_drift(goal_text, content)
    metrics["DVG"] = compute_dvg(window)
    metrics["INT"] = compute_int(window)
    metrics["TBF"] = compute_tbf(window)

    return metrics


def _detect_flags(metrics: Dict[str, Any]) -> List[str]:
    """Detect metric spikes and generate human-readable flags."""
    flags = []
    for name, m in metrics.items():
        val = m.get("value", 0)
        if val >= ALERT_HIGH:
            labels = {
                "CM": "Constraint violation detected",
                "DA": "High dissonance — possible contradiction or retraction",
                "DRIFT": "Topic drift from stated goal",
                "DVG": "High divergence in topics",
                "INT": "Elevated emotional intensity",
                "TBF": "Turn balance imbalance — one party dominating",
            }
            flags.append(f"{name}={val:.2f}: {labels.get(name, 'Metric spike')}")
    return flags


SUMMARY_PROMPT = """You are an expert analyst. Given the following EDCM analysis of a transcript, write a concise, actionable summary report.

Context:
- {turn_count} turns analyzed across {speaker_count} speakers
- {flag_count} turns flagged for metric spikes
- Goal: {goal}
- Constraints: {constraints}

Flagged turns (with reasons):
{flagged_details}

Overall metrics:
{overall_metrics}

Write a professional summary that:
1. Highlights key findings and patterns
2. Identifies specific points of concern (contradictions, topic drift, imbalanced participation)
3. Provides actionable insights (e.g., for a lawyer: which statements conflict, for a manager: which participants are being sidelined)
4. Is formatted with clear headings and bullet points in markdown

Be specific — reference turn numbers and speakers by name."""


async def _generate_narrative(
    turns: List[TurnMetric], flagged: List[int],
    goal_text: str, constraints: List[str],
    summary_metrics: Dict[str, Any],
    model: str, user: dict, registry: dict,
) -> str:
    """Generate a narrative summary of the analysis using an LLM."""
    speakers = set(t.speaker for t in turns)
    flagged_details = []
    for idx in flagged:
        t = turns[idx]
        flagged_details.append(f"Turn {idx} ({t.speaker}): {t.content[:100]}... | Flags: {', '.join(t.flags)}")

    prompt = SUMMARY_PROMPT.format(
        turn_count=len(turns),
        speaker_count=len(speakers),
        flag_count=len(flagged),
        goal=goal_text or "Not specified",
        constraints=", ".join(constraints) if constraints else "None specified",
        flagged_details="\n".join(flagged_details) if flagged_details else "None",
        overall_metrics="\n".join(f"- {k}: {v.get('value', 0):.3f}" for k, v in summary_metrics.items()),
    )

    messages = [{"role": "user", "content": prompt}]
    full_response = ""
    async for chunk in generate_response(model, messages, f"summary_{uuid.uuid4().hex[:8]}", user, registry):
        full_response += chunk

    if full_response.startswith("[ERROR]"):
        return f"Summary generation failed: {full_response}"

    return full_response


# ---- Endpoints ----

@router.post("/transcript", response_model=AnalysisReport)
async def analyze_transcript(
    request: AnalysisRequest,
    current_user: dict = Depends(get_current_user),
):
    """Upload transcript text, parse with LLM, apply EDCM per turn, generate report."""
    user_id = get_user_id(current_user)
    analysis_id = f"ana_{uuid.uuid4().hex[:16]}"

    # Get user's registry
    custom = await db.model_registry.find_one({"user_id": user_id}, {"_id": 0})
    registry = reconcile_registry_developers(custom["developers"] if custom and custom.get("developers") else DEFAULT_REGISTRY)[0]

    # Step 1: Parse transcript into turns using LLM
    raw_turns = await _parse_transcript_with_llm(
        request.transcript_text, request.model, current_user, registry
    )

    if not raw_turns:
        raise HTTPException(status_code=400, detail="Could not parse any turns from transcript")

    # Step 2: Compute EDCM metrics per turn
    goal = request.goal_text or ""
    constraints = request.declared_constraints or []
    analyzed_turns: List[TurnMetric] = []
    flagged_indices: List[int] = []

    for i, turn in enumerate(raw_turns):
        metrics = _compute_turn_metrics(turn, raw_turns, i, goal, constraints)
        flags = _detect_flags(metrics)
        tm = TurnMetric(
            turn_index=i,
            speaker=turn.get("speaker", f"Speaker {i + 1}"),
            content=turn.get("content", ""),
            metrics=metrics,
            flags=flags,
        )
        analyzed_turns.append(tm)
        if flags:
            flagged_indices.append(i)

    # Step 3: Compute summary metrics (average across turns)
    summary = {}
    for metric_name in ["CM", "DA", "DRIFT", "DVG", "INT", "TBF"]:
        values = [t.metrics[metric_name]["value"] for t in analyzed_turns if metric_name in t.metrics]
        avg = sum(values) / len(values) if values else 0.0
        summary[metric_name] = {"value": round(avg, 4), "range": [0, 1]}

    # Step 4: Generate narrative summary with LLM
    narrative = await _generate_narrative(
        analyzed_turns, flagged_indices, goal, constraints,
        summary, request.model, current_user, registry,
    )

    title = request.transcript_text[:60].replace("\n", " ").strip()

    # Persist to DB
    report_doc = {
        "analysis_id": analysis_id,
        "user_id": user_id,
        "title": title,
        "created_at": _iso_now(),
        "model_used": request.model,
        "turn_count": len(analyzed_turns),
        "turns": [t.model_dump() for t in analyzed_turns],
        "summary_metrics": summary,
        "flagged_turns": flagged_indices,
        "narrative_summary": narrative,
        "transcript_text": request.transcript_text,
    }
    await db.analyses.insert_one(report_doc)

    await emit_event("action_result", f"analysis:{analysis_id}", f"user:{user_id}", {
        "type": "transcript_analysis",
        "analysis_id": analysis_id,
        "turn_count": len(analyzed_turns),
        "flag_count": len(flagged_indices),
        "model": request.model,
    })

    return AnalysisReport(
        analysis_id=analysis_id,
        title=title,
        created_at=report_doc["created_at"],
        model_used=request.model,
        turn_count=len(analyzed_turns),
        turns=analyzed_turns,
        summary_metrics=summary,
        flagged_turns=flagged_indices,
        narrative_summary=narrative,
        provenance=build_provenance(model=request.model),
    )


@router.post("/transcript/upload")
async def upload_transcript_file(
    file: UploadFile = File(...),
    model: str = Form("gpt-4o-mini"),
    goal_text: str = Form(""),
    declared_constraints: str = Form(""),
    current_user: dict = Depends(get_current_user),
):
    """Upload a transcript file (.txt, .md) for analysis."""
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    if len(text) < 10:
        raise HTTPException(status_code=400, detail="Transcript too short")

    constraints_list = [c.strip() for c in declared_constraints.split(",") if c.strip()] if declared_constraints else []

    req = AnalysisRequest(
        transcript_text=text,
        model=model,
        goal_text=goal_text,
        declared_constraints=constraints_list,
    )
    return await analyze_transcript(req, current_user)


@router.get("/reports")
async def list_reports(
    current_user: dict = Depends(get_current_user),
):
    """List all analysis reports for the current user."""
    user_id = get_user_id(current_user)
    reports = await db.analyses.find(
        {"user_id": user_id},
        {"_id": 0, "analysis_id": 1, "title": 1, "created_at": 1, "model_used": 1,
         "turn_count": 1, "flagged_turns": 1, "summary_metrics": 1},
    ).sort("created_at", -1).to_list(100)
    return reports


@router.get("/reports/{analysis_id}")
async def get_report(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a full analysis report."""
    user_id = get_user_id(current_user)
    report = await db.analyses.find_one(
        {"analysis_id": analysis_id, "user_id": user_id},
        {"_id": 0},
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
# ratios: loc_comments=277:20 imports_exports=14:7 calls_definitions=92:12
