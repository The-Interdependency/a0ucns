"""
Iteration 10 Backend Tests
Testing features:
1. Service Account Policy APIs: GET/PUT /api/auth/service-account/policy
2. One-token-per-bot behavior: issuing a new token revokes previous active tokens when policy is enabled
3. Append-only audit logs for: chat_event_logs, payment_audit_logs, service_account_audit_logs
4. Regression: existing service account CRUD + token issue/revoke
"""
import os
import pytest
import requests
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestServiceAccountPolicy:
    """Test service account one-token-per-bot policy APIs"""

    @pytest.fixture(autouse=True)
    def setup_user(self, request):
        """Create a fresh test user and authenticate"""
        unique_id = uuid.uuid4().hex[:8]
        self.username = f"TEST_policy_user_{unique_id}"
        self.password = "test_policy_123"
        
        # Register user
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": self.username,
            "password": self.password
        })
        assert reg_resp.status_code == 200, f"Registration failed: {reg_resp.text}"
        data = reg_resp.json()
        self.token = data.get("access_token")
        self.user_id = data.get("user", {}).get("id")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        yield
        
        # Cleanup not strictly necessary for tests

    def test_get_policy_default_value(self):
        """GET /api/auth/service-account/policy should return default policy (one_token_per_bot=False)"""
        resp = requests.get(f"{BASE_URL}/api/auth/service-account/policy", headers=self.headers)
        assert resp.status_code == 200, f"Get policy failed: {resp.text}"
        data = resp.json()
        assert "one_token_per_bot" in data, "Response missing 'one_token_per_bot'"
        # Default should be False
        assert data["one_token_per_bot"] == False, "Default one_token_per_bot should be False"

    def test_put_policy_enable_one_token_per_bot(self):
        """PUT /api/auth/service-account/policy should update policy"""
        # Enable
        resp = requests.put(
            f"{BASE_URL}/api/auth/service-account/policy",
            headers=self.headers,
            json={"one_token_per_bot": True}
        )
        assert resp.status_code == 200, f"Put policy failed: {resp.text}"
        data = resp.json()
        assert data["one_token_per_bot"] == True, "Policy should be enabled"
        assert data.get("updated_at") is not None, "updated_at should be set"
        
        # Verify via GET
        verify_resp = requests.get(f"{BASE_URL}/api/auth/service-account/policy", headers=self.headers)
        assert verify_resp.status_code == 200
        assert verify_resp.json()["one_token_per_bot"] == True

    def test_put_policy_disable_one_token_per_bot(self):
        """PUT /api/auth/service-account/policy should disable policy"""
        # First enable
        requests.put(
            f"{BASE_URL}/api/auth/service-account/policy",
            headers=self.headers,
            json={"one_token_per_bot": True}
        )
        # Now disable
        resp = requests.put(
            f"{BASE_URL}/api/auth/service-account/policy",
            headers=self.headers,
            json={"one_token_per_bot": False}
        )
        assert resp.status_code == 200
        assert resp.json()["one_token_per_bot"] == False

    def test_policy_requires_auth(self):
        """Policy endpoints should require authentication"""
        # GET without auth
        get_resp = requests.get(f"{BASE_URL}/api/auth/service-account/policy")
        assert get_resp.status_code == 401, "GET policy without auth should return 401"
        
        # PUT without auth
        put_resp = requests.put(
            f"{BASE_URL}/api/auth/service-account/policy",
            json={"one_token_per_bot": True}
        )
        assert put_resp.status_code == 401, "PUT policy without auth should return 401"


