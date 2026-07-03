# ratios: loc_comments=105:42 imports_exports=5:14 calls_definitions=18:16
# === MODULE_BUILD ===
# id: a0p_models
#   module_name: models
#   module_kind: schema
#   summary: Pydantic surface for the public API (BYOK keys, vault, sessions, drafts, chat, agents)
#   owner: a0p maintainer
#   public_surface: KeyUpsert, KeyPublic, SiteAccountUpsert, SiteAccountPublic, SessionUpsert, SessionPublic, ChatTurn, DraftUpsert, DraftPublic, FanOutRequest, DaisyChainRequest, SynthesizeRequest, AgentExport, PROVIDERS, new_id
#   internal_surface: _utc_now_iso, _Base
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: revert file; consumers break at import
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: a0p_models_boundaries
#   summary: Pydantic surface for the public API (BYOK keys, vault, sessions, drafts, chat, agents)
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: a0p_models
#   summary: Pydantic surface for the public API (BYOK keys, vault, sessions, drafts, chat, agents)
#   exposes: KeyUpsert, KeyPublic, SiteAccountUpsert, SiteAccountPublic, SessionUpsert, SessionPublic, ChatTurn, DraftUpsert, DraftPublic, FanOutRequest, DaisyChainRequest, SynthesizeRequest, AgentExport, PROVIDERS, new_id
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""Pydantic models for the API surface."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Optional, List
from pydantic import BaseModel, ConfigDict, Field
import uuid


class _Base(BaseModel):
    model_config = ConfigDict(protected_namespaces=())


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


PROVIDERS = ("openai", "anthropic", "gemini", "xai")


class KeyUpsert(BaseModel):
    user_id: str = Field(default="local")
    provider: str
    api_key: str
    label: Optional[str] = None


class KeyPublic(BaseModel):
    id: str
    user_id: str
    provider: str
    label: Optional[str] = None
    masked: str
    has_key: bool
    last_used_at: Optional[str] = None
    created_at: str
    updated_at: str


class SiteAccountUpsert(BaseModel):
    user_id: str = Field(default="local")
    site: str                # e.g. "github.com", "gmail.com"
    account_label: str       # e.g. "personal", "work"
    env: dict[str, str] = Field(default_factory=dict)   # plaintext-input; encrypted at rest


class SiteAccountPublic(BaseModel):
    id: str
    user_id: str
    site: str
    account_label: str
    env_keys: List[str]      # only the keys, not the values
    created_at: str
    updated_at: str


class SessionUpsert(BaseModel):
    user_id: str = Field(default="local")
    title: Optional[str] = None
    system_context: str = ""
    persona: Optional[str] = None
    selected_models: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatTurn(BaseModel):
    role: str           # "user" | "assistant" | "system"
    content: str
    model_id: Optional[str] = None
    usage: dict[str, Any] = Field(default_factory=dict)
    ts: str = Field(default_factory=_utc_now_iso)


class SessionPublic(BaseModel):
    id: str
    user_id: str
    title: Optional[str] = None
    system_context: str = ""
    persona: Optional[str] = None
    selected_models: List[str] = []
    turns: List[ChatTurn] = []
    created_at: str
    updated_at: str


class DraftUpsert(BaseModel):
    user_id: str = Field(default="local")
    title: Optional[str] = None
    content: str
    tags: List[str] = Field(default_factory=list)


class DraftPublic(BaseModel):
    id: str
    user_id: str
    title: Optional[str] = None
    content: str
    tags: List[str] = []
    created_at: str
    updated_at: str


class FanOutRequest(BaseModel):
    user_id: str = Field(default="local")
    prompt: str
    system_context: str = ""
    model_ids: List[str]               # ["openai:gpt-4o-mini", "anthropic:claude-...", ...]
    session_id: Optional[str] = None


class DaisyChainRequest(BaseModel):
    user_id: str = Field(default="local")
    prompt: str
    system_context: str = ""
    model_ids: List[str]
    rounds: int = 1
    session_id: Optional[str] = None


class SynthesizeRequest(BaseModel):
    user_id: str = Field(default="local")
    prompt: str
    responses: List[dict]              # [{model_id, content}]
    synth_model: str


class AgentExport(BaseModel):
    slug: str
    name: str
    description: str = ""
    system_context: str = ""
    persona: str = ""
    default_models: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    aimmh_pattern: str = "fan_out"     # fan_out | daisy_chain | council | room_synthesized
    rounds: int = 1
    is_premium: bool = False


def new_id() -> str:
    return str(uuid.uuid4())

# === CONTRACTS ===
# id: a0p_models_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=105:42 imports_exports=5:14 calls_definitions=18:16
