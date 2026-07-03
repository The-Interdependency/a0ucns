# === MODULE_BUILD ===
# id: tests_conftest
#   module_name: conftest
#   module_kind: test
#   summary: pytest configuration — enables pytest-asyncio plugin in auto mode for the backend test suite
#   owner: Erin Spencer
#   public_surface: pytest_plugins
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: pytest_runs_this_file
#   rollout: default_enabled
#   rollback: revert; async tests fail to collect
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: tests_conftest_boundaries
#   summary: pytest plugin loader
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: tests_conftest
#   summary: pytest async config
#   exposes: pytest_plugins
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===

import pytest
pytest_plugins = ["pytest_asyncio"]

# === CONTRACTS ===
# id: tests_conftest_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===

