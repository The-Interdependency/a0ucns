# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 37:46
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 7:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 11:1
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: readiness
#   module_name: readiness
#   module_kind: hmmm
#   summary: Ithaca anchor — local-instance readiness / integrity self-check.
#   owner: hmmm
#   public_surface: check_readiness
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
# id: readiness_boundaries
#   summary: Ithaca anchor — local-instance readiness / integrity self-check.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: readiness
#   summary: Ithaca anchor — local-instance readiness / integrity self-check.
#   exposes: check_readiness
# === END CAPABILITIES ===
"""Ithaca anchor — local-instance readiness / integrity self-check.

Beyond ``/api/health``'s liveness ping, this confirms the self-hosted instance is
whole and at home: the database is reachable, the data directory is present and
writable, and storage is local-first. Served by ``GET /api/ready`` and suitable
for an orchestrator readiness probe (200 only when every critical check passes).
"""

import os
import uuid
from datetime import datetime
from typing import Dict


def check_readiness() -> Dict[str, object]:
    """Run the readiness checks and return a JSON-serialisable report.

    ``ready`` is True only when every critical check (database, data_dir) passes.
    ``local_first`` is informational — a remote database is a valid deployment, so
    it never fails readiness, it only reports whether storage stays on this host.
    """
    from core.constants import APP_VERSION, DATA_DIR
    from core.database import DATABASE_URL, engine
    from sqlalchemy import text as sql_text

    checks: Dict[str, Dict[str, object]] = {}

    # Database reachable — the simplest honest probe that the engine is live.
    try:
        with engine.connect() as conn:
            conn.execute(sql_text("SELECT 1"))
        checks["database"] = {"ok": True}
    except Exception as e:
        checks["database"] = {"ok": False, "error": str(e)}

    # Data directory present and writable — home must be able to hold its own data.
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        probe = os.path.join(DATA_DIR, f".ready_probe_{uuid.uuid4().hex}")
        with open(probe, "w", encoding="utf-8") as fh:
            fh.write("ok")
        os.remove(probe)
        checks["data_dir"] = {"ok": True, "path": DATA_DIR}
    except Exception as e:
        checks["data_dir"] = {"ok": False, "error": str(e)}

    # Local-first: storage stays on the home machine (informational, never fatal).
    local_first = (
        DATABASE_URL.startswith("sqlite")
        or "localhost" in DATABASE_URL
        or "127.0.0.1" in DATABASE_URL
    )
    checks["local_first"] = {"ok": True, "local": local_first}

    ready = all(bool(c.get("ok")) for c in checks.values())
    return {
        "ready": ready,
        "version": APP_VERSION,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 37:46
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 7:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 11:1
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
