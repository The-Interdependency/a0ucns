# ratios: loc_comments=106:49 imports_exports=6:10 calls_definitions=29:11
# === MODULE_BUILD ===
# id: skills_registry
#   module_name: registry
#   module_kind: engine
#   summary: per-user + global skill catalog with overlap detection — Skill schema (name, description, prompt_template, tool_bindings[], sentinel_overrides{}, scope_tokens[], logic_set_tokens[], source); jaccard-similarity overlap check against existing skills warns the user when a candidate skill shares logic+scope with one already in the catalog
#   owner: Erin Spencer
#   public_surface: Skill, SkillExistsWarning, register_skill, list_skills, get_skill, delete_skill, check_overlap, tokenize_scope, tokenize_logic
#   internal_surface: _jaccard
#   auth_boundary: bearer
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: write
#   admin_only: false
#   tests: a0p_skills.contracts.skills_registry_overlap_warns_holds
#   rollout: default_enabled
#   rollback: revert; skill catalog endpoint loses overlap detection
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: skills_registry_boundaries
#   summary: persists skill records to Mongo with overlap detection
#   auth_boundary: bearer
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: write
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: skills_registry
#   summary: skill registry + overlap detection
#   exposes: Skill, register_skill, list_skills, get_skill, delete_skill, check_overlap, tokenize_scope, tokenize_logic, SkillExistsWarning
#   boundaries: auth:bearer, storage:write, network:none, user_data:write
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: skills_registry_overlap_warns
#   given: two skill specs with overlapping scope_tokens and logic_set_tokens
#   then: check_overlap returns the higher-similarity match with score above
#         the threshold and the second register_skill call surfaces a warning
#   class: correctness
#   call: a0p_skills.contracts.skills_registry_overlap_warns_holds
# === END CONTRACTS ===
"""Skill catalog with overlap detection."""
from __future__ import annotations
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional


OVERLAP_THRESHOLD = 0.6   # jaccard similarity over (scope ∪ logic)


@dataclass
class Skill:
    id: str
    name: str
    description: str
    prompt_template: str
    tool_bindings: list[str]       # tool names (built-in or user/mcp/webhook)
    sentinel_overrides: dict       # {"S4": "observe", ...}
    scope_tokens: list[str]        # WHAT it applies to ("github", "scrape", "audit")
    logic_set_tokens: list[str]    # HOW it works ("summarize", "search", "compare")
    owner_user_id: Optional[str]   # None = global / from skill-lib repo
    source: str                    # "user" | "skill-lib" | "builtin"
    version: str = "1"
    created_at_ms: int = 0
    updated_at_ms: int = 0


class SkillExistsWarning(Exception):
    """Raised by register_skill when overlap_score >= threshold and the caller
    did not pass force=True."""

    def __init__(self, message: str, similar: list[dict]):
        super().__init__(message)
        self.similar = similar


def tokenize_scope(s: str) -> list[str]:
    return sorted(set(re.findall(r"[a-z0-9_]+", (s or "").lower())))


def tokenize_logic(s: str) -> list[str]:
    return tokenize_scope(s)


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


async def check_overlap(col, scope_tokens: list[str], logic_set_tokens: list[str],
                        user_id: Optional[str] = None) -> list[dict]:
    """Return existing skills whose combined-token jaccard is >= OVERLAP_THRESHOLD,
    sorted by descending score. Considers user-owned + global skills."""
    candidate = set(scope_tokens) | set(logic_set_tokens)
    if not candidate:
        return []
    q = {"$or": [{"owner_user_id": user_id}, {"owner_user_id": None}]} if user_id else {}
    matches: list[dict] = []
    async for d in col.find(q):
        existing = set(d.get("scope_tokens") or []) | set(d.get("logic_set_tokens") or [])
        if not existing:
            continue
        score = _jaccard(candidate, existing)
        if score >= OVERLAP_THRESHOLD:
            matches.append({
                "id": d["_id"], "name": d["name"], "source": d.get("source"),
                "owner_user_id": d.get("owner_user_id"), "score": round(score, 3),
                "description": d.get("description", "")[:200],
            })
    matches.sort(key=lambda m: m["score"], reverse=True)
    return matches


async def register_skill(col, *, user_id: str, name: str, description: str,
                          prompt_template: str, tool_bindings: list[str],
                          sentinel_overrides: Optional[dict] = None,
                          scope_tokens: Optional[list[str]] = None,
                          logic_set_tokens: Optional[list[str]] = None,
                          source: str = "user",
                          force: bool = False) -> Skill:
    """Insert a Skill. Raises SkillExistsWarning if an existing skill overlaps
    above threshold and ``force=False``."""
    scope_tokens = scope_tokens or tokenize_scope(name + " " + description)
    logic_set_tokens = logic_set_tokens or tokenize_logic(description)
    similar = await check_overlap(col, scope_tokens, logic_set_tokens, user_id=user_id)
    if similar and not force:
        raise SkillExistsWarning(
            f"a similar skill already exists: {similar[0]['name']} (score {similar[0]['score']})",
            similar=similar,
        )
    now = int(time.time() * 1000)
    sk = Skill(
        id=str(uuid.uuid4()),
        name=name, description=description,
        prompt_template=prompt_template,
        tool_bindings=list(tool_bindings or []),
        sentinel_overrides=dict(sentinel_overrides or {}),
        scope_tokens=scope_tokens, logic_set_tokens=logic_set_tokens,
        owner_user_id=(None if source != "user" else user_id),
        source=source, created_at_ms=now, updated_at_ms=now,
    )
    doc = asdict(sk); doc["_id"] = doc.pop("id")
    await col.insert_one(doc)
    return sk


async def list_skills(col, *, user_id: Optional[str] = None) -> list[Skill]:
    q = {"$or": [{"owner_user_id": user_id}, {"owner_user_id": None}]} if user_id else {}
    out: list[Skill] = []
    async for d in col.find(q).sort([("source", 1), ("name", 1)]):
        d["id"] = d.pop("_id")
        out.append(Skill(**d))
    return out


async def get_skill(col, skill_id: str) -> Optional[Skill]:
    d = await col.find_one({"_id": skill_id})
    if not d:
        return None
    d["id"] = d.pop("_id")
    return Skill(**d)


async def delete_skill(col, skill_id: str, user_id: str) -> bool:
    r = await col.delete_one({"_id": skill_id, "owner_user_id": user_id})
    return r.deleted_count == 1


__all__ = [
    "Skill", "SkillExistsWarning", "register_skill", "list_skills",
    "get_skill", "delete_skill", "check_overlap",
    "tokenize_scope", "tokenize_logic", "OVERLAP_THRESHOLD",
]
# ratios: loc_comments=106:49 imports_exports=6:10 calls_definitions=29:11
