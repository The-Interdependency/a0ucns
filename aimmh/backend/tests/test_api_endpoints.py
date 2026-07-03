"""
Backend API Tests for Multi-AI Hub - Post-Refactoring Verification
Tests all critical endpoints after backend modularization
"""
import pytest
import requests
import os
import uuid

from tests.test_credentials import TEST_FAKE_API_KEY, TEST_SHORT_PASSWORD, TEST_USER_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USERNAME = f"testuser_refactor_{uuid.uuid4().hex[:8]}"
TEST_PASSWORD = TEST_USER_PASSWORD


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Register a new test user and get auth token"""
    # Try to register first
    register_response = api_client.post(
        f"{BASE_URL}/api/auth/register",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    
    if register_response.status_code == 200:
        data = register_response.json()
        return data.get("access_token")
    
    # If registration fails (user exists), try login
    login_response = api_client.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    
    if login_response.status_code == 200:
        data = login_response.json()
        return data.get("access_token")
    
    pytest.skip(f"Authentication failed - cannot proceed with tests")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestHealthEndpoints:
    """Basic health and root endpoint tests"""
    
    def test_root_endpoint(self, api_client):
        """Test root /api/ endpoint returns success"""
        response = api_client.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Multi-AI Chat API" in data["message"]
        print(f"✓ Root endpoint working: {data}")


class TestAuthEndpoints:
    """Authentication flow tests - register, login, me"""
    
    def test_register_new_user(self, api_client):
        """Test user registration flow"""
        unique_username = f"test_register_{uuid.uuid4().hex[:8]}"
        response = api_client.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": unique_username, "password": TEST_USER_PASSWORD}
        )
        
        assert response.status_code == 200, f"Register failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data, "Missing access_token in response"
        assert "user" in data, "Missing user in response"
        assert data["user"]["username"] == unique_username
        assert "id" in data["user"]
        print(f"✓ Registration successful for {unique_username}")
    
    def test_register_duplicate_user(self, api_client):
        """Test duplicate registration returns error"""
        # First registration
        unique_username = f"test_dup_{uuid.uuid4().hex[:8]}"
        api_client.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": unique_username, "password": TEST_USER_PASSWORD}
        )
        
        # Duplicate registration
        response = api_client.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": unique_username, "password": TEST_USER_PASSWORD}
        )
        
        assert response.status_code == 400, "Should fail for duplicate username"
        print("✓ Duplicate registration correctly rejected")
    
    def test_login_success(self, api_client):
        """Test login with valid credentials"""
        # Create user first
        unique_username = f"test_login_{uuid.uuid4().hex[:8]}"
        api_client.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": unique_username, "password": TEST_USER_PASSWORD}
        )
        
        # Login
        response = api_client.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": unique_username, "password": TEST_USER_PASSWORD}
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["username"] == unique_username
        print(f"✓ Login successful, token received")
    
    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials returns 401"""
        response = api_client.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "nonexistent_user_xyz", "password": TEST_SHORT_PASSWORD}
        )
        
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected with 401")
    
    def test_get_current_user_me(self, authenticated_client):
        """Test /api/auth/me returns correct user info"""
        response = authenticated_client.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 200, f"Get /me failed: {response.text}"
        data = response.json()
        
        # Verify user info fields exist
        assert "user_id" in data or "email" in data
        print(f"✓ /api/auth/me returned user info: {data}")
    
    def test_me_without_auth(self, api_client):
        """Test /api/auth/me without token returns 401"""
        # Use fresh session without auth
        fresh_session = requests.Session()
        response = fresh_session.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 401 or response.status_code == 403
        print("✓ /api/auth/me correctly requires authentication")


class TestAPIKeysEndpoints:
    """API Key management tests"""
    
    def test_get_keys(self, authenticated_client):
        """Test GET /api/keys returns key info"""
        response = authenticated_client.get(f"{BASE_URL}/api/keys")
        
        assert response.status_code == 200, f"Get keys failed: {response.text}"
        data = response.json()
        
        # Verify expected providers exist in response
        expected_providers = ["gpt", "claude", "gemini", "grok", "deepseek", "perplexity"]
        for provider in expected_providers:
            assert provider in data, f"Missing provider: {provider}"
        print(f"✓ GET /api/keys returned: {data}")
    
    def test_update_key_universal(self, authenticated_client):
        """Test PUT /api/keys with universal toggle"""
        response = authenticated_client.put(
            f"{BASE_URL}/api/keys",
            json={"provider": "gpt", "use_universal": True}
        )
        
        assert response.status_code == 200, f"Update keys failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ PUT /api/keys with universal toggle: {data}")
        
        # Verify the update persisted
        get_response = authenticated_client.get(f"{BASE_URL}/api/keys")
        assert get_response.status_code == 200
        keys_data = get_response.json()
        assert keys_data.get("gpt") == "UNIVERSAL"
        print("✓ Universal key setting persisted correctly")
    
    def test_update_key_custom(self, authenticated_client):
        """Test PUT /api/keys with custom API key"""
        test_key = TEST_FAKE_API_KEY
        response = authenticated_client.put(
            f"{BASE_URL}/api/keys",
            json={"provider": "grok", "api_key": test_key, "use_universal": False}
        )
        
        assert response.status_code == 200
        print("✓ PUT /api/keys with custom key succeeded")