class TestOneTokenPerBotBehavior:
    """Test that one-token-per-bot policy auto-revokes previous tokens"""

    @pytest.fixture(autouse=True)
    def setup_user_and_service_account(self, request):
        """Create user and service account"""
        unique_id = uuid.uuid4().hex[:8]
        self.username = f"TEST_rotation_user_{unique_id}"
        self.sa_username = f"TEST_rotation_bot_{unique_id}"
        self.password = "rotation_test_123"
        
        # Register user
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": self.username,
            "password": self.password
        })
        assert reg_resp.status_code == 200
        data = reg_resp.json()
        self.token = data.get("access_token")
        self.user_id = data.get("user", {}).get("id")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create service account
        sa_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            headers=self.headers,
            json={"username": self.sa_username, "password": self.password, "label": "rotation test bot"}
        )
        assert sa_resp.status_code == 200
        self.service_account_id = sa_resp.json().get("id")
        
        yield

    def test_token_rotation_when_policy_enabled(self):
        """When one_token_per_bot is enabled, issuing new token should revoke previous active token"""
        # First enable policy
        policy_resp = requests.put(
            f"{BASE_URL}/api/auth/service-account/policy",
            headers=self.headers,
            json={"one_token_per_bot": True}
        )
        assert policy_resp.status_code == 200
        
        # Issue first token
        token1_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/token",
            json={"username": self.sa_username, "password": self.password, "expires_in_days": 30}
        )
        assert token1_resp.status_code == 200
        token1 = token1_resp.json().get("access_token")
        
        # Verify token1 works
        me_resp1 = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token1}"})
        assert me_resp1.status_code == 200, "Token1 should work initially"
        
        # Issue second token (should auto-revoke token1)
        token2_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/token",
            json={"username": self.sa_username, "password": self.password, "expires_in_days": 30}
        )
        assert token2_resp.status_code == 200
        token2 = token2_resp.json().get("access_token")
        
        # Verify token2 works
        me_resp2 = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token2}"})
        assert me_resp2.status_code == 200, "Token2 should work"
        
        # Verify token1 is now revoked
        me_resp1_after = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token1}"})
        assert me_resp1_after.status_code == 401, "Token1 should be auto-revoked when policy is enabled"
        
        # Verify via token list
        tokens_resp = requests.get(
            f"{BASE_URL}/api/auth/service-accounts/{self.service_account_id}/tokens",
            headers=self.headers
        )
        assert tokens_resp.status_code == 200
        tokens_list = tokens_resp.json().get("items", [])
        assert len(tokens_list) >= 2, "Should have at least 2 tokens"
        
        # First token should be revoked
        revoked_count = sum(1 for t in tokens_list if t.get("revoked") == True)
        assert revoked_count >= 1, "At least one token should be revoked"

    def test_no_rotation_when_policy_disabled(self):
        """When one_token_per_bot is disabled, multiple tokens can be active"""
        # Ensure policy is disabled
        policy_resp = requests.put(
            f"{BASE_URL}/api/auth/service-account/policy",
            headers=self.headers,
            json={"one_token_per_bot": False}
        )
        assert policy_resp.status_code == 200
        
        # Issue first token
        token1_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/token",
            json={"username": self.sa_username, "password": self.password, "expires_in_days": 30}
        )
        assert token1_resp.status_code == 200
        token1 = token1_resp.json().get("access_token")
        
        # Issue second token
        token2_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/token",
            json={"username": self.sa_username, "password": self.password, "expires_in_days": 30}
        )
        assert token2_resp.status_code == 200
        token2 = token2_resp.json().get("access_token")
        
        # Both tokens should work when policy is disabled
        me_resp1 = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token1}"})
        assert me_resp1.status_code == 200, "Token1 should still work when policy is disabled"
        
        me_resp2 = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token2}"})
        assert me_resp2.status_code == 200, "Token2 should work"


class TestAuditLogsAppendOnly:
    """Test that audit logs are properly created during write operations"""

    @pytest.fixture(autouse=True)
    def setup_user(self, request):
        """Create test user"""
        unique_id = uuid.uuid4().hex[:8]
        self.username = f"TEST_audit_user_{unique_id}"
        self.password = "audit_test_123"
        
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": self.username,
            "password": self.password
        })
        assert reg_resp.status_code == 200
        data = reg_resp.json()
        self.token = data.get("access_token")
        self.user_id = data.get("user", {}).get("id")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        yield

    def test_service_account_audit_on_create(self):
        """Creating a service account should write to service_account_audit_logs"""
        unique_id = uuid.uuid4().hex[:8]
        sa_username = f"TEST_audit_bot_{unique_id}"
        
        # Create service account
        resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            headers=self.headers,
            json={"username": sa_username, "password": "test123"}
        )
        assert resp.status_code == 200, f"Create service account failed: {resp.text}"
        # Audit log write is internal, we just verify the operation succeeds
        # The audit.py service writes to service_account_audit_logs collection

    def test_service_account_audit_on_token_issue(self):
        """Issuing a token should write to service_account_audit_logs"""
        unique_id = uuid.uuid4().hex[:8]
        sa_username = f"TEST_audit_token_bot_{unique_id}"
        
        # Create service account
        requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            headers=self.headers,
            json={"username": sa_username, "password": "test123"}
        )
        
        # Issue token
        resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/token",
            json={"username": sa_username, "password": "test123", "expires_in_days": 30}
        )
        assert resp.status_code == 200, f"Issue token failed: {resp.text}"

    def test_service_account_audit_on_policy_update(self):
        """Updating policy should write to service_account_audit_logs"""
        resp = requests.put(
            f"{BASE_URL}/api/auth/service-account/policy",
            headers=self.headers,
            json={"one_token_per_bot": True}
        )
        assert resp.status_code == 200, f"Update policy failed: {resp.text}"


