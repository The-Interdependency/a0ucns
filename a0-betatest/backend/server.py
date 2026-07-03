# ratios: loc_comments=839:116 imports_exports=48:56 calls_definitions=306:65
# === MODULE_BUILD ===
# id: a0p_server
#   module_name: server
#   module_kind: route
#   summary: FastAPI app — keys, vault, inventory, sessions, drafts, chat (single/fanout/daisy/synth), inspector, agents, usage, skill report
#   owner: a0p maintainer
#   public_surface: app, api, AGENT
#   internal_surface: _call_model, _split_model, _get_key, _record_usage, _utc_now_iso
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: external
#   user_data_boundary: write
#   admin_only: false
#   tests: a0p_skills.contracts.skill_report_visibility_holds
#   rollout: default_enabled
#   rollback: supervisorctl stop backend; restore previous server.py from git
#   ui_surface: all frontend pages
#   api_surface: /api/*
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: a0p_server_boundaries
#   summary: FastAPI app — keys, vault, inventory, sessions, drafts, chat (single/fanout/daisy/synth), inspector, agents, usage, skill report
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: external
#   user_data_boundary: write
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: a0p_server
#   summary: FastAPI app — keys, vault, inventory, sessions, drafts, chat (single/fanout/daisy/synth), inspector, agents, usage, skill report
#   exposes: app, api, AGENT
#   boundaries: auth:none, storage:write, network:external, user_data:write
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""
a0p — research instrument backend.

Exposes:
  /api/health
  /api/keys                — BYOK key vault (encrypted at rest)
  /api/vault               — per-site multi-account .env vault
  /api/models/inventory    — model inventory per provider key
  /api/sessions            — chat sessions with editable context
  /api/drafts              — prompt drafts (autosave)
  /api/chat/single         — single-model chat
  /api/chat/fanout         — fan-out: one prompt → N models
  /api/chat/daisychain     — daisy-chain: A → B → ... N rounds
  /api/chat/synthesize     — synthesize a chosen set of responses
  /api/inspector/heartbeat — PCNA heartbeat (PTCA cores phi/psi/omega)
  /api/inspector/snapshot  — full engine snapshot
  /api/agents              — detachable agents library
  /api/usage               — token / compute usage log