class TestConversationsEndpoints:
    """Conversation management tests"""
    
    def test_get_conversations(self, authenticated_client):
        """Test GET /api/conversations returns list"""
        response = authenticated_client.get(f"{BASE_URL}/api/conversations")
        
        assert response.status_code == 200, f"Get conversations failed: {response.text}"
        data = response.json()
        
        # Should return a list (empty or with conversations)
        assert isinstance(data, list), "Conversations should return a list"
        print(f"✓ GET /api/conversations returned {len(data)} conversations")


class TestChatFeedbackEndpoint:
    """Chat feedback (thumbs up/down) tests - previously reported as broken"""
    
    def test_feedback_invalid_message_id(self, authenticated_client):
        """Test POST /api/chat/feedback with invalid message_id returns 404"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/chat/feedback",
            json={"message_id": "nonexistent_message_id_xyz", "feedback": "up"}
        )
        
        assert response.status_code == 404, f"Expected 404 for invalid message_id, got {response.status_code}"
        print("✓ POST /api/chat/feedback with invalid ID correctly returns 404")
    
    def test_feedback_valid_format(self, authenticated_client):
        """Test feedback endpoint accepts valid format"""
        # This will likely return 404 since no real message exists, 
        # but it tests the endpoint is reachable and validates input
        response = authenticated_client.post(
            f"{BASE_URL}/api/chat/feedback",
            json={"message_id": "test_message_123", "feedback": "down"}
        )
        
        # 404 is acceptable (message not found), anything else indicates endpoint issues
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}, {response.text}"
        print(f"✓ POST /api/chat/feedback endpoint functional, returned {response.status_code}")


class TestExportEndpoint:
    """Conversation export tests"""
    
    def test_export_nonexistent_conversation(self, authenticated_client):
        """Test export with nonexistent conversation returns 404"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/conversations/nonexistent_conv_xyz/export",
            params={"format": "json"}
        )
        
        assert response.status_code == 404
        print("✓ Export nonexistent conversation correctly returns 404")


class TestAgentZeroEndpoints:
    """Agent Zero integration tests"""
    
    def test_a0_health_check(self, authenticated_client):
        """Test GET /api/a0/health returns status (unreachable is OK)"""
        response = authenticated_client.get(f"{BASE_URL}/api/a0/health")
        
        assert response.status_code == 200, f"A0 health check failed: {response.text}"
        data = response.json()
        
        # Should have status field
        assert "status" in data
        # Valid statuses: connected, unreachable, not_configured
        valid_statuses = ["connected", "unreachable", "not_configured", "error"]
        assert data["status"] in valid_statuses, f"Unexpected A0 status: {data['status']}"
        print(f"✓ GET /api/a0/health returned status: {data}")


class TestProtectedEndpoints:
    """Verify protected endpoints require authentication"""
    
    def test_keys_requires_auth(self):
        """Test /api/keys requires authentication"""
        fresh_session = requests.Session()
        response = fresh_session.get(f"{BASE_URL}/api/keys")
        assert response.status_code in [401, 403]
        print("✓ /api/keys requires authentication")
    
    def test_conversations_requires_auth(self):
        """Test /api/conversations requires authentication"""
        fresh_session = requests.Session()
        response = fresh_session.get(f"{BASE_URL}/api/conversations")
        assert response.status_code in [401, 403]
        print("✓ /api/conversations requires authentication")
    
    def test_a0_health_requires_auth(self):
        """Test /api/a0/health requires authentication"""
        fresh_session = requests.Session()
        response = fresh_session.get(f"{BASE_URL}/api/a0/health")
        assert response.status_code in [401, 403]
        print("✓ /api/a0/health requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
