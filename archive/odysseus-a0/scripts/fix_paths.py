# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 7:33
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 2:0
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 4:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: fix_paths
#   module_name: fix_paths
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
# id: fix_paths_boundaries
#   summary: hmmm
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: fix_paths
#   summary: hmmm
#   exposes: none
# === END CAPABILITIES ===
import fileinput
import sys

# Read app.py and replace the BASE_DIR line
for line in fileinput.input('app.py', inplace=True):
    if line.startswith('BASE_DIR = '):
        print('BASE_DIR = os.path.dirname(os.path.abspath(__file__)) + "/"')
    else:
        print(line, end='')
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 7:33
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 2:0
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 4:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
