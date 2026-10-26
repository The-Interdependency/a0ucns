# ratios: loc_comments=42:47 imports_exports=6:5 calls_definitions=18:6
# === MODULE_BUILD ===
# id: zfae_archive
#   module_name: archive
#   module_kind: service
#   summary: ZFAE archive — per-agent training records JSONL + per-session ephemeral chat archive with char-compress output shape
#   owner: Erin Spencer
#   public_surface: append_training_record, iter_records, archive_session, archive_path_for, training_records_path_for
#   internal_surface: _ensure_dir
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: write
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_archive_appends_jsonl_holds
#   rollout: default_enabled
#   rollback: stop appending; existing archive preserved
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_archive_boundaries
#   summary: ZFAE archive — per-agent training records JSONL + per-session ephemeral chat archive with char-compress output shape
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: write
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_archive
#   summary: ZFAE archive — per-agent training records JSONL + per-session ephemeral chat archive with char-compress output shape
#   exposes: append_training_record, iter_records, archive_session, archive_path_for, training_records_path_for
#   boundaries: auth:none, storage:write, network:none, user_data:write
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_archive_appends_jsonl
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_archive_appends_jsonl_holds
# === END CONTRACTS ===
"""ZFAE archive — training records + ephemeral chat archives."""
from __future__ import annotations
import json
import os
import time
from pathlib import Path
from typing import Iterator


_STORAGE_ROOT_ENV: str = "A0P_AGENTS_ROOT"
_DEFAULT_ROOT: str = "/app/storage/agents"


def _ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def archive_path_for(agent_id: str) -> Path:
    root = Path(os.environ.get(_STORAGE_ROOT_ENV, _DEFAULT_ROOT))
    return _ensure_dir(root / agent_id / "archive")


def training_records_path_for(agent_id: str) -> Path:
    root = Path(os.environ.get(_STORAGE_ROOT_ENV, _DEFAULT_ROOT))
    return _ensure_dir(root / agent_id) / "training_records.jsonl"


def append_training_record(agent_id: str, record: dict) -> str:
    """Append a training record to <agent>/training_records.jsonl. Returns the path."""
    path = training_records_path_for(agent_id)
    record = {"timestamp_ms": int(time.time() * 1000), **record}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")
    return str(path)


def iter_records(agent_id: str) -> Iterator[dict]:
    path = training_records_path_for(agent_id)
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def archive_session(agent_id: str, session_id: str, content: dict) -> str:
    """Write an ephemeral chat session to <agent>/archive/<session_id>.json.

    Content SHOULD follow char-compress output shape — flesh-dense, frozen-bones
    preserved, hmmm carried — but this function does not enforce it.
    """
    path = archive_path_for(agent_id) / f"{session_id}.json"
    payload = {"agent_id": agent_id, "session_id": session_id,
               "archived_ms": int(time.time() * 1000), **content}
    path.write_text(json.dumps(payload, default=str, indent=2), encoding="utf-8")
    return str(path)
# ratios: loc_comments=42:47 imports_exports=6:5 calls_definitions=18:6
