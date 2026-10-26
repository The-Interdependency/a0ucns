# ratios: loc_comments=250:85 imports_exports=7:9 calls_definitions=50:11
# === MODULE_BUILD ===
# id: api_agent_lab_routes
#   module_name: agent_lab
#   module_kind: route
#   summary: the Agent Creation Lab — a composer that lets a user assemble ANY permutation of the agent-creation logic explored across the a0 family and get back a validated, ordered execution plan. GET /api/agent-lab/permutations returns the full catalogue of creation stages (identity/mode from the 6-lattice, instance create + fresh three-core ZFAE weight bank, multi-teacher distill unlock, native-readiness gate, mode inference, sentinel/override config, volatile MemoryCore sub-instancing, safetensors checkpoint) plus the a0-canonical merge strategies (InstanceMerge fork/absorb/converge, sub_agent_spawn/executor) each tagged native vs cross-repo with its real entrypoint. POST /api/agent-lab/identity-preview composes the canonical a0(<energy>)<auditor> name. POST /api/agent-lab/plan validates a chosen recipe and returns the ordered steps, each mapped to the REAL route/primitive it executes against (or flagged plan-only for the _legacy_a0-only strategies) with preconditions + firewalls. POST /api/agent-lab/sub-memory actually runs the a0p-native volatile MemoryCore spawn_sub/merge_sub primitive (ephemeral, no persistence). The lab never re-implements create/train/sentinel logic — it plans permutations and drives the existing endpoints; cross-repo (a0-canonical) strategies are surfaced as doctrine, never falsely executed here.
#   owner: Erin Spencer
#   public_surface: router
#   internal_surface: LabRecipe, IdentityBody, SubMemoryBody, STAGE_CATALOGUE, build_plan
#   auth_boundary: bearer
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.agent_lab_plan_holds
#   rollout: default_enabled
#   rollback: revert + unmount from server.py; the Agent Lab tab loses its catalogue/plan/sub-memory endpoints (instance create/train/sentinel routes are unaffected)
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: api_agent_lab_routes_boundaries
#   summary: catalogue + planner + identity preview + ephemeral MemoryCore sub demo; no persistence, no network, drives existing routes only
#   auth_boundary: bearer
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: api_agent_lab_routes
#   summary: agent-creation permutation catalogue + recipe planner + identity preview + volatile sub-memory demo
#   exposes: router
#   boundaries: auth:bearer, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: agent_lab_plan
#   given: the lab catalogue, an identity, a recipe mixing native + cross-repo stages, and a sub-memory demo
#   then: permutations lists every stage tagged native/cross-repo; identity-preview composes a0(<energy>)<auditor>; plan returns ordered steps mapped to real routes/primitives (cross-repo flagged plan-only, not executable_here) with precondition warnings; sub-memory folds spawn_sub items into the ST ring
#   class: correctness
#   call: a0p_skills.contracts.agent_lab_plan_holds
# === END CONTRACTS ===
"""Agent Creation Lab — compose and plan any permutation of a0 agent-creation logic.

The a0 family has explored several distinct ways to bring an agent into being.
This lab is the single place to compose them. It does NOT re-implement any of
that logic — it catalogues the stages, validates a chosen recipe into an ordered
execution plan, and tells the caller which REAL route or primitive each stage
runs against. The frontend executes the native stages by driving the existing
endpoints (`POST /api/instances`, `/train`, the sentinel PATCH routes, …); the
one thing this module executes directly is the a0p-native *volatile* MemoryCore
sub-instancing primitive, which is engine-internal and has no route of its own.

Three lineages, honestly separated:
  * a0p-native, persistent  — instance create + fresh three-core ZFAE weight
    bank + safetensors checkpoint; multi-teacher distill unlock; native-readiness
    gate; mode inference (zfae_native vs teacher_assisted, no silent fallback);
    sentinel/override config.
  * a0p-native, volatile     — MemoryCore.spawn_sub / merge_sub (in-process sub
    caches folded into the short-term ring; NOT persisted instancing).
  * a0-canonical, cross-repo — InstanceMerge fork/absorb/converge and
    sub_agent_spawn/executor. These live only under `_legacy_a0/` (a Postgres
    agent_runs / queue-worker architecture a0p did not port). The lab plans them
    but marks them plan-only / not executable here — no theorem, proof, or
    runtime status is transferred by naming them.
"""
from __future__ import annotations
from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator

from auth import get_current_user
from agents.schema import AgentMode, compose_canonical_name, compose_agent_name
from interdependent_lib.pcna.memory_core import MemoryCore


