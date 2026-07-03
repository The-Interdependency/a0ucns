# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 2:38
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 1:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: companion
#   module_name: companion
#   module_kind: hmmm
#   summary: Odysseus companion bridge — additive LAN endpoints.
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
# id: companion_boundaries
#   summary: Odysseus companion bridge — additive LAN endpoints.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: companion
#   summary: Odysseus companion bridge — additive LAN endpoints.
#   exposes: none
# === END CAPABILITIES ===
"""Odysseus companion bridge — additive LAN endpoints.

Read endpoints (/api/companion/ping, /info, owner-scoped /models) so a LAN
client can discover what a server offers, plus admin-only pairing
(/api/companion/pair) that mints a one-time chat-scoped token on POST. No new LLM
logic; auth is enforced by the existing AuthMiddleware. See companion/README.md.
"""

from companion.routes import setup_companion_routes

__all__ = ["setup_companion_routes"]
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 2:38
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 1:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