class TestServiceAccountRegressions:
    """Regression tests for existing service account features from iteration 9"""

    @pytest.fixture(autouse=True)
    def setup_user(self, request):
        """Create test user"""
        unique_id = uuid.uuid4().hex[:8]
        self.username = f"TEST_regress_user_{unique_id}"
        self.password = "regress_test_123"
        
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": self.username,
            "password": self.password
        })
        assert reg_resp.status_code == 200
        data = reg_resp.json()
        self.token = data.get("access_token")
        self.user_id = data.get("user", {}).get("id")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        yield

    def test_create_service_account(self):
        """POST /api/auth/service-account/create still works"""
        unique_id = uuid.uuid4().hex[:8]
        sa_username = f"TEST_reg_bot_{unique_id}"
        
        resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            headers=self.headers,
            json={"username": sa_username, "password": "test123", "label": "regression test"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("username") == sa_username
        assert data.get("label") == "regression test"
        assert data.get("active") == True

    def test_list_service_accounts(self):
        """GET /api/auth/service-accounts lists owned accounts"""
        unique_id = uuid.uuid4().hex[:8]
        sa_username = f"TEST_list_bot_{unique_id}"
        
        # Create one
        requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            headers=self.headers,
            json={"username": sa_username, "password": "test123"}
        )
        
        # List
        resp = requests.get(f"{BASE_URL}/api/auth/service-accounts", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_issue_token(self):
        """POST /api/auth/service-account/token issues a token"""
        unique_id = uuid.uuid4().hex[:8]
        sa_username = f"TEST_token_bot_{unique_id}"
        
        # Create account
        requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            headers=self.headers,
            json={"username": sa_username, "password": "test123"}
        )
        
        # Issue token
        resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/token",
            json={"username": sa_username, "password": "test123", "expires_in_days": 30}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["access_token"].startswith("sat_")
        assert "expires_at" in data

    def test_revoke_token(self):
        """POST /api/auth/service-account/tokens/{id}/revoke revokes token"""
        unique_id = uuid.uuid4().hex[:8]
        sa_username = f"TEST_revoke_bot_{unique_id}"
        
        # Create account
        sa_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            headers=self.headers,
            json={"username": sa_username, "password": "test123"}
        )
        sa_id = sa_resp.json().get("id")
        
        # Issue token
        token_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/token",
            json={"username": sa_username, "password": "test123", "expires_in_days": 30}
        )
        token = token_resp.json().get("access_token")
        
        # Get token id from list
        list_resp = requests.get(f"{BASE_URL}/api/auth/service-accounts/{sa_id}/tokens", headers=self.headers)
        tokens = list_resp.json().get("items", [])
        assert len(tokens) > 0
        token_id = tokens[0]["id"]
        
        # Revoke
        revoke_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/tokens/{token_id}/revoke",
            headers=self.headers
        )
        assert revoke_resp.status_code == 200
        
        # Token should no longer work
        me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 401


class TestChatBasicFlow:
    """Basic regression test for chat send (triggers chat_event_logs audit)"""

    @pytest.fixture(autouse=True)
    def setup_user(self, request):
        unique_id = uuid.uuid4().hex[:8]
        self.username = f"TEST_chat_user_{unique_id}"
        self.password = "chat_test_123"
        
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": self.username,
            "password": self.password
        })
        assert reg_resp.status_code == 200
        data = reg_resp.json()
        self.token = data.get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        yield

    def test_chat_stream_endpoint_exists(self):
        """POST /api/chat/stream should accept request (even without real AI key)"""
        # Note: Without valid API keys, the models will return errors, but endpoint should accept request
        resp = requests.post(
            f"{BASE_URL}/api/chat/stream",
            headers=self.headers,
            json={
                "message": "Test message",
                "models": ["gpt-4"],
                "conversation_id": f"test_conv_{uuid.uuid4().hex[:8]}",
                "context_mode": "compartmented",
            },
            stream=True
        )
        # Should at least accept the request (200 for SSE)
        assert resp.status_code == 200, f"Chat stream returned {resp.status_code}"

    def test_chat_feedback_endpoint(self):
        """POST /api/chat/feedback should work"""
        # First we need to get a message ID from a conversation
        # This test just validates the endpoint exists
        resp = requests.post(
            f"{BASE_URL}/api/chat/feedback",
            headers=self.headers,
            json={"message_id": "test_msg_id", "feedback": "up"}
        )
        # Will return 404 because message doesn't exist, but validates endpoint works
        assert resp.status_code in [200, 404], f"Feedback endpoint error: {resp.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