router = APIRouter(prefix="/api/agent-lab", tags=["agent-lab"])

# Native-readiness constants mirrored from ZFAERuntime._is_trained_enough — kept
# as data (not an import of the heavy runtime) for the catalogue description.
_NATIVE_MIN_STEPS = 16
_NATIVE_MAX_LOSS = 0.1
_ALL_SEED_PAIRS = 471   # 157 seeds x 3 cores

# Sub-memory demo bounds — this endpoint synchronously appends + echoes the input,
# so cap the fan-out and text size to keep a single request off the event loop.
_MAX_SUBS = 32
_MAX_ITEMS_PER_SUB = 128
_MAX_ITEM_CHARS = 2_000
_MAX_TOTAL_CHARS = 200_000

# The canonical creation ladder. Order here is the plan order. Each stage carries
# whether it is native/executable-here and the REAL entrypoint it maps to.
STAGE_CATALOGUE: list[dict] = [
    {
        "id": "identity_mode",
        "title": "Identity & mode (6-lattice)",
        "kind": "required",
        "native": True,
        "executes_via": "POST /api/agent-lab/identity-preview (compose) then the create stage",
        "source": "agents/schema.py:AgentMode / compose_canonical_name",
        "options": [m.value for m in AgentMode],
        "summary": "Choose the a0(<energy>)<auditor> shape + base/outer model; composes the canonical, owner-namespaced name.",
        "firewalls": [],
    },
    {
        "id": "create",
        "title": "Instance create + fresh ZFAE weight bank",
        "kind": "required",
        "native": True,
        "executes_via": "POST /api/instances",
        "source": "agents/store.py:AgentStore.create -> weights.py:A0ZFAEWeightBank.fresh",
        "options": ["multi_teacher", "single", "native_only"],
        "summary": "Mint the AgentInstance + CharacterSheet; always seeds a fresh three-core (157x53x7x7) weight bank and writes zfae_core.safetensors.",
        "firewalls": ["per-instance safetensors checkpoint is non-committable key material"],
    },
    {
        "id": "distill_unlock",
        "title": "Multi-teacher distill unlock",
        "kind": "optional",
        "native": True,
        "executes_via": "POST /api/instances/{id}/train",
        "source": "runtime.py:ZFAERuntime.train_multi -> trainer.py:ZFAELearner.distill_step",
        "options": ["multi_teacher_distill", "per_turn_distill"],
        "summary": "Distill toward >=2 teacher signatures (round-robin core per step) to drive the bank toward native readiness.",
        "firewalls": ["requires >=2 teacher models; recompose-only training of the seed bank"],
    },
    {
        "id": "readiness_gate",
        "title": "Native-readiness gate",
        "kind": "derived",
        "native": True,
        "executes_via": "GET /api/instances/{id} (inspect zfae_metrics)",
        "source": "runtime.py:_is_trained_enough",
        "options": [],
        "summary": f"Gate to native inference: last_loss set, training_step >= {_NATIVE_MIN_STEPS}, last_loss <= {_NATIVE_MAX_LOSS}, and all {_ALL_SEED_PAIRS} (core,seed) pairs touched.",
        "firewalls": [],
    },
    {
        "id": "mode_inference",
        "title": "Mode inference (native vs teacher-assisted)",
        "kind": "derived",
        "native": True,
        "executes_via": "POST /api/chat/instance/{id}",
        "source": "routes.py chat_instance -> runtime.py RuntimeMode dispatch",
        "options": ["zfae_native", "teacher_assisted"],
        "summary": "The 6-lattice mode resolves to zfae_native or teacher_assisted; native refuses (zfae_refused) rather than silently falling back to a teacher.",
        "firewalls": ["no silent fallback: native mode refuses when not ready"],
    },
    {
        "id": "sentinel_config",
        "title": "Sentinel modes / weights / overrides",
        "kind": "optional",
        "native": True,
        "executes_via": "PATCH /api/instances/{id}/sentinel-modes | /sentinel-weights ; POST /api/overrides/{id}/approve|reject",
        "source": "zfae/sentinel_modes.py, sentinel_weights.py, overrides.py",
        "options": ["observe", "flag", "off"],
        "summary": "Reshape the 13-sentinel halt behavior and resolve pending overrides that gate halted chat/tool turns.",
        "firewalls": ["sentinels gate turns, not creation; instance_create event kind exists but is not fired at create"],
    },
    {
        "id": "sub_memory",
        "title": "Volatile MemoryCore sub-instancing",
        "kind": "optional",
        "native": True,
        "executes_via": "POST /api/agent-lab/sub-memory",
        "source": "interdependent_lib/pcna/memory_core.py:MemoryCore.spawn_sub/merge_sub",
        "options": ["spawn_sub", "push_sub", "merge_sub"],
        "summary": "In-process scratch sub-caches folded into the short-term ring on merge. A real 'sub' primitive — NOT persisted agent instancing.",
        "firewalls": ["volatile only: no persistence, no PCNA fork, no run rows"],
    },
    {
        "id": "checkpoint",
        "title": "Safetensors checkpoint",
        "kind": "automatic",
        "native": True,
        "executes_via": "(implicit) AgentStore.create + train write the checkpoint",
        "source": "weights.py:A0ZFAEWeightBank.save -> store.py:checkpoint_path",
        "options": [],
        "summary": "The three-core bank is written to agents/<id>/zfae_core.safetensors at create and after each training run.",
        "firewalls": ["checkpoint + any last_state PCEA key material are non-committable"],
    },
    {
        "id": "cross_repo_merge",
        "title": "a0-canonical fork / absorb / converge (cross-repo)",
        "kind": "plan_only",
        "native": False,
        "executes_via": None,
        "source": "_legacy_a0/python/engine/merge.py:InstanceMerge ; services/tools/sub_agent_spawn.py",
        "options": ["fork", "absorb", "converge", "sub_agent_spawn"],
        "summary": "The a0-canonical PCNA-fork + spawn/merge lifecycle (agent_runs queue-worker model). NOT ported into a0p's backend; planned here as doctrine only.",
        "firewalls": [
            "a0-canonical only (_legacy_a0); not importable from backend/",
            "no theorem/proof/runtime status transfers by naming it",
        ],
    },
]