"""
from __future__ import annotations
import os
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI, APIRouter, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any

from db import (
    keys_col, vault_col, sessions_col, drafts_col,
    fanout_col, chain_col, agents_col, usage_col, ensure_indexes,
)
from models import (
    KeyUpsert, KeyPublic,
    SiteAccountUpsert, SiteAccountPublic,
    SessionUpsert, SessionPublic, ChatTurn,
    DraftUpsert, DraftPublic,
    FanOutRequest, DaisyChainRequest, SynthesizeRequest,
    AgentExport,
    PROVIDERS, new_id,
)
import crypto_vault as cv
from providers import REGISTRY
from interdependent_lib.aimmh import fan_out as aimmh_fan_out, daisy_chain as aimmh_daisy
from interdependent_lib.zfae import ZFAEAgent, A0ZFAEInferenceEngine
from interdependent_lib._msdmd import report as msdmd_report
from a0p_skills import test_build_runner, module_build_runner
from a0p_skills import boundaries_runner, capabilities_runner, ratios_runner
from agents.routes import router as agents_router, init_routes as init_agents_routes
from interdependent_lib.zfae.runtime import ZFAERuntime
from interdependent_lib.zfae.teacher import TeacherClient
from interdependent_lib.zfae import (
    sentinel_modes as zfae_sentinel_modes,
    sentinel_weights as zfae_sentinel_weights,
    overrides as zfae_overrides,
    SENTINELS,
)
from interdependent_lib.gonal import registry as gonal_registry


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- app ----------
app = FastAPI(title="a0p — research instrument", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Append-only traffic log (metadata only — no bodies/headers/cookies/secrets).
from traffic_log import traffic_middleware
app.middleware("http")(traffic_middleware)

api = APIRouter(prefix="/api")


# ---------- shared persistent ZFAE agent ----------
AGENT = ZFAEAgent(name="a0(zfae)", base_seed=157)

# ---------- native a0(zfae) inference engine ----------
# This engine is the ONLY source of `assistantText` for /api/chat/zfae.
# It MUST NOT be replaced by an LLM provider. See its CONTRACTS.
A0_ZFAE_ENGINE = A0ZFAEInferenceEngine()


# ---------- health ----------
@api.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "a0p",
        "ts": _utc_now_iso(),
        "providers": list(REGISTRY.keys()),
        "agent": {"id": AGENT.id, "name": AGENT.name, "born_ms": AGENT.born_ms},
    }


# ---------- BYOK keys ----------
async def _auth_uid(request: Request, fallback: str = "local") -> str:
    """Resolve the acting user id from the auth cookie; fall back when unauth.

    The BYOK key vault, env vault and inventory are per authenticated user — the
    chat runtime looks keys up under the same id, so these routes must NOT trust
    the client-supplied ``user_id`` (which legacy clients hardcode to 'local').
    """
    from auth import get_current_user
    try:
        user = await get_current_user(request)
        return user["id"]
    except Exception:
        return fallback


@api.get("/keys")
async def list_keys(request: Request, user_id: str = "local"):
    user_id = await _auth_uid(request, user_id)
    out: list[KeyPublic] = []
    async for doc in keys_col.find({"user_id": user_id}).sort("provider", 1):
        try:
            plain = cv.decrypt(doc["enc_api_key"])
        except Exception:
            plain = ""
        out.append(KeyPublic(
            id=doc["_id"],
            user_id=doc["user_id"],
            provider=doc["provider"],
            label=doc.get("label"),
            masked=cv.mask(plain),
            has_key=bool(plain),
            last_used_at=doc.get("last_used_at"),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
        ).model_dump())
    return {"keys": out}


@api.put("/keys")
async def upsert_key(body: KeyUpsert, request: Request):
    uid = await _auth_uid(request, body.user_id)
    if body.provider not in PROVIDERS:
        raise HTTPException(400, f"provider must be one of {PROVIDERS}")
    if not body.api_key or len(body.api_key) < 8:
        raise HTTPException(400, "api_key looks invalid")
    now = _utc_now_iso()
    enc = cv.encrypt(body.api_key)
    existing = await keys_col.find_one({"user_id": uid, "provider": body.provider})
    if existing:
        await keys_col.update_one(
            {"_id": existing["_id"]},
            {"$set": {"enc_api_key": enc, "label": body.label, "updated_at": now}},
        )
        _id = existing["_id"]
    else:
        _id = new_id()
        await keys_col.insert_one({
            "_id": _id,
            "user_id": uid,
            "provider": body.provider,
            "label": body.label,
            "enc_api_key": enc,
            "created_at": now,
            "updated_at": now,
            "last_used_at": None,
        })
    return {"ok": True, "id": _id, "provider": body.provider, "masked": cv.mask(body.api_key)}


@api.delete("/keys/{key_id}")
async def delete_key(key_id: str, request: Request, user_id: str = "local"):
    user_id = await _auth_uid(request, user_id)
    r = await keys_col.delete_one({"_id": key_id, "user_id": user_id})
    return {"ok": r.deleted_count == 1}


async def _get_key(user_id: str, provider: str) -> str:
    doc = await keys_col.find_one({"user_id": user_id, "provider": provider})
    if not doc:
        return ""
    try:
        return cv.decrypt(doc["enc_api_key"])
    except Exception:
        return ""


# ---------- Site .env vault ----------
@api.get("/vault")
async def list_vault(request: Request, user_id: str = "local"):
    user_id = await _auth_uid(request, user_id)
    out: list[SiteAccountPublic] = []
    async for doc in vault_col.find({"user_id": user_id}).sort([("site", 1), ("account_label", 1)]):
        # do not return encrypted values; just keys
        env_keys = list((doc.get("enc_env") or {}).keys())
        out.append(SiteAccountPublic(
            id=doc["_id"],
            user_id=doc["user_id"],
            site=doc["site"],
            account_label=doc["account_label"],
            env_keys=env_keys,
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
        ).model_dump())
    return {"accounts": out}


@api.put("/vault")
async def upsert_vault(body: SiteAccountUpsert, request: Request):
    uid = await _auth_uid(request, body.user_id)
    now = _utc_now_iso()
    enc_env = {k: cv.encrypt(v) for k, v in body.env.items() if v}
    existing = await vault_col.find_one({"user_id": uid, "site": body.site, "account_label": body.account_label})
    if existing:
        merged = {**(existing.get("enc_env") or {}), **enc_env}
        await vault_col.update_one(
            {"_id": existing["_id"]},
            {"$set": {"enc_env": merged, "updated_at": now}},
        )
        _id = existing["_id"]
    else:
        _id = new_id()
        await vault_col.insert_one({
            "_id": _id,
            "user_id": uid,
            "site": body.site,
            "account_label": body.account_label,
            "enc_env": enc_env,
            "created_at": now,
            "updated_at": now,
        })
    return {"ok": True, "id": _id, "site": body.site, "account_label": body.account_label,
            "env_keys": list(enc_env.keys())}


class VaultRevealRequest(BaseModel):
    user_id: str = "local"
    id: str
    keys: List[str]


@api.post("/vault/reveal")
async def reveal_vault(body: VaultRevealRequest, request: Request):
    uid = await _auth_uid(request, body.user_id)
    doc = await vault_col.find_one({"_id": body.id, "user_id": uid})
    if not doc:
        raise HTTPException(404, "vault entry not found")
    env = doc.get("enc_env") or {}
    return {"values": {k: cv.decrypt(env[k]) for k in body.keys if k in env}}


@api.delete("/vault/{vault_id}")
async def delete_vault(vault_id: str, request: Request, user_id: str = "local"):
    user_id = await _auth_uid(request, user_id)
    r = await vault_col.delete_one({"_id": vault_id, "user_id": user_id})
    return {"ok": r.deleted_count == 1}


# ---------- Model inventory ----------
@api.get("/models/inventory")
async def model_inventory(request: Request, user_id: str = "local"):
    """Aggregate live model inventory across BYOK providers the user has keys for."""
    user_id = await _auth_uid(request, user_id)
    inv: list[dict] = []
    errors: dict[str, str] = {}

    # For each provider the user has a key for, fetch live inventory.
    # No platform-bundled inventory — this build is BYOK-only.
    async for doc in keys_col.find({"user_id": user_id}):
        prov = doc["provider"]
        try:
            plain = cv.decrypt(doc["enc_api_key"])
        except Exception:
            continue
        if not plain:
            continue
        try:
            models = await REGISTRY[prov].list_models(plain)
            inv.extend(models)
        except Exception as e:
            errors[prov] = str(e)[:200]

    return {"models": inv, "errors": errors, "count": len(inv)}


# ---------- Sessions (editable context) ----------
@api.get("/sessions")
async def list_sessions(request: Request, user_id: str = "local"):
    user_id = await _auth_uid(request, user_id)
    out = []
    async for d in sessions_col.find({"user_id": user_id}).sort("updated_at", -1).limit(50):
        out.append({
            "id": d["_id"],
            "user_id": d["user_id"],
            "title": d.get("title"),
            "system_context": d.get("system_context", ""),
            "persona": d.get("persona"),
            "selected_models": d.get("selected_models", []),
            "turns_count": len(d.get("turns", [])),
            "created_at": d.get("created_at"),
            "updated_at": d.get("updated_at"),
        })
    return {"sessions": out}


@api.post("/sessions")
async def create_session(body: SessionUpsert, request: Request):
    uid = await _auth_uid(request, body.user_id)
    now = _utc_now_iso()
    _id = new_id()
    doc = {
        "_id": _id,
        "user_id": uid,
        "title": body.title or f"session-{_id[:8]}",
        "system_context": body.system_context or "",
        "persona": body.persona,
        "selected_models": body.selected_models,
        "metadata": body.metadata,
        "turns": [],
        "created_at": now,
        "updated_at": now,
    }
    await sessions_col.insert_one(doc)
    return {"id": _id, **{k: v for k, v in doc.items() if k != "_id"}}


@api.get("/sessions/{session_id}")
async def get_session(session_id: str, user_id: str = "local"):
    d = await sessions_col.find_one({"_id": session_id, "user_id": user_id})
    if not d:
        raise HTTPException(404, "session not found")
    return {**d, "id": d.pop("_id")}


@api.patch("/sessions/{session_id}")
async def update_session(session_id: str, body: SessionUpsert, request: Request):
    uid = await _auth_uid(request, body.user_id)
    now = _utc_now_iso()
    upd = {
        "title": body.title,
        "system_context": body.system_context,
        "persona": body.persona,
        "selected_models": body.selected_models,
        "metadata": body.metadata,
        "updated_at": now,
    }
    upd = {k: v for k, v in upd.items() if v is not None or k == "updated_at"}
    r = await sessions_col.update_one(
        {"_id": session_id, "user_id": uid},
        {"$set": upd},
    )
    if r.matched_count == 0:
        raise HTTPException(404, "session not found")
    return {"ok": True}


@api.delete("/sessions/{session_id}")
async def delete_session(session_id: str, request: Request, user_id: str = "local"):
    user_id = await _auth_uid(request, user_id)
    r = await sessions_col.delete_one({"_id": session_id, "user_id": user_id})
    return {"ok": r.deleted_count == 1}


# ---------- Drafts ----------
@api.get("/drafts")
async def list_drafts(request: Request, user_id: str = "local"):
    user_id = await _auth_uid(request, user_id)
    out = []
    async for d in drafts_col.find({"user_id": user_id}).sort("updated_at", -1).limit(100):
        out.append({"id": d["_id"], **{k: d[k] for k in d if k != "_id"}})
    return {"drafts": out}


@api.post("/drafts")
async def create_draft(body: DraftUpsert, request: Request):
    uid = await _auth_uid(request, body.user_id)
    now = _utc_now_iso()
    _id = new_id()
    doc = {
        "_id": _id,
        "user_id": uid,
        "title": body.title,
        "content": body.content,
        "tags": body.tags,
        "created_at": now,
        "updated_at": now,
    }
    await drafts_col.insert_one(doc)
    return {"id": _id, **{k: v for k, v in doc.items() if k != "_id"}}


@api.patch("/drafts/{draft_id}")
async def update_draft(draft_id: str, body: DraftUpsert, request: Request):
    uid = await _auth_uid(request, body.user_id)
    now = _utc_now_iso()
    upd = {k: v for k, v in body.model_dump().items() if k != "user_id"}
    upd["updated_at"] = now
    r = await drafts_col.update_one(
        {"_id": draft_id, "user_id": uid},
        {"$set": upd},
    )
    if r.matched_count == 0:
        raise HTTPException(404, "draft not found")
    return {"ok": True}


@api.delete("/drafts/{draft_id}")
async def delete_draft(draft_id: str, request: Request, user_id: str = "local"):
    user_id = await _auth_uid(request, user_id)
    r = await drafts_col.delete_one({"_id": draft_id, "user_id": user_id})
    return {"ok": r.deleted_count == 1}


# ---------- Chat plumbing ----------
def _split_model(model_id: str) -> tuple[str, str]:
    """'provider:name' → (provider, name). For 'emergent', name keeps 'sub:model'."""
    if ":" not in model_id:
        raise HTTPException(400, f"model_id must be 'provider:name', got {model_id!r}")
    prov, rest = model_id.split(":", 1)
    return prov, rest


async def _call_model(
    user_id: str,
    model_id: str,
    messages: list[dict],
    system: str | None,
) -> dict:
    prov, name = _split_model(model_id)

    if prov not in REGISTRY:
        return {"content": "", "error": f"unknown provider {prov!r}",
                "model_id": model_id, "provider": prov}

    key = await _get_key(user_id, prov)
    if not key:
        return {
            "content": "",
            "error": (
                f"no api key for provider {prov!r}; add one in the Key Vault. "
                f"This build is BYOK-only — no platform fallback."
            ),
            "model_id": model_id,
            "provider": prov,
        }

    adapter = REGISTRY[prov]
    result = await adapter.chat(key, name, messages, system=system)
    await keys_col.update_one({"user_id": user_id, "provider": prov},
                              {"$set": {"last_used_at": _utc_now_iso()}})
    return {**result, "routed_via": prov}


async def _record_usage(user_id: str, model_id: str, usage: dict, kind: str):
    await usage_col.insert_one({
        "_id": new_id(),
        "user_id": user_id,
        "model_id": model_id,
        "kind": kind,
        "usage": usage or {},
        "created_at": _utc_now_iso(),
    })


# ---------- Single-model chat ----------
class SingleChatRequest(BaseModel):
    user_id: str = "local"
    model_id: str
    messages: list[dict]
    system: Optional[str] = ""
    session_id: Optional[str] = None


@api.post("/chat/single")
async def chat_single(body: SingleChatRequest):
    AGENT.receive((body.messages[-1]["content"] if body.messages else "") or "")
    r = await _call_model(
        user_id=body.user_id,
        model_id=body.model_id,
        messages=body.messages,
        system=body.system or None,
    )
    AGENT.absorb(body.model_id, r.get("content", ""), r.get("usage"))
    await _record_usage(body.user_id, body.model_id, r.get("usage", {}), "single")

    if body.session_id:
        turn_user = ChatTurn(role="user", content=body.messages[-1]["content"]).model_dump() if body.messages else None
        turn_asst = ChatTurn(role="assistant", content=r.get("content", ""), model_id=body.model_id, usage=r.get("usage", {})).model_dump()
        push_turns = [t for t in [turn_user, turn_asst] if t]
        await sessions_col.update_one(
            {"_id": body.session_id, "user_id": body.user_id},
            {"$push": {"turns": {"$each": push_turns}},
             "$set": {"updated_at": _utc_now_iso()}},
        )
    return {"result": r, "agent_tick": AGENT.engine.tick_count}


# ---------- Fan-out ----------
@api.post("/chat/fanout")
async def chat_fanout(body: FanOutRequest):
    AGENT.receive(body.prompt)
    messages = [{"role": "user", "content": body.prompt}]
    system = body.system_context or None

    async def call_fn(model_id: str, msgs: list[dict]):
        return await _call_model(body.user_id, model_id, msgs, system)

    results = await aimmh_fan_out(call_fn, body.model_ids, messages)

    # absorb + persist
    run_id = new_id()
    record = {
        "_id": run_id,
        "user_id": body.user_id,
        "session_id": body.session_id,
        "prompt": body.prompt,
        "system_context": body.system_context,
        "results": [{
            "model_id": r.model_id,
            "content": r.content,
            "usage": r.usage,
            "error": r.error,
        } for r in results],
        "created_at": _utc_now_iso(),
    }
    await fanout_col.insert_one(record)

    for r in results:
        AGENT.absorb(r.model_id, r.content, r.usage)
        await _record_usage(body.user_id, r.model_id, r.usage or {}, "fanout")

    if body.session_id:
        turns = [ChatTurn(role="user", content=body.prompt).model_dump()]
        for r in results:
            turns.append(ChatTurn(role="assistant", content=r.content,
                                  model_id=r.model_id, usage=r.usage).model_dump())
        await sessions_col.update_one(
            {"_id": body.session_id, "user_id": body.user_id},
            {"$push": {"turns": {"$each": turns}},
             "$set": {"updated_at": _utc_now_iso()}},
        )

    return {
        "run_id": run_id,
        "results": record["results"],
        "agent_tick": AGENT.engine.tick_count,
    }


# ---------- Daisy chain ----------
@api.post("/chat/daisychain")
async def chat_daisychain(body: DaisyChainRequest):
    AGENT.receive(body.prompt)
    messages = [{"role": "user", "content": body.prompt}]
    system = body.system_context or None
    rounds = max(1, min(body.rounds, 6))

    async def call_fn(model_id: str, msgs: list[dict]):
        return await _call_model(body.user_id, model_id, msgs, system)

    results = await aimmh_daisy(call_fn, body.model_ids, messages, rounds=rounds)

    run_id = new_id()
    serialised = [{
        "step": i + 1,
        "model_id": r.model_id,
        "content": r.content,
        "usage": r.usage,
        "error": r.error,
    } for i, r in enumerate(results)]
    await chain_col.insert_one({
        "_id": run_id,
        "user_id": body.user_id,
        "session_id": body.session_id,
        "prompt": body.prompt,
        "system_context": body.system_context,
        "rounds": rounds,
        "model_ids": body.model_ids,
        "steps": serialised,
        "created_at": _utc_now_iso(),
    })

    for r in results:
        AGENT.absorb(r.model_id, r.content, r.usage)
        await _record_usage(body.user_id, r.model_id, r.usage or {}, "daisy")

    if body.session_id:
        turns = [ChatTurn(role="user", content=body.prompt).model_dump()]
        for r in results:
            turns.append(ChatTurn(role="assistant", content=r.content,
                                  model_id=r.model_id, usage=r.usage).model_dump())
        await sessions_col.update_one(
            {"_id": body.session_id, "user_id": body.user_id},
            {"$push": {"turns": {"$each": turns}},
             "$set": {"updated_at": _utc_now_iso()}},
        )

    return {"run_id": run_id, "steps": serialised, "agent_tick": AGENT.engine.tick_count}


# ---------- Synthesize selected responses ----------
@api.post("/chat/synthesize")
async def chat_synthesize(body: SynthesizeRequest):
    panel = "\n\n".join(f"[{r.get('model_id')}]:\n{r.get('content','')}" for r in body.responses)
    synth_prompt = (
        "You are the synthesizer. Below are responses from multiple models to the same prompt. "
        "Synthesize them into a single cohesive, accurate answer that incorporates the strongest reasoning "
        "from each. Note any disagreements explicitly.\n\n"
        f"ORIGINAL PROMPT:\n{body.prompt}\n\nMODEL RESPONSES:\n{panel}\n\nSYNTHESIS:"
    )
    r = await _call_model(
        user_id=body.user_id,
        model_id=body.synth_model,
        messages=[{"role": "user", "content": synth_prompt}],
        system=None,
    )
    AGENT.absorb(body.synth_model, r.get("content", ""), r.get("usage"))
    await _record_usage(body.user_id, body.synth_model, r.get("usage", {}), "synthesis")
    return {"synthesis": r}


# ---------- Inspector (PCNA / PTCA / EDCM / Memory) ----------
@api.get("/inspector/snapshot")
async def inspector_snapshot():
    return {
        "agent_card": AGENT.card(),
    }


@api.post("/inspector/heartbeat")
async def inspector_heartbeat(intent: Optional[str] = Body(default=None, embed=True)):
    return AGENT.engine.heartbeat(intent=intent)


# ---------- Detachable Agents ----------
@api.get("/agents")
async def list_agents():
    out = []
    async for d in agents_col.find({}).sort("created_at", -1):
        out.append({"id": d["_id"], **{k: d[k] for k in d if k != "_id"}})
    return {"agents": out}


@api.post("/agents")
async def create_agent(body: AgentExport):
    existing = await agents_col.find_one({"slug": body.slug})
    if existing:
        raise HTTPException(409, "slug already exists")
    _id = new_id()
    now = _utc_now_iso()
    doc = {"_id": _id, **body.model_dump(), "created_at": now, "updated_at": now}
    await agents_col.insert_one(doc)
    return {"id": _id, **{k: v for k, v in doc.items() if k != "_id"}}


@api.get("/agents/{slug}/manifest")
async def agent_manifest(slug: str):
    d = await agents_col.find_one({"slug": slug})
    if not d:
        raise HTTPException(404, "agent not found")
    manifest = {
        "manifest_version": "a0p-agent-v0",
        "slug": d["slug"],
        "name": d["name"],
        "description": d.get("description", ""),
        "system_context": d.get("system_context", ""),
        "persona": d.get("persona", ""),
        "default_models": d.get("default_models", []),
        "capabilities": d.get("capabilities", []),
        "aimmh_pattern": d.get("aimmh_pattern", "fan_out"),
        "rounds": d.get("rounds", 1),
        "tier": "premium" if d.get("is_premium") else "free",
        "exported_at": _utc_now_iso(),
    }
    return manifest


@api.delete("/agents/{slug}")
async def delete_agent(slug: str):
    r = await agents_col.delete_one({"slug": slug})
    return {"ok": r.deleted_count == 1}


# ---------- Usage log ----------
@api.get("/usage")
async def list_usage(request: Request, user_id: str = "local", limit: int = 100):
    user_id = await _auth_uid(request, user_id)
    out = []
    async for d in usage_col.find({"user_id": user_id}).sort("created_at", -1).limit(limit):
        out.append({"id": d["_id"], **{k: d[k] for k in d if k != "_id"}})
    agg = {"total_tokens": 0, "calls": 0, "by_provider": {}, "by_model": {}}
    for u in out:
        agg["calls"] += 1
        t = (u.get("usage") or {}).get("total", 0) or 0
        agg["total_tokens"] += t
        prov = (u.get("model_id") or "").split(":", 1)[0] or "unknown"
        agg["by_provider"][prov] = agg["by_provider"].get(prov, 0) + t
        agg["by_model"][u.get("model_id", "?")] = agg["by_model"].get(u.get("model_id", "?"), 0) + t
    return {"records": out, "aggregate": agg}


# ---------- msdmd skill coverage ----------
# === CONTRACTS ===
# id: skill_report_visibility
#   given: GET /api/skill/<name>/report for any of capabilities|contracts|module-build
#   then: returns scanned/covered/gaps_count plus the gaps array; gaps array MUST be present per msdmd doctrine
#   class: observability
#   call: a0p_skills.contracts.skill_report_visibility_holds
# === END CONTRACTS ===
@api.get("/skill/capabilities/report")
async def skill_capabilities_report(block: str = "CAPABILITIES"):
    """Legacy CAPABILITIES coverage report (deprecated; here for migration view)."""
    from pathlib import Path
    return msdmd_report(Path("/app/backend"), block)


@api.get("/skill/contracts/report")
async def skill_contracts_report():
    """test-build runner — imports each CONTRACTS `call:` path and runs it."""
    from pathlib import Path
    rep = await test_build_runner.run_async(Path("/app/backend"))
    return rep


@api.get("/skill/module-build/report")
async def skill_module_build_report():
    """meta-module-build runner — validates MODULE_BUILD schema + gap list."""
    from pathlib import Path
    return module_build_runner.run(Path("/app/backend"))


@api.get("/skill/report")
async def skill_report_legacy(block: str = "CAPABILITIES"):
    """Back-compat alias for /skill/capabilities/report."""
    from pathlib import Path
    return msdmd_report(Path("/app/backend"), block)


# ---------- Skill coverage runners — additional (Tier 5) -----------------
@api.get("/skill/boundaries/report")
async def skill_boundaries_report():
    from pathlib import Path
    return boundaries_runner.run(Path("/app/backend"))


@api.get("/skill/capabilities/report")
async def skill_capabilities_report_v2():
    from pathlib import Path
    return capabilities_runner.run(Path("/app/backend"))


@api.get("/skill/ratios/report")
async def skill_ratios_report():
    from pathlib import Path
    return ratios_runner.run(Path("/app/backend"))


@api.get("/skill/all/report")
async def skill_all_report():
    """Roll-up across all skill runners."""
    from pathlib import Path
    root = Path("/app/backend")
    return {
        "module-build": module_build_runner.run(root),
        "boundaries": boundaries_runner.run(root),
        "capabilities": capabilities_runner.run(root),
        "ratios": ratios_runner.run(root),
        "contracts": await test_build_runner.run_async(root),
    }


app.include_router(api)

# ---------- Auth (JWT + Emergent Google + GitHub OAuth) ----------
from auth import init_auth as _init_auth, get_current_user_or_demo
_init_auth(app)

# ---------- API extensions: custom keys vault, demo quota, living spec ----
from api_extensions import router as _ext_router
app.include_router(_ext_router)

# ---------- Tools / MCP (server + client) / Skills ----------
from api_tools_mcp_skills import router as _tools_router
from tools.mcp_server import router as _mcp_server_router
from app_settings import router as _settings_router
app.include_router(_tools_router)
app.include_router(_mcp_server_router)
app.include_router(_settings_router)


# ---------- Agents (Tier 3): /api/instances/* + /api/chat/instance/{id} ----
from db import agent_instances_col, pending_overrides_col, fiq_audit_col

_TEACHER_CLIENT = TeacherClient(REGISTRY, _get_key)
_ZFAE_RUNTIME = ZFAERuntime(
    teacher_client=_TEACHER_CLIENT,
    pending_overrides_col=pending_overrides_col,
    fiq_audit_col=fiq_audit_col,
    get_key_fn=_get_key,
)
init_agents_routes(agent_instances_col, runtime=_ZFAE_RUNTIME, get_key_fn=_get_key)
app.include_router(agents_router, prefix="/api")


# ---------- Sentinel modes + weights endpoints ----------
sentinels_api = APIRouter(prefix="/api")


@sentinels_api.get("/sentinels/canon")
async def sentinels_canon():
    """The 13 sentinels — names, cuts, cliff flags. Read-only canon."""
    return {
        "count": len(SENTINELS),
        "sentinels": [
            {
                "name": s.name, "title": s.title, "cut": s.cut,
                "cliff": s.cliff, "structural": s.structural, "plane": s.plane,
            }
            for s in SENTINELS
        ],
        "defaults": {
            "modes": {k: v.value for k, v in zfae_sentinel_modes.SENTINEL_MODES_DEFAULT.items()},
            "weights": zfae_sentinel_weights.SENTINEL_WEIGHTS_DEFAULT,
            "inference_channel_default": zfae_sentinel_weights.INFERENCE_CHANNEL_DEFAULT,
        },
    }


@sentinels_api.get("/instances/{agent_id}/sentinel-modes")
async def get_sentinel_modes(agent_id: str, request: Request, user_id: str = "local"):
    user_id = await _auth_uid(request, user_id)
    doc = await agent_instances_col.find_one({"_id": agent_id, "user_id": user_id})
    if not doc:
        raise HTTPException(404, f"agent {agent_id} not found")
    overrides = (doc.get("sheet") or {}).get("sentinel_modes") or {}
    resolved = zfae_sentinel_modes.resolve_modes(overrides)
    return {
        "agent_id": agent_id,
        "modes": {k: v.value for k, v in resolved.items()},
        "overrides": overrides,
    }


class SentinelModesPatch(BaseModel):
    user_id: str = "local"
    modes: dict[str, str] = {}


@sentinels_api.patch("/instances/{agent_id}/sentinel-modes")
async def patch_sentinel_modes(agent_id: str, body: SentinelModesPatch, request: Request):
    uid = await _auth_uid(request, body.user_id)
    try:
        zfae_sentinel_modes.validate_modes(body.modes)
    except ValueError as e:
        raise HTTPException(400, str(e))
    r = await agent_instances_col.update_one(
        {"_id": agent_id, "user_id": uid},
        {"$set": {"sheet.sentinel_modes": body.modes, "updated_at": _utc_now_iso()}},
    )
    if r.matched_count == 0:
        raise HTTPException(404, f"agent {agent_id} not found")
    return {"ok": True, "modes": body.modes}


class SentinelBulkMode(BaseModel):
    user_id: str = "local"
    mode: str = "observe"


@sentinels_api.post("/instances/{agent_id}/sentinel-modes/bulk")
async def bulk_sentinel_modes(agent_id: str, body: SentinelBulkMode, request: Request):
    uid = await _auth_uid(request, body.user_id)
    try:
        bulk = zfae_sentinel_modes.bulk_set(body.mode)
    except ValueError as e:
        raise HTTPException(400, str(e))
    modes = {k: v.value for k, v in bulk.items()}
    r = await agent_instances_col.update_one(
        {"_id": agent_id, "user_id": uid},
        {"$set": {"sheet.sentinel_modes": modes, "updated_at": _utc_now_iso()}},
    )
    if r.matched_count == 0:
        raise HTTPException(404, f"agent {agent_id} not found")
    return {"ok": True, "applied": body.mode, "modes": modes}


@sentinels_api.get("/instances/{agent_id}/sentinel-weights")
async def get_sentinel_weights(agent_id: str, request: Request, user_id: str = "local"):
    user_id = await _auth_uid(request, user_id)
    doc = await agent_instances_col.find_one({"_id": agent_id, "user_id": user_id})
    if not doc:
        raise HTTPException(404, f"agent {agent_id} not found")
    overrides = (doc.get("sheet") or {}).get("sentinel_weights") or {}
    mode_overrides = (doc.get("sheet") or {}).get("sentinel_modes") or {}
    resolved_weights = zfae_sentinel_weights.resolve_weights(overrides)
    resolved_modes = zfae_sentinel_modes.resolve_modes(mode_overrides)
    ic = zfae_sentinel_weights.inference_channel(resolved_weights, resolved_modes)
    return {
        "agent_id": agent_id,
        "weights": resolved_weights,
        "overrides": overrides,
        "inference_channel": ic,
    }


class SentinelWeightsPatch(BaseModel):
    user_id: str = "local"
    weights: dict[str, float] = {}


@sentinels_api.patch("/instances/{agent_id}/sentinel-weights")
async def patch_sentinel_weights(agent_id: str, body: SentinelWeightsPatch, request: Request):
    uid = await _auth_uid(request, body.user_id)
    try:
        zfae_sentinel_weights.validate_weights(body.weights)
    except ValueError as e:
        raise HTTPException(400, str(e))
    r = await agent_instances_col.update_one(
        {"_id": agent_id, "user_id": uid},
        {"$set": {"sheet.sentinel_weights": body.weights, "updated_at": _utc_now_iso()}},
    )
    if r.matched_count == 0:
        raise HTTPException(404, f"agent {agent_id} not found")
    return {"ok": True, "weights": body.weights}


# ---------- Pending overrides endpoints ----------
@sentinels_api.get("/overrides")
async def list_overrides(request: Request, user_id: str = "local", status: str = "pending", limit: int = 100):
    user_id = await _auth_uid(request, user_id)
    if status == "pending":
        records = await zfae_overrides.list_pending(pending_overrides_col, user_id=user_id, limit=limit)
        return {"overrides": [r.__dict__ for r in records], "count": len(records)}
    out = []
    async for doc in pending_overrides_col.find(
        {"user_id": user_id, "status": status}
    ).sort("created_ms", -1).limit(limit):
        doc.setdefault("id", doc.pop("_id", None))
        out.append(doc)
    return {"overrides": out, "count": len(out)}


@sentinels_api.get("/overrides/{override_id}")
async def get_override(override_id: str):
    rec = await zfae_overrides.get(pending_overrides_col, override_id)
    if rec is None:
        raise HTTPException(404, f"override {override_id} not found")
    return rec.__dict__


class OverrideApprove(BaseModel):
    user_id: str = "local"
    justification: str = ""


@sentinels_api.post("/overrides/{override_id}/approve")
async def approve_override(override_id: str, body: OverrideApprove, request: Request):
    uid = await _auth_uid(request, body.user_id)
    rec = await zfae_overrides.approve(pending_overrides_col, override_id, uid, body.justification)
    if rec is None:
        raise HTTPException(404, f"override {override_id} not found or not pending")
    return {"ok": True, "status": rec.status, "id": rec.id, "resolved_ms": rec.resolved_ms}


class OverrideReject(BaseModel):
    user_id: str = "local"
    reason: str = ""


@sentinels_api.post("/overrides/{override_id}/reject")
async def reject_override(override_id: str, body: OverrideReject, request: Request):
    uid = await _auth_uid(request, body.user_id)
    rec = await zfae_overrides.reject(pending_overrides_col, override_id, uid, body.reason)
    if rec is None:
        raise HTTPException(404, f"override {override_id} not found or not pending")
    return {"ok": True, "status": rec.status, "id": rec.id, "resolved_ms": rec.resolved_ms}


@sentinels_api.post("/overrides/expire")
async def expire_overrides():
    n = await zfae_overrides.expire(pending_overrides_col)
    return {"expired": n}


# ---------- Gonal registry endpoint (public counts only) ----------
@sentinels_api.get("/gonals")
async def list_gonals():
    """Three named gonals. Default+mirror are public; private is per-agent and not enumerated here."""
    from interdependent_lib.gonal.gonal import validate_gonal, GonalSpec
    default = gonal_registry.get_default()
    mirror = gonal_registry.get_mirror()
    spec = GonalSpec()
    return {
        "gonals": [
            {"name": "default", "n": len(default), "counts": validate_gonal(default, spec)["counts"], "is_public": True},
            {"name": "mirror",  "n": len(mirror),  "counts": validate_gonal(mirror, spec)["counts"],  "is_public": True},
            {"name": "private", "n": "hmmm",        "counts": "hmmm",                                   "is_public": False},
        ],
    }


app.include_router(sentinels_api)


# ---------- startup ----------
@app.on_event("startup")
async def _on_startup():
    await ensure_indexes()
    # Seed admin from .env (idempotent)
    from auth import seed_admin
    admin = await seed_admin()
    # Migrate legacy user_id='local' agents to the admin user (idempotent).
    if admin and admin.get("_id"):
        from db import agent_instances_col as _ai
        r = await _ai.update_many(
            {"user_id": "local"}, {"$set": {"user_id": admin["_id"]}},
        )
        if r.modified_count:
            import logging as _lg
            _lg.getLogger("a0p").info("migrated %d legacy local agents to admin", r.modified_count)
        # Migrate legacy user_id='local' BYOK keys + env vault to admin so the
        # authenticated chat runtime can find them (idempotent). Avoid clobbering
        # an existing admin key for the same provider.
        for _col, _label in ((keys_col, "byok keys"), (vault_col, "vault entries")):
            _moved = 0
            async for _doc in _col.find({"user_id": "local"}):
                _q = {"user_id": admin["_id"], "provider": _doc.get("provider")} \
                    if _label == "byok keys" else \
                    {"user_id": admin["_id"], "site": _doc.get("site"),
                     "account_label": _doc.get("account_label")}
                if await _col.find_one(_q):
                    continue  # admin already has this one; leave the local orphan
                await _col.update_one({"_id": _doc["_id"]},
                                      {"$set": {"user_id": admin["_id"]}})
                _moved += 1
            if _moved:
                import logging as _lgk
                _lgk.getLogger("a0p").info("migrated %d legacy local %s to admin", _moved, _label)
    # Regenerate README.md from the living spec
    try:
        from readme_writer import write_readme
        n = write_readme()
        import logging as _lg2
        _lg2.getLogger("a0p").info("README.md regenerated from %d living-spec modules", n)
    except Exception as _e:
        import logging as _lg3
        _lg3.getLogger("a0p").warning("README regeneration failed: %s", _e)
    # Seed a few starter detachable agents if the collection is empty.
    n = await agents_col.count_documents({})
    if n == 0:
        starters: list[AgentExport] = [
            AgentExport(slug="research-council", name="Research Council",
                        description="Three frontier models confer on a question, then each synthesizes the panel's view. BYOK: add keys for OpenAI / Anthropic / Google.",
                        system_context="You are a careful, source-aware research assistant. Cite reasoning steps explicitly.",
                        default_models=["openai:gpt-4o", "anthropic:claude-sonnet-4-5-20250929", "gemini:gemini-2.5-flash"],
                        capabilities=["math", "literature", "synthesis"],
                        aimmh_pattern="council", rounds=1, is_premium=False),
            AgentExport(slug="daisy-prover", name="Daisy Prover",
                        description="Two models pass a proof attempt back and forth, refining each round. BYOK: OpenAI + Anthropic.",
                        system_context="You are a rigorous mathematical prover. Critique the prior step before extending it.",
                        default_models=["openai:gpt-4o", "anthropic:claude-sonnet-4-5-20250929"],
                        capabilities=["proofs", "critique"],
                        aimmh_pattern="daisy_chain", rounds=3, is_premium=False),
            AgentExport(slug="zfae-classic", name="ZFAE Classic (Φ Ψ Ω)",
                        description="Single persistent agent over the PTCA(157) phi/psi/omega cores. BYOK: OpenAI.",
                        system_context="You are ZFAE — the zeta-function alpha-echo agent. Be exploratory and link concepts.",
                        default_models=["openai:gpt-4o-mini"],
                        capabilities=["exploration", "linking"],
                        aimmh_pattern="fan_out", rounds=1, is_premium=False),
            AgentExport(slug="premium-symphony", name="Premium · Symphony",
                        description="(Coming soon) — Six-model orchestrated round with PCNA-EDCM scoring loop.",
                        system_context="",
                        default_models=[],
                        capabilities=["pcna-edcm", "scoring"],
                        aimmh_pattern="room_synthesized", rounds=3, is_premium=True),
        ]
        now = _utc_now_iso()
        for a in starters:
            await agents_col.insert_one({"_id": new_id(), **a.model_dump(),
                                         "created_at": now, "updated_at": now})
# ratios: loc_comments=839:116 imports_exports=48:56 calls_definitions=306:65
