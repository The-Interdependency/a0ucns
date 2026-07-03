# === MODULE_BUILD ===
# id: tests_backend_test
#   module_name: backend_test
#   module_kind: test
#   summary: end-to-end backend regression suite — covers /api/health, BYOK keys CRUD with encryption-at-rest masking, and chat session flows; intended to be executed by the testing-agent harness against the live preview ingress
#   owner: Erin Spencer
#   public_surface: test_*
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   tests: pytest_runs_this_file
#   rollout: default_enabled
#   rollback: revert; lose e2e coverage
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: tests_backend_test_boundaries
#   summary: end-to-end regression suite over REACT_APP_BACKEND_URL
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: tests_backend_test
#   summary: e2e regression suite
#   exposes: test_*
#   boundaries: auth:none, storage:none, network:external, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===

"""End-to-end backend regression tests for the a0p research instrument.

Covers:
- /api/health
- BYOK keys (PUT/GET/DELETE) + encryption-at-rest masking
- Site .env vault (PUT/GET/POST reveal/DELETE)
- Model inventory (Emergent curated + BYOK fetched + errors map)
- Sessions CRUD (with editable system_context + persona + selected_models)
- Drafts CRUD (autosave)
- Chat: /single, /fanout, /daisychain, /synthesize  (routed via Emergent universal key)
- Inspector heartbeat + snapshot (PCNA/PTCA + ring signals)
- Detachable agents: list (starters seeded), create, manifest, delete
- Usage log + aggregate

xAI is intentionally not tested (no user key).
"""
from __future__ import annotations
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    # Tests should not silently use a fallback; surface mis-config loudly.
    raise RuntimeError("REACT_APP_BACKEND_URL is not set in env")
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

