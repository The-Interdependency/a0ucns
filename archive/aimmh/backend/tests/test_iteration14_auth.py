"""
Iteration 14: OAuth and Standard Auth Tests
Tests for:
1. Backend /api/auth/google/session response includes access_token and token_type
2. Standard auth login/register flow and JWT token validation
3. No regression in existing auth endpoints
"""

import pytest
import requests
import os
import time

from tests.test_credentials import TEST_AUTH_STRONG_PASSWORD, TEST_USER_WRONG_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')


class TestStandardAuth:
    """Test standard username/password auth flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.timestamp = int(time.time())
        self.test_username = f"testauth_{self.timestamp}"
        self.test_password = TEST_AUTH_STRONG_PASSWORD
    
    def test_register_returns_access_token(self):
        """POST /api/auth/register should return access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": self.test_username,
            "password": self.test_password
        })
        assert response.status_code == 200, f"Register failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "access_token missing from register response"
        assert "token_type" in data, "token_type missing from register response"
        assert data["token_type"] == "bearer", f"Expected token_type 'bearer', got {data['token_type']}"
        assert "user" in data, "user missing from register response"
        assert isinstance(data["access_token"], str) and len(data["access_token"]) > 0
        
        # Verify user structure
        user = data["user"]
        assert "id" in user
        assert user["username"] == self.test_username
        assert "created_at" in user
        
    def test_login_returns_access_token(self):
        """POST /api/auth/login should return access_token"""
        # First register
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": f"logintest_{self.timestamp}",
            "password": self.test_password
        })
        assert register_response.status_code == 200
        
        # Then login
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": f"logintest_{self.timestamp}",
            "password": self.test_password
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        
    def test_login_invalid_credentials_returns_401(self):
        """POST /api/auth/login with invalid credentials should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "nonexistent_user_xyz",
            "password": TEST_USER_WRONG_PASSWORD
        })
        assert response.status_code == 401
        
    def test_auth_me_with_valid_token(self):
        """GET /api/auth/me with valid token should return user info"""
        # Register to get token
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": f"metest_{self.timestamp}",
            "password": self.test_password
        })
        assert register_response.status_code == 200
        token = register_response.json()["access_token"]
        
        # Call /api/auth/me with token
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "email" in data or "name" in data
        
    def test_auth_me_without_token_returns_401(self):
        """GET /api/auth/me without token should return 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401


class TestGoogleAuthSessionSchema:
    """Test /api/auth/google/session response schema
    
    Note: We cannot fully test Google OAuth flow externally, 
    but we can verify the schema includes the new fields.
    """
    
    def test_google_session_without_session_id_returns_400(self):
        """POST /api/auth/google/session without X-Session-ID should return 400"""
        response = requests.post(f"{BASE_URL}/api/auth/google/session")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "session" in data["detail"].lower() or "id" in data["detail"].lower()
        
    def test_google_session_with_invalid_session_returns_401(self):
        """POST /api/auth/google/session with invalid session should return 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/session",
            headers={"X-Session-ID": "invalid_session_xyz"}
        )
        # Should return 401 for invalid session
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"


class TestTokenPersistence:
    """Test that tokens work for subsequent requests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.timestamp = int(time.time())
        
    def test_token_can_access_protected_endpoints(self):
        """Verify JWT token works for protected endpoints"""
        # Register
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": f"protectedtest_{self.timestamp}",
            "password": TEST_AUTH_STRONG_PASSWORD
        })
        assert register_response.status_code == 200
        token = register_response.json()["access_token"]
        
        # Access protected endpoint
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        
        # Try accessing another protected endpoint (service-accounts)
        sa_response = requests.get(
            f"{BASE_URL}/api/auth/service-accounts",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert sa_response.status_code == 200
        

class TestAuthModelSchema:
    """Verify the GoogleAuthUser model includes access_token field"""
    
    def test_google_auth_model_has_access_token_field(self):
        """Verify GoogleAuthUser Pydantic model includes access_token"""
        # This is a code-level verification - we import the model
        import sys
        sys.path.insert(0, '/app/backend')
        
        from models.auth import GoogleAuthUser
        
        # Check model fields
        fields = GoogleAuthUser.model_fields
        assert "access_token" in fields, "GoogleAuthUser missing access_token field"
        assert "token_type" in fields, "GoogleAuthUser missing token_type field"
        
        # Verify field properties
        access_token_field = fields["access_token"]
        token_type_field = fields["token_type"]
        
        # access_token should be Optional
        # token_type should have default "bearer"
        assert str(token_type_field.default) == "bearer", f"token_type default should be 'bearer', got {token_type_field.default}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
