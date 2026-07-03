# ratios: loc_comments=118:54 imports_exports=6:3 calls_definitions=38:3
# === MODULE_BUILD ===
# id: skills_sync
#   module_name: sync
#   module_kind: service
#   summary: pulls canonical skills from The-Interdependency/skill-lib GitHub repo — fetches the index.json, validates each entry, upserts global skills (owner_user_id=None); reverse direction (publish-back) is reserved for skills marked as publishable=True
#   owner: Erin Spencer
#   public_surface: pull_from_skill_lib, push_to_skill_lib_stub
#   internal_surface: _fetch_index, _SKILL_LIB_URL
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: true
#   tests: a0p_skills.contracts.skills_sync_pull_holds
#   rollout: default_enabled
#   rollback: revert; the skill catalog stops auto-syncing
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: skills_sync_boundaries
#   summary: GitHub pull-sync for global skill catalog
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: true
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: skills_sync
#   summary: skill-lib repo sync
#   exposes: pull_from_skill_lib, push_to_skill_lib_stub
#   boundaries: auth:none, storage:write, network:external, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: skills_sync_pull
#   given: a transient network error from GitHub
#   then: pull_from_skill_lib returns {ok:false, error:..., pulled:0} instead of raising
#   class: integration
#   call: a0p_skills.contracts.skills_sync_pull_holds
# === END CONTRACTS ===
"""Pull global skills from The-Interdependency/skill-lib."""
from __future__ import annotations
import time
from typing import Any

import httpx

from .registry import tokenize_scope, tokenize_logic, OVERLAP_THRESHOLD


_SKILL_LIB_URL = "https://raw.githubusercontent.com/The-Interdependency/skill-lib/main/index.json"


async def _fetch_index(url: str = _SKILL_LIB_URL) -> list[dict]:
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as cli:
        r = await cli.get(url)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and "skills" in data:
        data = data["skills"]
    if not isinstance(data, list):
        raise ValueError("skill-lib index.json must be a list (or {skills:[...]})")
    return data


async def pull_from_skill_lib(col, url: str = _SKILL_LIB_URL) -> dict[str, Any]:
    """Pull and upsert global skills. Best-effort — network failures return a
    structured error and do not raise.

    Returns ``{ok:bool, pulled:int, skipped:int, errors:list, fetched_at_ms:int}``.
    """
    try:
        entries = await _fetch_index(url)
    except Exception as e:
        return {"ok": False, "pulled": 0, "skipped": 0,
                "errors": [f"{type(e).__name__}: {e}"], "fetched_at_ms": int(time.time() * 1000)}

    pulled = 0
    skipped = 0
    errors: list[str] = []
    now = int(time.time() * 1000)
    for ent in entries:
        try:
            name = ent["name"]
            description = ent.get("description", "")
            scope = list(ent.get("scope_tokens") or tokenize_scope(name + " " + description))
            logic = list(ent.get("logic_set_tokens") or tokenize_logic(description))
            doc = {
                "_id": ent.get("id") or f"skill_lib::{name}",
                "name": name, "description": description,
                "prompt_template": ent.get("prompt_template", ""),
                "tool_bindings": list(ent.get("tool_bindings") or []),
                "sentinel_overrides": dict(ent.get("sentinel_overrides") or {}),
                "scope_tokens": scope, "logic_set_tokens": logic,
                "owner_user_id": None, "source": "skill-lib",
                "version": str(ent.get("version", "1")),
                "created_at_ms": now, "updated_at_ms": now,
            }
            await col.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
            pulled += 1
        except KeyError as e:
            skipped += 1
            errors.append(f"missing required key in skill-lib entry: {e}")
        except Exception as e:
            skipped += 1
            errors.append(f"{type(e).__name__}: {e}")
    return {"ok": True, "pulled": pulled, "skipped": skipped,
            "errors": errors, "fetched_at_ms": now}