USER_ID = "local"
# Unique tag so we can clean up our own artifacts even if other rows exist.
TAG = f"TEST_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def client() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ----------------- 1) Health -----------------
class TestHealth:
    def test_health_ok(self, client):
        r = client.get(f"{API}/health", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "ok"
        assert data["service"] == "a0p"
        # providers must include the four BYOK + emergent
        providers = set(data.get("providers", []))
        for p in ("openai", "anthropic", "gemini", "xai", "emergent"):
            assert p in providers, f"provider {p} missing from /health: {providers}"
        # agent card present
        agent = data.get("agent") or {}
        assert agent.get("id") and agent.get("name")


# ----------------- 2) BYOK keys -----------------
class TestKeys:
    test_key = "sk-test-1234567890abcdef"
    created_id = None

    def test_put_key_encrypted(self, client):
        r = client.put(f"{API}/keys", json={
            "user_id": USER_ID, "provider": "openai",
            "api_key": self.test_key, "label": f"{TAG}-openai",
        }, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["ok"] is True
        assert data["provider"] == "openai"
        # masked format ('sk-t...cdef')
        assert data["masked"].startswith("sk-t") and data["masked"].endswith("cdef")
        TestKeys.created_id = data["id"]

    def test_list_keys_masked(self, client):
        r = client.get(f"{API}/keys", params={"user_id": USER_ID}, timeout=15)
        assert r.status_code == 200, r.text
        keys = r.json()["keys"]
        openai_entries = [k for k in keys if k["provider"] == "openai"]
        assert len(openai_entries) >= 1
        k = openai_entries[0]
        assert k["has_key"] is True
        assert k["masked"].startswith("sk-t") and k["masked"].endswith("cdef")
        # plaintext must NOT be returned
        assert "api_key" not in k
        assert "enc_api_key" not in k

    def test_delete_key(self, client):
        assert TestKeys.created_id, "previous test must populate created_id"
        r = client.delete(f"{API}/keys/{TestKeys.created_id}",
                          params={"user_id": USER_ID}, timeout=15)
        assert r.status_code == 200
        assert r.json()["ok"] is True
        # verify removed
        r2 = client.get(f"{API}/keys", params={"user_id": USER_ID}, timeout=15)
        assert all(k["id"] != TestKeys.created_id for k in r2.json()["keys"])


# ----------------- 3) Site .env vault -----------------
class TestVault:
    created_id = None

    def test_put_vault(self, client):
        body = {
            "user_id": USER_ID,
            "site": "github.com",
            "account_label": f"{TAG}-personal",
            "env": {"TOKEN": "ghp_abcSECRETvalue123"},
        }
        r = client.put(f"{API}/vault", json=body, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["ok"] is True
        assert data["site"] == "github.com"
        assert "TOKEN" in data["env_keys"]
        TestVault.created_id = data["id"]

    def test_list_vault_no_values(self, client):
        r = client.get(f"{API}/vault", params={"user_id": USER_ID}, timeout=15)
        assert r.status_code == 200
        accounts = r.json()["accounts"]
        ours = [a for a in accounts if a["id"] == TestVault.created_id]
        assert len(ours) == 1
        a = ours[0]
        assert "TOKEN" in a["env_keys"]
        # ensure no decrypted value leaks through
        text = str(a)
        assert "ghp_abcSECRETvalue123" not in text

    def test_reveal_returns_decrypted(self, client):
        r = client.post(f"{API}/vault/reveal", json={
            "user_id": USER_ID, "id": TestVault.created_id, "keys": ["TOKEN"],
        }, timeout=15)
        assert r.status_code == 200, r.text
        vals = r.json()["values"]
        assert vals["TOKEN"] == "ghp_abcSECRETvalue123"

    def test_delete_vault(self, client):
        r = client.delete(f"{API}/vault/{TestVault.created_id}",
                          params={"user_id": USER_ID}, timeout=15)
        assert r.status_code == 200
        assert r.json()["ok"] is True


# ----------------- 4) Model inventory -----------------
class TestInventory:
    def test_inventory_curated_present(self, client):
        r = client.get(f"{API}/models/inventory", params={"user_id": USER_ID}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        models = data.get("models", [])
        # Emergent-curated inventory must yield >= 9 models
        assert len(models) >= 9, f"expected >=9 curated models, got {len(models)}: {models}"
        # Each curated model exposes an id of the form 'provider:name'
        # (the field is 'id' for Emergent inventory, 'model_id' for BYOK providers).
        for m in models:
            ident = m.get("id") or m.get("model_id") or ""
            assert ":" in ident, m
        # errors must be a dict (may be empty)
        assert isinstance(data.get("errors", {}), dict)


# ----------------- 5) Sessions CRUD -----------------
class TestSessions:
    sid = None

    def test_create_session(self, client):
        body = {
            "user_id": USER_ID,
            "title": f"{TAG}-session",
            "system_context": "You are a careful research assistant.",
            "persona": "researcher",
            "selected_models": ["emergent:openai:gpt-4o-mini"],
        }
        r = client.post(f"{API}/sessions", json=body, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["title"] == body["title"]
        assert d["system_context"] == body["system_context"]
        assert d["persona"] == "researcher"
        TestSessions.sid = d["id"]

    def test_get_session(self, client):
        r = client.get(f"{API}/sessions/{TestSessions.sid}",
                       params={"user_id": USER_ID}, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["id"] == TestSessions.sid
        assert d["persona"] == "researcher"

    def test_patch_session(self, client):
        new_ctx = "Updated context — be concise."
        r = client.patch(f"{API}/sessions/{TestSessions.sid}", json={
            "user_id": USER_ID,
            "system_context": new_ctx,
            "selected_models": ["emergent:openai:gpt-4o-mini",
                                "emergent:anthropic:claude-sonnet-4-6"],
        }, timeout=15)
        assert r.status_code == 200, r.text
        # verify persisted
        r2 = client.get(f"{API}/sessions/{TestSessions.sid}",
                        params={"user_id": USER_ID}, timeout=15)
        d = r2.json()
        assert d["system_context"] == new_ctx
        assert len(d["selected_models"]) == 2

    def test_delete_session(self, client):
        r = client.delete(f"{API}/sessions/{TestSessions.sid}",
                          params={"user_id": USER_ID}, timeout=15)
        assert r.status_code == 200
        assert r.json()["ok"] is True
        # verify removal
        r2 = client.get(f"{API}/sessions/{TestSessions.sid}",
                        params={"user_id": USER_ID}, timeout=15)
        assert r2.status_code == 404


# ----------------- 6) Drafts CRUD -----------------
class TestDrafts:
    did = None

    def test_create_draft(self, client):
        r = client.post(f"{API}/drafts", json={
            "user_id": USER_ID, "title": f"{TAG}-draft",
            "content": "initial draft body",
            "tags": ["test", TAG],
        }, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["content"] == "initial draft body"
        TestDrafts.did = d["id"]

    def test_patch_draft(self, client):
        r = client.patch(f"{API}/drafts/{TestDrafts.did}", json={
            "user_id": USER_ID, "title": f"{TAG}-draft",
            "content": "updated body", "tags": ["test", TAG],
        }, timeout=15)
        assert r.status_code == 200, r.text
        # list and verify
        r2 = client.get(f"{API}/drafts", params={"user_id": USER_ID}, timeout=15)
        ours = [x for x in r2.json()["drafts"] if x["id"] == TestDrafts.did]
        assert ours and ours[0]["content"] == "updated body"

    def test_delete_draft(self, client):
        r = client.delete(f"{API}/drafts/{TestDrafts.did}",
                          params={"user_id": USER_ID}, timeout=15)
        assert r.status_code == 200
        assert r.json()["ok"] is True


# ----------------- 7) Chat (Emergent-routed) -----------------
# AI calls may take a few seconds.
class TestChat:
    fanout_results = None

    def test_chat_single(self, client):
        r = client.post(f"{API}/chat/single", json={
            "user_id": USER_ID,
            "model_id": "emergent:openai:gpt-4o-mini",
            "messages": [{"role": "user",
                          "content": "Reply with exactly the word HELLO and nothing else"}],
        }, timeout=90)
        assert r.status_code == 200, r.text
        result = r.json()["result"]
        assert not result.get("error"), f"chat error: {result.get('error')}"
        assert result.get("content", "").strip(), "expected non-empty content"

    def test_chat_fanout(self, client):
        r = client.post(f"{API}/chat/fanout", json={
            "user_id": USER_ID,
            "prompt": "In one short sentence, what is 2+2?",
            "model_ids": ["emergent:openai:gpt-4o-mini",
                          "emergent:anthropic:claude-sonnet-4-6"],
        }, timeout=120)
        assert r.status_code == 200, r.text
        data = r.json()
        results = data.get("results", [])
        assert len(results) == 2, f"expected 2 results, got {len(results)}"
        TestChat.fanout_results = results
        # Each result must have either non-empty content OR a non-null error.
        # Silent empty content with no error indicates a regression in
        # error-propagation through aimmh.fan_out._invoke().
        empties = [item for item in results
                   if not (item.get("content") or item.get("error"))]
        assert not empties, (
            "Silent failure: result(s) have neither content nor error — "
            f"aimmh.patterns._invoke drops the provider error field: {empties}"
        )

    def test_chat_daisychain(self, client):
        r = client.post(f"{API}/chat/daisychain", json={
            "user_id": USER_ID,
            "prompt": "Begin a one-sentence story about a number line.",
            "model_ids": ["emergent:openai:gpt-4o-mini",
                          "emergent:anthropic:claude-sonnet-4-6"],
            "rounds": 1,
        }, timeout=180)
        assert r.status_code == 200, r.text
        data = r.json()
        steps = data.get("steps", [])
        assert len(steps) == 2, f"expected 2 steps, got {len(steps)}"
        for i, s in enumerate(steps):
            assert s["step"] == i + 1
            assert "model_id" in s

    def test_chat_fanout_invalid_model_surfaces_error(self, client):
        """Validates the _invoke fix: invalid emergent model id must yield
        result entry with a non-null 'error' (no silent empty content)."""
        r = client.post(f"{API}/chat/fanout", json={
            "user_id": USER_ID,
            "prompt": "ping",
            "model_ids": ["emergent:openai:does-not-exist"],
        }, timeout=120)
        assert r.status_code == 200, r.text
        results = r.json().get("results", [])
        assert len(results) == 1
        item = results[0]
        # The fix requires that error is propagated (non-null) for invalid IDs
        assert item.get("error"), (
            "Regression: invalid emergent model id produced no error field. "
            f"_invoke must propagate provider error. item={item}"
        )

    def test_chat_synthesize(self, client):
        # Use any prior fanout output OR fall back to fabricated panel content.
        if TestChat.fanout_results:
            responses = [{"model_id": r["model_id"],
                          "content": r.get("content") or "(no content)"}
                         for r in TestChat.fanout_results]
        else:
            responses = [
                {"model_id": "model-a", "content": "2+2 equals 4."},
                {"model_id": "model-b", "content": "The sum of two and two is four."},
            ]
        r = client.post(f"{API}/chat/synthesize", json={
            "user_id": USER_ID,
            "prompt": "In one short sentence, what is 2+2?",
            "responses": responses,
            "synth_model": "emergent:openai:gpt-4o-mini",
        }, timeout=120)
        assert r.status_code == 200, r.text
        synth = r.json()["synthesis"]
        assert not synth.get("error"), f"synth error: {synth.get('error')}"
        assert synth.get("content", "").strip(), "expected non-empty synthesis content"


# ----------------- 8) Inspector -----------------
class TestInspector:
    def test_heartbeat(self, client):
        r = client.post(f"{API}/inspector/heartbeat",
                        json={"intent": "test inspector"}, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "tick" in data
        rs = data.get("ring_signals") or {}
        for ring in ("phi", "psi", "omega", "theta", "sigma", "epsilon"):
            assert ring in rs, f"ring {ring} missing from ring_signals: {list(rs.keys())}"
        assert "edcm" in data
        assert "cores" in data
        assert "memory" in data

    def test_snapshot(self, client):
        r = client.get(f"{API}/inspector/snapshot", timeout=15)
        assert r.status_code == 200
        assert "agent_card" in r.json()


# ----------------- 9) Detachable agents -----------------
class TestAgents:
    new_slug = "prompt-synthesis-hub"

    def test_list_seeded(self, client):
        r = client.get(f"{API}/agents", timeout=15)
        assert r.status_code == 200, r.text
        agents = r.json()["agents"]
        slugs = {a["slug"] for a in agents}
        for required in ("research-council", "daisy-prover",
                         "zfae-classic", "premium-symphony"):
            assert required in slugs, f"starter {required} missing; have {slugs}"
        # Verify starter default_models use only valid Emergent IDs after fix.
        by_slug = {a["slug"]: a for a in agents}
        invalid_ids = {
            "emergent:openai:gpt-5.4",
            "emergent:openai:gpt-5.4-mini",
            "emergent:anthropic:claude-sonnet-4-6",
        }
        for slug in ("research-council", "daisy-prover"):
            dms = by_slug[slug].get("default_models", [])
            assert dms, f"{slug} has empty default_models"
            bad = [m for m in dms if m in invalid_ids]
            assert not bad, f"{slug} still references invalid IDs: {bad} (full={dms})"
            # Sanity: at least one of the allow-listed substitutes should appear
            assert any(
                m in dms for m in (
                    "emergent:openai:gpt-5",
                    "emergent:openai:gpt-5-mini",
                    "emergent:anthropic:claude-sonnet-4-5",
                )
            ), f"{slug} default_models has no recognised valid IDs: {dms}"

    def test_create_agent(self, client):
        # ensure clean slate for our test slug
        client.delete(f"{API}/agents/{TestAgents.new_slug}", timeout=15)
        body = {
            "slug": TestAgents.new_slug,
            "name": "Prompt Synthesis Hub",
            "description": "test agent",
            "system_context": "synthesize prompts",
            "default_models": ["emergent:openai:gpt-4o-mini"],
            "capabilities": ["synthesis"],
            "aimmh_pattern": "fan_out",
            "rounds": 1,
            "is_premium": False,
        }
        r = client.post(f"{API}/agents", json=body, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["slug"] == TestAgents.new_slug
        # Duplicate slug should 409
        r2 = client.post(f"{API}/agents", json=body, timeout=15)
        assert r2.status_code == 409

    def test_manifest(self, client):
        r = client.get(f"{API}/agents/{TestAgents.new_slug}/manifest", timeout=15)
        assert r.status_code == 200, r.text
        m = r.json()
        assert m["slug"] == TestAgents.new_slug
        assert m["manifest_version"].startswith("a0p-agent")
        assert m["tier"] in ("free", "premium")
        assert "aimmh_pattern" in m

    def test_delete_agent(self, client):
        r = client.delete(f"{API}/agents/{TestAgents.new_slug}", timeout=15)
        assert r.status_code == 200
        assert r.json()["ok"] is True


# ----------------- 10) Usage -----------------
class TestUsage:
    def test_usage_records(self, client):
        # The chat tests above generated usage rows.
        r = client.get(f"{API}/usage", params={"user_id": USER_ID, "limit": 100}, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "records" in data
        assert "aggregate" in data
        agg = data["aggregate"]
        assert agg["calls"] >= 1, f"expected >=1 usage call recorded; agg={agg}"
        # Token totals may legitimately be 0 when routed through Emergent.
        assert isinstance(agg.get("total_tokens", 0), int)
        assert isinstance(agg.get("by_provider", {}), dict)
        assert isinstance(agg.get("by_model", {}), dict)

# === CONTRACTS ===
# id: tests_backend_test_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===

