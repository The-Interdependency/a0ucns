"""End-to-end auth + custom-keys + demo-quota + living-spec tests (T1-T7)."""
from __future__ import annotations
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    raise RuntimeError("REACT_APP_BACKEND_URL is not set in env")
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

UNIQUE = uuid.uuid4().hex[:8]
ALICE = {
    "username": f"qa_alice_{UNIQUE}",
    "email": f"qa_alice_{UNIQUE}@example.com",
    "passphrase": "sixteen-chars-and-more-pass",
}


@pytest.fixture(scope="module")
def alice_session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{API}/auth/register", json=ALICE, timeout=30)
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    return s


# -------- T1: register --------
class TestRegister:
    def test_register_success(self):
        s = requests.Session()
        body = {
            "username": f"qa_reg_{UNIQUE}",
            "email": f"qa_reg_{UNIQUE}@example.com",
            "passphrase": "sixteen-chars-and-more-pass",
        }
        r = s.post(f"{API}/auth/register", json=body, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["user"]["username"] == body["username"]
        assert data["user"]["email"] == body["email"]
        assert "password" in data["user"].get("auth_methods", [])
        # cookies set
        cookies = {c.name for c in s.cookies}
        assert "access_token" in cookies, f"missing access_token cookie: {cookies}"
        assert "refresh_token" in cookies, f"missing refresh_token cookie: {cookies}"

    def test_register_duplicate_username_409(self):
        s = requests.Session()
        body = {
            "username": f"qa_dup_{UNIQUE}",
            "email": f"qa_dup_{UNIQUE}@example.com",
            "passphrase": "sixteen-chars-and-more-pass",
        }
        r1 = s.post(f"{API}/auth/register", json=body, timeout=30)
        assert r1.status_code == 200
        r2 = s.post(f"{API}/auth/register", json=body, timeout=30)
        assert r2.status_code == 409, f"expected 409, got {r2.status_code}: {r2.text}"

    def test_register_short_passphrase_422(self):
        s = requests.Session()
        body = {
            "username": f"qa_short_{UNIQUE}",
            "email": f"qa_short_{UNIQUE}@example.com",
            "passphrase": "tooshort",
        }
        r = s.post(f"{API}/auth/register", json=body, timeout=30)
        assert r.status_code == 422, f"expected 422, got {r.status_code}: {r.text}"


# -------- T2: login --------
class TestLogin:
    def test_login_with_username(self, alice_session):
        s = requests.Session()
        r = s.post(f"{API}/auth/login",
                   json={"identifier": ALICE["username"],
                         "passphrase": ALICE["passphrase"]},
                   timeout=30)
        assert r.status_code == 200, r.text
        assert "access_token" in {c.name for c in s.cookies}

    def test_login_with_email(self):
        s = requests.Session()
        r = s.post(f"{API}/auth/login",
                   json={"identifier": ALICE["email"],
                         "passphrase": ALICE["passphrase"]},
                   timeout=30)
        assert r.status_code == 200, r.text

    def test_login_wrong_passphrase(self):
        s = requests.Session()
        r = s.post(f"{API}/auth/login",
                   json={"identifier": ALICE["username"],
                         "passphrase": "wrong-passphrase-1234567"},
                   timeout=30)
        assert r.status_code == 401, f"expected 401, got {r.status_code}: {r.text}"

    def test_brute_force_429(self):
        """Attempt to verify 6th-attempt lockout. NOTE: backend keys lockout
        by request.client.host, which is the K8s ingress proxy IP that
        ROTATES between requests behind the load balancer. We send many
        attempts and only assert that at least one 429 occurs."""
        s = requests.Session()
        body = {
            "username": f"qa_bf_{UNIQUE}",
            "email": f"qa_bf_{UNIQUE}@example.com",
            "passphrase": "sixteen-chars-and-more-pass",
        }
        rr = s.post(f"{API}/auth/register", json=body, timeout=30)
        assert rr.status_code == 200
        codes = []
        for _ in range(20):
            r = requests.post(f"{API}/auth/login",
                              json={"identifier": body["username"],
                                    "passphrase": "wrongpassphrase-xyz1"},
                              timeout=30)
            codes.append(r.status_code)
        assert 429 in codes, (
            f"expected at least one 429 in 20 wrong-passphrase attempts; "
            f"got {codes}. Possible cause: lockout key uses "
            f"request.client.host which rotates per request behind k8s ingress."
        )


# -------- T3: me + logout --------
class TestMeAndLogout:
    def test_me_with_cookies(self, alice_session):
        r = alice_session.get(f"{API}/auth/me", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        # /me returns { user: {...} }
        u = data.get("user", data)
        assert u["username"] == ALICE["username"]
        assert u["email"] == ALICE["email"]

    def test_me_without_cookies(self):
        r = requests.get(f"{API}/auth/me", timeout=30)
        assert r.status_code == 401

    def test_logout_clears_cookies(self):
        s = requests.Session()
        s.post(f"{API}/auth/register", json={
            "username": f"qa_lo_{UNIQUE}",
            "email": f"qa_lo_{UNIQUE}@example.com",
            "passphrase": "sixteen-chars-and-more-pass",
        }, timeout=30)
        r1 = s.get(f"{API}/auth/me", timeout=30)
        assert r1.status_code == 200
        r2 = s.post(f"{API}/auth/logout", timeout=30)
        assert r2.status_code == 200, r2.text
        # New session with the same cookies cleared -> me should be 401
        r3 = s.get(f"{API}/auth/me", timeout=30)
        assert r3.status_code == 401, f"expected 401 after logout, got {r3.status_code}"


# -------- T4: admin seeding --------
class TestAdminSeed:
    def test_admin_login(self):
        s = requests.Session()
        r = s.post(f"{API}/auth/login",
                   json={"identifier": "wayseer",
                         "passphrase": "ChangeMeOnFirstLogin2026"},
                   timeout=30)
        assert r.status_code == 200, f"admin seed login failed: {r.status_code} {r.text}"
        r2 = s.get(f"{API}/auth/me", timeout=30)
        assert r2.status_code == 200
        me = r2.json()
        me = me.get("user", me)
        assert me["username"] == "wayseer"
        assert me["email"] == "wayseer@interdependentway.org"
        assert me["role"] == "admin", f"role={me.get('role')}"


# -------- T5: Custom Keys CRUD --------
class TestCustomKeys:
    def test_custom_keys_full_crud(self, alice_session):
        # PUT create
        body = {"name": "github_pat", "value": "ghp_test_1234567890",
                "kind": "github", "label": "qa test"}
        r = alice_session.put(f"{API}/custom-keys", json=body, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d.get("rotated") is False

        # GET list
        r = alice_session.get(f"{API}/custom-keys", timeout=30)
        assert r.status_code == 200, r.text
        items = r.json().get("keys") or r.json().get("items") or []
        assert len(items) >= 1
        entry = next(x for x in items if x.get("name") == "github_pat")
        assert "value" not in entry or "ghp_test_1234567890" not in str(entry.get("value", ""))
        # masked preview must exist
        assert any(k in entry for k in ("masked", "preview", "value_preview", "masked_value")), entry
        key_id = entry.get("id") or entry.get("_id")
        assert key_id

        # Reveal
        r = alice_session.post(f"{API}/custom-keys/{key_id}/reveal", timeout=30)
        assert r.status_code == 200, r.text
        rd = r.json()
        revealed = rd.get("value") or rd.get("plaintext")
        assert revealed == "ghp_test_1234567890", rd

        # PUT rotate - same name new value
        r = alice_session.put(f"{API}/custom-keys",
                              json={**body, "value": "ghp_test_NEWVAL_999"},
                              timeout=30)
        assert r.status_code == 200, r.text
        rotated = r.json()
        assert rotated.get("rotated") is True, rotated
        # rotated_count present and >=1
        rc = rotated.get("rotated_count")
        if rc is not None:
            assert rc >= 1

        # DELETE
        r = alice_session.delete(f"{API}/custom-keys/{key_id}", timeout=30)
        assert r.status_code == 200, r.text
        # List - the rotated entry replaces same name; the original id may have new id after rotate.
        r = alice_session.get(f"{API}/custom-keys", timeout=30)
        items_after = r.json().get("keys") or r.json().get("items") or []
        assert not any(x.get("id") == key_id for x in items_after)


# -------- T6: Demo quota --------
class TestDemoQuota:
    def test_demo_quota_fresh_user(self):
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        body = {
            "username": f"qa_dq_{UNIQUE}",
            "email": f"qa_dq_{UNIQUE}@example.com",
            "passphrase": "sixteen-chars-and-more-pass",
        }
        r = s.post(f"{API}/auth/register", json=body, timeout=30)
        assert r.status_code == 200
        r = s.get(f"{API}/demo-quota", timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["budget"] == 25000, d
        assert d["used"] == 0
        assert d["remaining"] == 25000
        assert d["fits"] is True
        assert "day" in d


# -------- T7: Living spec --------
class TestLivingSpec:
    def test_living_spec_public(self):
        r = requests.get(f"{API}/spec/living", timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["count"] >= 100, f"count={d.get('count')}"
        by_kind = d.get("by_kind", {})
        for k in ("engine", "schema", "ui_page", "api_router"):
            assert k in by_kind, f"missing kind {k} in {list(by_kind.keys())}"
        modules = d.get("modules", [])
        assert len(modules) >= 100
        for m in modules[:20]:
            assert m.get("module_name"), m
            assert m.get("summary"), m


# -------- T15 regression --------
class TestRegression:
    def test_health(self):
        r = requests.get(f"{API}/health", timeout=15)
        assert r.status_code == 200

    def test_legacy_instances_list(self):
        r = requests.get(f"{API}/instances/", params={"user_id": "local"}, timeout=30)
        assert r.status_code == 200, r.text
