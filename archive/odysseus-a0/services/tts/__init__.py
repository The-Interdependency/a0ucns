# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 5:34
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
# id: tts
#   module_name: tts
#   module_kind: service
#   summary: TTS service — text-to-speech.
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
# id: tts_boundaries
#   summary: TTS service — text-to-speech.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: tts
#   summary: TTS service — text-to-speech.
#   exposes: none
# === END CAPABILITIES ===
# services/tts/__init__.py
"""TTS service — text-to-speech."""

from .tts_service import (
    TTSService,
    get_tts_service,
)

__all__ = ["TTSService", "get_tts_service"]
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 5:34
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