async def push_to_skill_lib_stub(col, *, user_id: str) -> dict:
    """Publish skills marked ``publishable=True`` to The-Interdependency/skill-lib.

    If ``SKILL_LIB_GH_TOKEN`` is set, opens a PR via the GitHub API that updates
    ``index.json`` with the publishable skill entries. Without the token, returns
    a structured ``next_step`` payload describing the manual PR the user should open.
    """
    import os, base64, json as _json, time as _time
    pubs: list[dict] = []
    async for d in col.find({"owner_user_id": user_id, "publishable": True}):
        pubs.append({"id": d["_id"], "name": d["name"], "description": d.get("description"),
                     "prompt_template": d.get("prompt_template"),
                     "tool_bindings": d.get("tool_bindings", []),
                     "sentinel_overrides": d.get("sentinel_overrides", {}),
                     "scope_tokens": d.get("scope_tokens", []),
                     "logic_set_tokens": d.get("logic_set_tokens", []),
                     "version": d.get("version", "1")})
    token = os.environ.get("SKILL_LIB_GH_TOKEN")
    repo = os.environ.get("SKILL_LIB_REPO", "The-Interdependency/skill-lib")
    if not pubs:
        return {"publish_ready": [], "ok": True, "next_step": "no skills marked publishable=true"}
    if not token:
        return {
            "publish_ready": pubs, "ok": False, "pr_url": None,
            "next_step": ("SKILL_LIB_GH_TOKEN not set — set it in /app/backend/.env "
                          f"(needs `repo` scope on {repo}) and retry. "
                          "Without it I cannot open the PR for you."),
        }
    # Real GitHub-API path: fetch index.json (default branch), merge our entries,
    # create a branch, write the file, open a PR. Best-effort; any HTTP error
    # bubbles up as ok:false.
    base = f"https://api.github.com/repos/{repo}"
    h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
         "X-GitHub-Api-Version": "2022-11-28"}
    branch = f"a0p-publish-{int(_time.time())}"
    try:
        async with httpx.AsyncClient(timeout=30) as cli:
            repo_info = (await cli.get(base, headers=h)).json()
            default_branch = repo_info.get("default_branch", "main")
            ref_resp = (await cli.get(f"{base}/git/refs/heads/{default_branch}", headers=h)).json()
            head_sha = ref_resp["object"]["sha"]
            file_resp = await cli.get(f"{base}/contents/index.json?ref={default_branch}", headers=h)
            existing: list[dict] = []
            file_sha: str | None = None
            if file_resp.status_code == 200:
                d = file_resp.json()
                file_sha = d["sha"]
                existing = _json.loads(base64.b64decode(d["content"]).decode())
                if isinstance(existing, dict):
                    existing = existing.get("skills", [])
            by_name = {e.get("name"): e for e in existing if isinstance(e, dict)}
            for p in pubs:
                by_name[p["name"]] = p
            merged = sorted(by_name.values(), key=lambda x: x.get("name", ""))
            new_content = base64.b64encode(_json.dumps(merged, indent=2).encode()).decode()
            await cli.post(f"{base}/git/refs", headers=h,
                           json={"ref": f"refs/heads/{branch}", "sha": head_sha})
            put_body = {"message": f"a0p: publish {len(pubs)} skill(s) from {user_id}",
                        "content": new_content, "branch": branch}
            if file_sha:
                put_body["sha"] = file_sha
            await cli.put(f"{base}/contents/index.json", headers=h, json=put_body)
            pr = (await cli.post(f"{base}/pulls", headers=h, json={
                "title": f"a0p: publish {len(pubs)} skill(s)",
                "head": branch, "base": default_branch,
                "body": f"Automated publish from a0p (user_id `{user_id}`).\n\n" +
                        "\n".join(f"- {p['name']}" for p in pubs),
            })).json()
        return {"publish_ready": pubs, "ok": True, "pr_url": pr.get("html_url"),
                "branch": branch, "next_step": "review and merge the PR"}
    except Exception as e:
        return {"publish_ready": pubs, "ok": False, "pr_url": None,
                "next_step": f"github push failed: {type(e).__name__}: {e}"}


__all__ = ["pull_from_skill_lib", "push_to_skill_lib_stub", "_SKILL_LIB_URL"]
# ratios: loc_comments=118:54 imports_exports=6:3 calls_definitions=38:3