_STAGE_BY_ID = {s["id"]: s for s in STAGE_CATALOGUE}
_ALWAYS = ("identity_mode", "create", "checkpoint")
# Modes whose canonical name embeds a <model> energy, so base_model is required.
_NEEDS_BASE = {
    AgentMode.ZFAE_ASSISTED.value, AgentMode.MODEL_OBSERVED_BY_ZFAE.value,
    AgentMode.MODEL_PLUS_CRITIC.value, AgentMode.MODEL_ONLY.value,
    AgentMode.BARE_MODEL.value,
}
_NEEDS_OUTER = {AgentMode.MODEL_PLUS_CRITIC.value}


class IdentityBody(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    mode: str = Field(AgentMode.ZFAE_NATIVE.value, max_length=64)
    base_model: Optional[str] = Field(None, max_length=128)
    outer_model: Optional[str] = Field(None, max_length=128)
    username: Optional[str] = Field(None, max_length=64)


class LabRecipe(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    identity: IdentityBody = Field(default_factory=IdentityBody)
    stages: list[str] = Field(default_factory=list, max_length=32)


class SubMemoryBody(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    # {sub_id: [items...]} — each list is spawned, pushed, then merged into ST.
    items_by_sub: dict[str, list[str]] = Field(default_factory=dict)
    seed_long_term: list[str] = Field(default_factory=list, max_length=64)
    seed_short_term: list[str] = Field(default_factory=list, max_length=64)

    @field_validator("items_by_sub")
    @classmethod
    def _bound_subs(cls, v: dict[str, list[str]]) -> dict[str, list[str]]:
        if len(v) > _MAX_SUBS:
            raise ValueError(f"at most {_MAX_SUBS} sub-caches")
        total = 0
        for sub_id, items in v.items():
            if len(sub_id) > 128:
                raise ValueError("sub id too long")
            if len(items) > _MAX_ITEMS_PER_SUB:
                raise ValueError(f"at most {_MAX_ITEMS_PER_SUB} items per sub")
            for it in items:
                if len(it) > _MAX_ITEM_CHARS:
                    raise ValueError(f"each item must be <= {_MAX_ITEM_CHARS} chars")
                total += len(it)
        if total > _MAX_TOTAL_CHARS:
            raise ValueError("aggregate sub-memory text too large")
        return v

    @field_validator("seed_long_term", "seed_short_term")
    @classmethod
    def _bound_seeds(cls, v: list[str]) -> list[str]:
        for it in v:
            if len(it) > _MAX_ITEM_CHARS:
                raise ValueError(f"each seed must be <= {_MAX_ITEM_CHARS} chars")
        return v


def _identity_warnings(idn: IdentityBody) -> list[str]:
    warns: list[str] = []
    if idn.mode not in {m.value for m in AgentMode}:
        warns.append(f"unknown mode {idn.mode!r}; falling back to a0(zfae) native")
    if idn.mode in _NEEDS_BASE and not idn.base_model:
        warns.append(f"mode {idn.mode!r} embeds a <model> energy — base_model is required")
    if idn.mode in _NEEDS_OUTER and not idn.outer_model:
        warns.append(f"mode {idn.mode!r} needs a second model (outer_model) as critic/auditor")
    return warns


def build_plan(recipe: LabRecipe) -> dict:
    """Compose any permutation into a validated, ordered execution plan.

    Always includes identity -> create -> checkpoint; folds in the requested
    optional/derived/cross-repo stages in canonical ladder order. Each step says
    the real route/primitive it maps to and whether it is executable here.
    """
    idn = recipe.identity
    warnings = _identity_warnings(idn)
    canonical = compose_canonical_name(idn.mode, idn.base_model, idn.outer_model)
    agent_name = compose_agent_name(idn.username, idn.mode, idn.base_model, idn.outer_model)

    chosen = set(recipe.stages) | set(_ALWAYS)
    # readiness_gate + mode_inference are implied once the agent exists.
    chosen |= {"readiness_gate", "mode_inference"}
    if "distill_unlock" not in chosen and idn.mode == AgentMode.ZFAE_NATIVE.value:
        warnings.append("a0(zfae) native mode with no distill_unlock stage will start in zfae_refused until trained")

    steps: list[dict] = []
    for stage in STAGE_CATALOGUE:            # STAGE_CATALOGUE order == plan order
        if stage["id"] not in chosen:
            continue
        executable = bool(stage["native"]) and stage["kind"] != "plan_only"
        steps.append({
            "id": stage["id"],
            "title": stage["title"],
            "kind": stage["kind"],
            "native": stage["native"],
            "executable_here": executable,
            "executes_via": stage["executes_via"],
            "source": stage["source"],
            "firewalls": stage["firewalls"],
        })
    return {
        "identity": {
            "mode": idn.mode, "canonical": canonical, "agent_name": agent_name,
            "base_model": idn.base_model, "outer_model": idn.outer_model,
        },
        "steps": steps,
        "step_count": len(steps),
        "executable_steps": sum(1 for s in steps if s["executable_here"]),
        "plan_only_steps": [s["id"] for s in steps if not s["executable_here"]],
        "warnings": warnings,
    }


@router.get("/permutations")
async def permutations(user=Depends(get_current_user)):
    """The lab palette: every agent-creation stage/strategy, tagged native vs cross-repo."""
    return {
        "ladder": [s["id"] for s in STAGE_CATALOGUE],
        "stages": STAGE_CATALOGUE,
        "modes": [m.value for m in AgentMode],
        "native_readiness": {"min_steps": _NATIVE_MIN_STEPS,
                             "max_loss": _NATIVE_MAX_LOSS,
                             "seed_pairs": _ALL_SEED_PAIRS},
    }


@router.post("/identity-preview")
async def identity_preview(body: IdentityBody, user=Depends(get_current_user)):
    """Compose the canonical a0(<energy>)<auditor> name + owner-namespaced name."""
    return {
        "canonical": compose_canonical_name(body.mode, body.base_model, body.outer_model),
        "agent_name": compose_agent_name(body.username, body.mode, body.base_model, body.outer_model),
        "warnings": _identity_warnings(body),
    }


@router.post("/plan")
async def plan(recipe: LabRecipe, user=Depends(get_current_user)):
    """Validate a chosen permutation and return the ordered execution plan."""
    return build_plan(recipe)


@router.post("/sub-memory")
async def sub_memory(body: SubMemoryBody, user=Depends(get_current_user)):
    """Run the a0p-native volatile MemoryCore sub-instancing primitive (ephemeral).

    Spawns a fresh MemoryCore, seeds LT/ST, then spawn_sub -> push_sub -> merge_sub
    each requested sub-cache (folding its items into the short-term ring). No
    persistence — this is the volatile sub primitive, not agent instancing.
    """
    core = MemoryCore()
    for it in body.seed_long_term:
        core.push_lt(it)
    for it in body.seed_short_term:
        core.push_st(it)
    merges: dict[str, list[str]] = {}
    for sub_id, items in body.items_by_sub.items():
        core.spawn_sub(sub_id)
        for it in items:
            core.push_sub(sub_id, it)
        merges[sub_id] = core.merge_sub(sub_id)
    return {
        "merged": merges,
        "snapshot": core.snapshot(),
        "firewall": "volatile only — no persistence, no PCNA fork, no run rows",
    }


__all__ = ["router"]
# ratios: loc_comments=250:85 imports_exports=7:9 calls_definitions=50:11
