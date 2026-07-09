# ratios: loc_comments=50:43 imports_exports=2:1 calls_definitions=25:1
# === MODULE_BUILD ===
# id: a0p_db_motor
#   module_name: db
#   module_kind: service
#   summary: Motor async client + collection accessors + index ensurance
#   owner: a0p maintainer
#   public_surface: db, keys_col, vault_col, sessions_col, drafts_col, fanout_col, chain_col, agents_col, usage_col, ensure_indexes
#   internal_surface: _client, _MONGO_URL, _DB_NAME
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: internal
#   user_data_boundary: write
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: drop mongo collections; revert server.py import
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: a0p_db_motor_boundaries
#   summary: Motor async client + collection accessors + index ensurance
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: internal
#   user_data_boundary: write
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: a0p_db_motor
#   summary: Motor async client + collection accessors + index ensurance
#   exposes: db, keys_col, vault_col, sessions_col, drafts_col, fanout_col, chain_col, agents_col, usage_col, ensure_indexes
#   boundaries: auth:none, storage:write, network:internal, user_data:write
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""MongoDB Motor client + collection accessors."""
import os
from motor.motor_asyncio import AsyncIOMotorClient

_MONGO_URL = os.environ.get("MONGO_URL")
_DB_NAME = os.environ.get("DB_NAME")
if not _MONGO_URL or not _DB_NAME:
    raise RuntimeError("MONGO_URL / DB_NAME missing")

_client = AsyncIOMotorClient(_MONGO_URL)
db = _client[_DB_NAME]

# Collections
keys_col       = db["byok_keys"]
vault_col      = db["site_vault"]
sessions_col   = db["chat_sessions"]
drafts_col     = db["prompt_drafts"]
fanout_col     = db["fanout_runs"]
chain_col      = db["daisy_chain_runs"]
agents_col     = db["detachable_agents"]
agent_instances_col = db["agent_instances"]
usage_col      = db["usage_records"]
fiq_audit_col  = db["fiq_audit_log"]
pending_overrides_col = db["pending_overrides"]
users_col      = db["users"]
login_attempts_col = db["login_attempts"]
password_reset_tokens_col = db["password_reset_tokens"]
demo_quota_col = db["demo_quota"]
custom_keys_col = db["custom_keys"]
user_tools_col = db["user_tools"]
mcp_servers_col = db["mcp_servers"]
odysseus_servers_col = db["odysseus_servers"]
skills_col = db["skills"]


async def ensure_indexes():
    await keys_col.create_index([("user_id", 1), ("provider", 1)])
    await vault_col.create_index([("user_id", 1), ("site", 1), ("account_label", 1)])
    await sessions_col.create_index([("user_id", 1), ("updated_at", -1)])
    await drafts_col.create_index([("user_id", 1), ("updated_at", -1)])
    await fanout_col.create_index([("user_id", 1), ("created_at", -1)])
    await chain_col.create_index([("user_id", 1), ("created_at", -1)])
    await agents_col.create_index([("slug", 1)])
    await agent_instances_col.create_index([("user_id", 1), ("updated_at", -1)])
    await usage_col.create_index([("user_id", 1), ("created_at", -1)])
    await fiq_audit_col.create_index([("timestamp_ms", -1)])
    await users_col.create_index("email", unique=True)
    await users_col.create_index("username", unique=True)
    await login_attempts_col.create_index("identifier")
    await password_reset_tokens_col.create_index("expires_at", expireAfterSeconds=0)
    await demo_quota_col.create_index([("user_id", 1), ("day", 1)], unique=True)
    await custom_keys_col.create_index([("user_id", 1), ("name", 1)], unique=True)
    await user_tools_col.create_index([("user_id", 1), ("name", 1)], unique=True)
    await mcp_servers_col.create_index([("user_id", 1), ("name", 1)], unique=True)
    await odysseus_servers_col.create_index([("user_id", 1), ("name", 1)], unique=True)
    await skills_col.create_index([("name", 1)])
    await skills_col.create_index([("owner_user_id", 1)])

# === CONTRACTS ===
# id: a0p_db_motor_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=50:43 imports_exports=2:1 calls_definitions=25:1
