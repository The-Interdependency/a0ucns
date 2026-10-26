"""
Test Iteration 9: Service Account Management Features
- Service account CRUD operations
- Token management (issue, list, revoke)
- Protected endpoint access with service tokens
- Basic auth regression (register/login/me)
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

from tests.test_credentials import (
    TEST_SERVICE_ACCOUNT_ALT_PASSWORD,
    TEST_SERVICE_ACCOUNT_PASSWORD,
    TEST_SHORT_ALT_PASSWORD,
    TEST_SHORT_PASSWORD,
    TEST_USER_PASSWORD,
    TEST_USER_WRONG_PASSWORD,
)

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable must be set")


class TestBasicAuthRegression:
    """Verify basic auth flows still work"""
    
    def test_register_new_user(self):
        """Test user registration"""
        username = f"test_sa_reg_{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": username,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["username"] == username
        
    def test_login_with_valid_credentials(self):
        """Test login flow"""
        # First create a user
        username = f"test_sa_login_{uuid.uuid4().hex[:8]}"
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": username,
            "password": TEST_USER_PASSWORD
        })
        assert reg_resp.status_code == 200
        
        # Now login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": username,
            "password": TEST_USER_PASSWORD
        })
        assert login_resp.status_code == 200
        data = login_resp.json()
        assert "access_token" in data
        assert data["user"]["username"] == username
        
    def test_login_with_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "nonexistent_user_xyz",
            "password": TEST_USER_WRONG_PASSWORD
        })
        assert response.status_code == 401
        
    def test_me_endpoint_with_valid_token(self):
        """Test /api/auth/me with valid JWT"""
        # Create user and get token
        username = f"test_sa_me_{uuid.uuid4().hex[:8]}"
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": username,
            "password": TEST_USER_PASSWORD
        })
        assert reg_resp.status_code == 200
        token = reg_resp.json()["access_token"]
        
        # Call /me endpoint
        me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert me_resp.status_code == 200
        data = me_resp.json()
        assert "user_id" in data or "email" in data
        
    def test_me_endpoint_without_token(self):
        """Test /api/auth/me without authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401


class TestServiceAccountCreation:
    """Test service account creation endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Create a test user and return auth token"""
        username = f"test_sa_owner_{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": username,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
        
    def test_create_service_account_success(self, auth_token):
        """Test creating a service account"""
        sa_username = f"bot_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            json={
                "username": sa_username,
                "password": TEST_SERVICE_ACCOUNT_ALT_PASSWORD,
                "label": "Test Bot"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert data["username"] == sa_username
        assert data["label"] == "Test Bot"
        assert data["active"] == True
        assert "id" in data
        assert "owner_user_id" in data
        
    def test_create_service_account_no_label(self, auth_token):
        """Test creating service account without label"""
        sa_username = f"bot_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            json={
                "username": sa_username,
                "password": TEST_SERVICE_ACCOUNT_ALT_PASSWORD
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == sa_username
        assert data["label"] is None
        
    def test_create_service_account_duplicate_username(self, auth_token):
        """Test creating service account with duplicate username"""
        sa_username = f"bot_{uuid.uuid4().hex[:8]}"
        # Create first
        response1 = requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            json={"username": sa_username, "password": TEST_SHORT_PASSWORD},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response1.status_code == 200
        
        # Try to create duplicate
        response2 = requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            json={"username": sa_username, "password": TEST_SHORT_ALT_PASSWORD},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response2.status_code == 400
        assert "already in use" in response2.json()["detail"].lower()
        
    def test_create_service_account_requires_auth(self):
        """Test that creating service account requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            json={"username": "bot_test", "password": TEST_SHORT_PASSWORD}
        )
        assert response.status_code == 401


class TestServiceAccountListing:
    """Test service account listing endpoint"""
    
    @pytest.fixture
    def user_with_service_accounts(self):
        """Create user with some service accounts"""
        username = f"test_sa_list_{uuid.uuid4().hex[:8]}"
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": username,
            "password": TEST_USER_PASSWORD
        })
        assert reg_resp.status_code == 200
        token = reg_resp.json()["access_token"]
        
        # Create 2 service accounts
        sa_ids = []
        for i in range(2):
            sa_resp = requests.post(
                f"{BASE_URL}/api/auth/service-account/create",
                json={
                    "username": f"bot_{uuid.uuid4().hex[:8]}",
                    "password": TEST_SERVICE_ACCOUNT_PASSWORD,
                    "label": f"Bot {i+1}"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            assert sa_resp.status_code == 200
            sa_ids.append(sa_resp.json()["id"])
            
        return {"token": token, "sa_ids": sa_ids}
        
    def test_list_service_accounts(self, user_with_service_accounts):
        """Test listing owned service accounts"""
        token = user_with_service_accounts["token"]
        response = requests.get(
            f"{BASE_URL}/api/auth/service-accounts",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 2
        
        # Verify structure
        for item in data["items"]:
            assert "id" in item
            assert "username" in item
            assert "active" in item
            assert "created_at" in item
            
    def test_list_service_accounts_requires_auth(self):
        """Test that listing requires authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/service-accounts")
        assert response.status_code == 401


