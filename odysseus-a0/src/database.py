# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 35:34
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 2:0
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: database
#   module_name: database
#   module_kind: hmmm
#   summary: hmmm
#   owner: hmmm
#   public_surface: none
#   internal_surface: none
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   tests: hmmm
#   rollout: hmmm
#   rollback: hmmm
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: database_boundaries
#   summary: hmmm
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: database
#   summary: hmmm
#   exposes: none
# === END CAPABILITIES ===
# Re-export everything from the canonical core.database module
# so that `from src.database import X` continues to work everywhere.
from core.database import *  # noqa: F401,F403
from core.database import (  # explicit re-exports for IDE/type-checker visibility
    Base,
    TimestampMixin,
    DATABASE_URL,
    engine,
    SessionLocal,
    Session,
    ChatMessage,
    Document,
    DocumentVersion,
    GalleryImage,
    ModelEndpoint,
    McpServer,
    Comparison,
    ApiToken,
    Signature,
    Webhook,
    UserTool,
    UserToolData,
    CrewMember,
    ScheduledTask,
    TaskRun,
    Memory,
    init_db,
    get_db,
    get_db_session,
    bulk_insert_messages,
    cleanup_old_sessions,
    get_session_stats,
    get_detailed_stats,
    update_session_last_accessed,
    get_session_by_id,
    archive_session,
)
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 35:34
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 2:0
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
