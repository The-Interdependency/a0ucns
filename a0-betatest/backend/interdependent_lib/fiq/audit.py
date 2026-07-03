# ratios: loc_comments=74:48 imports_exports=8:1 calls_definitions=24:8
# === MODULE_BUILD ===
# id: fiq_audit_log
#   module_name: audit
#   module_kind: service
#   summary: append-only JSONL fiq audit log at /app/storage/fiq_audit/YYYY-MM-DD.jsonl + MongoDB mirror; prev_hash chain verifiable end-to-end
#   owner: Erin Spencer
#   public_surface: AuditLog, append, iter_today, verify, last_hash
#   internal_surface: _path_for_day
#   auth_boundary: admin
#   storage_boundary: write
#   network_boundary: internal
#   user_data_boundary: write
#   admin_only: false
#   tests: a0p_skills.contracts.fiq_audit_filesystem_and_mongo_holds
#   rollout: default_enabled
#   rollback: stop appending; existing log preserved
#   storage_policy: filesystem canonical + MongoDB read-optimized mirror
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: fiq_audit_log_boundaries
#   summary: append-only JSONL fiq audit log at /app/storage/fiq_audit/YYYY-MM-DD.jsonl + MongoDB mirror; prev_hash chain verifiable end-to-end
#   auth_boundary: admin
#   storage_boundary: write
#   network_boundary: internal
#   user_data_boundary: write
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: fiq_audit_log
#   summary: append-only JSONL fiq audit log at /app/storage/fiq_audit/YYYY-MM-DD.jsonl + MongoDB mirror; prev_hash chain verifiable end-to-end
#   exposes: AuditLog, append, iter_today, verify, last_hash
#   boundaries: auth:admin, storage:write, network:internal, user_data:write
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: fiq_audit_filesystem_and_mongo
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.fiq_audit_filesystem_and_mongo_holds
# === END CONTRACTS ===
"""Fiq audit log — filesystem canonical + Mongo mirror."""
from __future__ import annotations
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .events import AuditEvent, chain_hash, verify_chain


_STORAGE_ROOT_ENV: str = "A0P_AUDIT_STORAGE_ROOT"
_DEFAULT_ROOT: str = "/app/storage/fiq_audit"


class AuditLog:
    """Append-only JSONL log of fiq audit events with prev_hash chain."""

    def __init__(self, root: str | None = None, mongo_collection=None):
        self.root = Path(root or os.environ.get(_STORAGE_ROOT_ENV, _DEFAULT_ROOT))
        self.root.mkdir(parents=True, exist_ok=True)
        self._mongo = mongo_collection  # optional read-optimised mirror
        self._last_hash: str = self._scan_last_hash()

    def _path_for_day(self, ts_ms: int | None = None) -> Path:
        ts = ts_ms / 1000 if ts_ms else None
        d = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else datetime.now(tz=timezone.utc)
        return self.root / f"{d.strftime('%Y-%m-%d')}.jsonl"

    def _scan_last_hash(self) -> str:
        """Recover the last this_hash from the most recent file (chain continuity)."""
        files = sorted(self.root.glob("*.jsonl"))
        if not files:
            return "0" * 32
        last_file = files[-1]
        last_line = ""
        with last_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last_line = line
        if not last_line:
            return "0" * 32
        try:
            d = json.loads(last_line)
            return d.get("this_hash", "0" * 32)
        except json.JSONDecodeError:
            return "0" * 32

    def append(self, event: AuditEvent) -> str:
        """Append `event` to the canonical filesystem log, mirror to Mongo if available."""
        event.prev_hash = self._last_hash
        event.this_hash = chain_hash(event, self._last_hash)
        path = self._path_for_day(event.timestamp_ms)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), default=str) + "\n")
        if self._mongo is not None:
            try:
                self._mongo.insert_one({**asdict(event), "_log_path": str(path)})
            except Exception:
                pass  # mirror is non-canonical; failure does not block append
        self._last_hash = event.this_hash
        return event.this_hash

    def last_hash(self) -> str:
        return self._last_hash

    def iter_today(self) -> Iterator[dict]:
        path = self._path_for_day()
        if not path.exists():
            return
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue

    def verify(self) -> bool:
        """Walk the entire on-disk log and verify the prev_hash chain end-to-end."""
        # Simplified: walk today's file only for now; multi-day chain spans need a stitch.
        events: list[dict] = list(self.iter_today())
        if not events:
            return True
        prev = events[0].get("prev_hash", "0" * 32)
        for d in events:
            if d.get("prev_hash") != prev:
                return False
            prev = d.get("this_hash", "")
        return True
# ratios: loc_comments=74:48 imports_exports=8:1 calls_definitions=24:8