class TestServiceAccountUpdate:
    """Test service account update (toggle active, update label)"""
    
    @pytest.fixture
    def service_account_setup(self):
        """Create user and service account for testing"""
        username = f"test_sa_update_{uuid.uuid4().hex[:8]}"
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": username,
            "password": TEST_USER_PASSWORD
        })
        assert reg_resp.status_code == 200
        token = reg_resp.json()["access_token"]
        
        sa_username = f"bot_{uuid.uuid4().hex[:8]}"
        sa_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            json={
                "username": sa_username,
                "password": TEST_SERVICE_ACCOUNT_PASSWORD,
                "label": "Original Label"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert sa_resp.status_code == 200
        
        return {
            "token": token,
            "sa_id": sa_resp.json()["id"],
            "sa_username": sa_username
        }
        
    def test_toggle_service_account_active(self, service_account_setup):
        """Test disabling and enabling a service account"""
        token = service_account_setup["token"]
        sa_id = service_account_setup["sa_id"]
        
        # Disable
        disable_resp = requests.patch(
            f"{BASE_URL}/api/auth/service-accounts/{sa_id}",
            json={"active": False},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert disable_resp.status_code == 200
        assert disable_resp.json()["active"] == False
        
        # Enable
        enable_resp = requests.patch(
            f"{BASE_URL}/api/auth/service-accounts/{sa_id}",
            json={"active": True},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert enable_resp.status_code == 200
        assert enable_resp.json()["active"] == True
        
    def test_update_service_account_label(self, service_account_setup):
        """Test updating service account label"""
        token = service_account_setup["token"]
        sa_id = service_account_setup["sa_id"]
        
        response = requests.patch(
            f"{BASE_URL}/api/auth/service-accounts/{sa_id}",
            json={"label": "Updated Label"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["label"] == "Updated Label"
        
    def test_update_nonexistent_service_account(self, service_account_setup):
        """Test updating a non-existent service account"""
        token = service_account_setup["token"]
        response = requests.patch(
            f"{BASE_URL}/api/auth/service-accounts/nonexistent-id",
            json={"active": False},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
        
    def test_update_service_account_requires_auth(self, service_account_setup):
        """Test that update requires authentication"""
        sa_id = service_account_setup["sa_id"]
        response = requests.patch(
            f"{BASE_URL}/api/auth/service-accounts/{sa_id}",
            json={"active": False}
        )
        assert response.status_code == 401


class TestServiceAccountTokenIssuance:
    """Test service account token issuance"""
    
    @pytest.fixture
    def service_account_setup(self):
        """Create user and service account"""
        username = f"test_sa_token_{uuid.uuid4().hex[:8]}"
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": username,
            "password": TEST_USER_PASSWORD
        })
        assert reg_resp.status_code == 200
        token = reg_resp.json()["access_token"]
        
        sa_username = f"bot_{uuid.uuid4().hex[:8]}"
        sa_password = TEST_SERVICE_ACCOUNT_PASSWORD
        sa_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            json={
                "username": sa_username,
                "password": sa_password,
                "label": "Token Test Bot"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert sa_resp.status_code == 200
        
        return {
            "user_token": token,
            "sa_id": sa_resp.json()["id"],
            "sa_username": sa_username,
            "sa_password": sa_password
        }
        
    def test_issue_service_token(self, service_account_setup):
        """Test issuing a service account token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/service-account/token",
            json={
                "username": service_account_setup["sa_username"],
                "password": service_account_setup["sa_password"],
                "expires_in_days": 30
            }
        )
        assert response.status_code == 200, f"Token issue failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["access_token"].startswith("sat_")
        assert "expires_at" in data
        assert data["service_account_username"] == service_account_setup["sa_username"]
        
    def test_issue_token_invalid_password(self, service_account_setup):
        """Test issuing token with wrong password"""
        response = requests.post(
            f"{BASE_URL}/api/auth/service-account/token",
            json={
                "username": service_account_setup["sa_username"],
                "password": TEST_USER_WRONG_PASSWORD,
                "expires_in_days": 30
            }
        )
        assert response.status_code == 401
        
    def test_issue_token_nonexistent_account(self):
        """Test issuing token for non-existent account"""
        response = requests.post(
            f"{BASE_URL}/api/auth/service-account/token",
            json={
                "username": "nonexistent_bot_xyz",
                "password": TEST_SHORT_ALT_PASSWORD,
                "expires_in_days": 30
            }
        )
        assert response.status_code == 401
        
    def test_issue_token_disabled_account(self, service_account_setup):
        """Test issuing token for disabled service account"""
        # Disable the account
        disable_resp = requests.patch(
            f"{BASE_URL}/api/auth/service-accounts/{service_account_setup['sa_id']}",
            json={"active": False},
            headers={"Authorization": f"Bearer {service_account_setup['user_token']}"}
        )
        assert disable_resp.status_code == 200
        
        # Try to issue token
        response = requests.post(
            f"{BASE_URL}/api/auth/service-account/token",
            json={
                "username": service_account_setup["sa_username"],
                "password": service_account_setup["sa_password"],
                "expires_in_days": 30
            }
        )
        assert response.status_code == 401


class TestServiceAccountTokenListing:
    """Test listing tokens for a service account"""
    
    @pytest.fixture
    def service_account_with_tokens(self):
        """Create user, service account, and some tokens"""
        username = f"test_sa_tlist_{uuid.uuid4().hex[:8]}"
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": username,
            "password": TEST_USER_PASSWORD
        })
        assert reg_resp.status_code == 200
        user_token = reg_resp.json()["access_token"]
        
        sa_username = f"bot_{uuid.uuid4().hex[:8]}"
        sa_password = TEST_SERVICE_ACCOUNT_PASSWORD
        sa_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            json={"username": sa_username, "password": sa_password},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert sa_resp.status_code == 200
        sa_id = sa_resp.json()["id"]
        
        # Issue 2 tokens
        issued_tokens = []
        for _ in range(2):
            tok_resp = requests.post(
                f"{BASE_URL}/api/auth/service-account/token",
                json={
                    "username": sa_username,
                    "password": sa_password,
                    "expires_in_days": 30
                }
            )
            assert tok_resp.status_code == 200
            issued_tokens.append(tok_resp.json()["access_token"])
            
        return {
            "user_token": user_token,
            "sa_id": sa_id,
            "issued_tokens": issued_tokens
        }
        
    def test_list_tokens_for_service_account(self, service_account_with_tokens):
        """Test listing tokens"""
        response = requests.get(
            f"{BASE_URL}/api/auth/service-accounts/{service_account_with_tokens['sa_id']}/tokens",
            headers={"Authorization": f"Bearer {service_account_with_tokens['user_token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 2
        
        # Verify structure
        for item in data["items"]:
            assert "id" in item
            assert "token_prefix" in item
            assert "revoked" in item
            assert "created_at" in item
            assert "expires_at" in item
            
    def test_list_tokens_nonexistent_account(self, service_account_with_tokens):
        """Test listing tokens for non-existent service account"""
        response = requests.get(
            f"{BASE_URL}/api/auth/service-accounts/nonexistent-id/tokens",
            headers={"Authorization": f"Bearer {service_account_with_tokens['user_token']}"}
        )
        assert response.status_code == 404
        
    def test_list_tokens_requires_auth(self, service_account_with_tokens):
        """Test that listing tokens requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/auth/service-accounts/{service_account_with_tokens['sa_id']}/tokens"
        )
        assert response.status_code == 401


class TestServiceAccountTokenRevocation:
    """Test token revocation"""
    
    @pytest.fixture
    def token_to_revoke(self):
        """Create user, service account, and a token to revoke"""
        username = f"test_sa_revoke_{uuid.uuid4().hex[:8]}"
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": username,
            "password": TEST_USER_PASSWORD
        })
        assert reg_resp.status_code == 200
        user_token = reg_resp.json()["access_token"]
        
        sa_username = f"bot_{uuid.uuid4().hex[:8]}"
        sa_password = TEST_SERVICE_ACCOUNT_PASSWORD
        sa_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            json={"username": sa_username, "password": sa_password},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert sa_resp.status_code == 200
        sa_id = sa_resp.json()["id"]
        
        # Issue a token
        tok_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/token",
            json={
                "username": sa_username,
                "password": sa_password,
                "expires_in_days": 30
            }
        )
        assert tok_resp.status_code == 200
        service_token = tok_resp.json()["access_token"]
        
        # Get token id
        list_resp = requests.get(
            f"{BASE_URL}/api/auth/service-accounts/{sa_id}/tokens",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert list_resp.status_code == 200
        token_id = list_resp.json()["items"][0]["id"]
        
        return {
            "user_token": user_token,
            "sa_id": sa_id,
            "token_id": token_id,
            "service_token": service_token
        }
        
    def test_revoke_token(self, token_to_revoke):
        """Test revoking a service token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/service-account/tokens/{token_to_revoke['token_id']}/revoke",
            headers={"Authorization": f"Bearer {token_to_revoke['user_token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Token revoked"
        assert data["token_id"] == token_to_revoke["token_id"]
        
    def test_revoke_already_revoked_token(self, token_to_revoke):
        """Test revoking an already revoked token"""
        # Revoke first time
        requests.post(
            f"{BASE_URL}/api/auth/service-account/tokens/{token_to_revoke['token_id']}/revoke",
            headers={"Authorization": f"Bearer {token_to_revoke['user_token']}"}
        )
        
        # Revoke second time
        response = requests.post(
            f"{BASE_URL}/api/auth/service-account/tokens/{token_to_revoke['token_id']}/revoke",
            headers={"Authorization": f"Bearer {token_to_revoke['user_token']}"}
        )
        assert response.status_code == 200
        assert "already revoked" in response.json()["message"].lower()
        
    def test_revoke_nonexistent_token(self, token_to_revoke):
        """Test revoking non-existent token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/service-account/tokens/nonexistent-token-id/revoke",
            headers={"Authorization": f"Bearer {token_to_revoke['user_token']}"}
        )
        assert response.status_code == 404
        
    def test_revoke_requires_auth(self, token_to_revoke):
        """Test that revocation requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/auth/service-account/tokens/{token_to_revoke['token_id']}/revoke"
        )
        assert response.status_code == 401


class TestProtectedEndpointsWithServiceToken:
    """Test that service tokens work for protected endpoints and revoked tokens are rejected"""
    
    @pytest.fixture
    def service_token_setup(self):
        """Create user, service account, and issue token"""
        username = f"test_sa_protect_{uuid.uuid4().hex[:8]}"
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": username,
            "password": TEST_USER_PASSWORD
        })
        assert reg_resp.status_code == 200
        user_token = reg_resp.json()["access_token"]
        
        sa_username = f"bot_{uuid.uuid4().hex[:8]}"
        sa_password = TEST_SERVICE_ACCOUNT_PASSWORD
        sa_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/create",
            json={"username": sa_username, "password": sa_password},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert sa_resp.status_code == 200
        sa_id = sa_resp.json()["id"]
        
        # Issue a token
        tok_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/token",
            json={
                "username": sa_username,
                "password": sa_password,
                "expires_in_days": 30
            }
        )
        assert tok_resp.status_code == 200
        service_token = tok_resp.json()["access_token"]
        
        # Get token id for revocation
        list_resp = requests.get(
            f"{BASE_URL}/api/auth/service-accounts/{sa_id}/tokens",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert list_resp.status_code == 200
        token_id = list_resp.json()["items"][0]["id"]
        
        return {
            "user_token": user_token,
            "service_token": service_token,
            "token_id": token_id
        }
        
    def test_service_token_accesses_protected_endpoint(self, service_token_setup):
        """Test that valid service token can access /api/auth/me"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {service_token_setup['service_token']}"}
        )
        assert response.status_code == 200, f"Service token rejected: {response.text}"
        data = response.json()
        assert "user_id" in data or "email" in data
        
    def test_revoked_token_rejected(self, service_token_setup):
        """Test that revoked service token is rejected"""
        # First verify token works
        pre_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {service_token_setup['service_token']}"}
        )
        assert pre_response.status_code == 200
        
        # Revoke the token
        revoke_resp = requests.post(
            f"{BASE_URL}/api/auth/service-account/tokens/{service_token_setup['token_id']}/revoke",
            headers={"Authorization": f"Bearer {service_token_setup['user_token']}"}
        )
        assert revoke_resp.status_code == 200
        
        # Now token should be rejected
        post_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {service_token_setup['service_token']}"}
        )
        assert post_response.status_code == 401, f"Revoked token should be rejected but got {post_response.status_code}"
        
    def test_jwt_still_works(self, service_token_setup):
        """Test that regular JWT tokens still work"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {service_token_setup['user_token']}"}
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
