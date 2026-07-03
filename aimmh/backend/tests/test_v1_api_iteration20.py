"""
Iteration 20: Comprehensive backend API tests for the Multi-Model Hub v1 API surface.

Tests covered:
- Auth endpoints: login with configured test credentials
- v1 System endpoints: /health, /models
- v1 a0 endpoints: /prompt, /prompt-single, /history, /feedback
- v1 EDCM endpoint: /eval
- v1 Keys endpoint: GET /keys
"""

import os
import pytest
import requests
import time

from tests.test_credentials import TEST_USER_PASSWORD, TEST_USER_WRONG_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USERNAME = "testbot01"
TEST_PASSWORD = TEST_USER_PASSWORD


class TestAuth:
    """Authentication endpoint tests"""

    def test_login_success(self):
        """POST /api/auth/login - successful login returns token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Missing access_token in response"
        assert "user" in data, "Missing user in response"
        assert data["user"]["username"] == TEST_USERNAME

    def test_login_invalid_credentials(self):
        """POST /api/auth/login - invalid credentials returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "wrong_user", "password": TEST_USER_WRONG_PASSWORD}
        )
        assert response.status_code == 401


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for protected endpoints"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestSystemEndpoints:
    """V1 System endpoints - /api/v1/health, /models"""

    def test_health_check(self):
        """GET /api/v1/health - returns ok status"""
        response = requests.get(f"{BASE_URL}/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok", f"Health check failed: {data}"
        assert "build" in data

    def test_models_list(self):
        """GET /api/v1/models - returns list of developers with models"""
        response = requests.get(f"{BASE_URL}/api/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert "developers" in data
        developers = data["developers"]
        assert len(developers) >= 6, f"Expected at least 6 developers, got {len(developers)}"
        
        # Verify expected developers are present
        dev_ids = [d["developer_id"] for d in developers]
        expected_devs = ["openai", "anthropic", "google", "xai", "deepseek", "perplexity"]
        for expected in expected_devs:
            assert expected in dev_ids, f"Missing developer: {expected}"
        
        # Verify each developer has models
        for dev in developers:
            assert "models" in dev, f"Developer {dev['developer_id']} missing models"
            assert len(dev["models"]) > 0, f"Developer {dev['developer_id']} has no models"


class TestKeysEndpoints:
    """V1 Keys endpoints - /api/v1/keys"""

    def test_get_keys_status(self, auth_headers):
        """GET /api/v1/keys - returns key status list"""
        response = requests.get(f"{BASE_URL}/api/v1/keys", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Expected list of key statuses"
        assert len(data) >= 6, f"Expected at least 6 developer keys, got {len(data)}"
        
        # Verify structure of each key status
        for key_status in data:
            assert "developer_id" in key_status
            assert "status" in key_status
            # Emergent developers should show 'universal' if no custom key set
            if key_status["developer_id"] in ["openai", "anthropic", "google"]:
                assert key_status["status"] in ["universal", "configured", "missing"]


class TestA0Endpoints:
    """V1 a0 endpoints - prompt, prompt-single, history, feedback"""

    def test_history_endpoint(self, auth_headers):
        """GET /api/v1/a0/history - returns thread list"""
        response = requests.get(f"{BASE_URL}/api/v1/a0/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "threads" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data
        
        # Verify thread structure if any exist
        if data["threads"]:
            thread = data["threads"][0]
            assert "thread_id" in thread
            assert "title" in thread
            assert "created_at" in thread

    def test_prompt_single_endpoint(self, auth_headers):
        """POST /api/v1/a0/prompt-single - single model call with auth"""
        response = requests.post(
            f"{BASE_URL}/api/v1/a0/prompt-single",
            headers=auth_headers,
            json={
                "message": "Say exactly: Test successful",
                "model": "gpt-4o-mini"
            }
        )
        assert response.status_code == 200, f"Prompt-single failed: {response.text}"
        data = response.json()
        assert "thread_id" in data
        assert "responses" in data
        assert len(data["responses"]) == 1
        
        resp = data["responses"][0]
        assert resp["model"] == "gpt-4o-mini"
        assert "content" in resp
        assert "message_id" in resp

    def test_prompt_multi_model(self, auth_headers):
        """POST /api/v1/a0/prompt - multi-model call"""
        response = requests.post(
            f"{BASE_URL}/api/v1/a0/prompt",
            headers=auth_headers,
            json={
                "message": "Say 'hello' in one word only.",
                "models": ["gpt-4o-mini"]
            }
        )
        assert response.status_code == 200, f"Prompt failed: {response.text}"
        data = response.json()
        assert "thread_id" in data
        assert "responses" in data
        assert "provenance" in data
        assert "sentinel_context" in data

    def test_feedback_endpoint(self, auth_headers):
        """POST /api/v1/a0/feedback - submit feedback"""
        # First, get a message ID from history
        history_resp = requests.get(f"{BASE_URL}/api/v1/a0/history", headers=auth_headers)
        threads = history_resp.json().get("threads", [])
        
        if not threads:
            pytest.skip("No threads available for feedback test")
        
        # Get messages from first thread
        thread_id = threads[0]["thread_id"]
        thread_resp = requests.get(f"{BASE_URL}/api/v1/a0/thread/{thread_id}", headers=auth_headers)
        messages = thread_resp.json()
        
        # Find an assistant message
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
        if not assistant_msgs:
            pytest.skip("No assistant messages for feedback test")
        
        message_id = assistant_msgs[0]["message_id"]
        
        # Submit feedback
        response = requests.post(
            f"{BASE_URL}/api/v1/a0/feedback",
            headers=auth_headers,
            json={"message_id": message_id, "feedback": "up"}
        )
        assert response.status_code == 200, f"Feedback failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert data["message"] == "Feedback submitted"

    def test_thread_messages_endpoint(self, auth_headers):
        """GET /api/v1/a0/thread/{thread_id} - get thread messages"""
        # Get threads first
        history_resp = requests.get(f"{BASE_URL}/api/v1/a0/history", headers=auth_headers)
        threads = history_resp.json().get("threads", [])
        
        if not threads:
            pytest.skip("No threads available")
        
        thread_id = threads[0]["thread_id"]
        response = requests.get(f"{BASE_URL}/api/v1/a0/thread/{thread_id}", headers=auth_headers)
        assert response.status_code == 200
        messages = response.json()
        assert isinstance(messages, list)
        
        # Verify message structure
        if messages:
            msg = messages[0]
            assert "message_id" in msg
            assert "role" in msg
            assert "content" in msg


class TestEdcmEndpoints:
    """V1 EDCM endpoints - /api/v1/edcm/eval"""

    def test_edcm_eval_endpoint(self, auth_headers):
        """POST /api/v1/edcm/eval - returns EDCM metrics"""
        # Get a thread first
        history_resp = requests.get(f"{BASE_URL}/api/v1/a0/history", headers=auth_headers)
        threads = history_resp.json().get("threads", [])
        
        if not threads:
            pytest.skip("No threads available for EDCM eval")
        
        thread_id = threads[0]["thread_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/v1/edcm/eval",
            headers=auth_headers,
            json={
                "thread_id": thread_id,
                "goal_text": "Test evaluation"
            }
        )
        assert response.status_code == 200, f"EDCM eval failed: {response.text}"
        data = response.json()
        
        # Verify EDCM report structure
        assert "snapshot_id" in data
        assert "metrics" in data
        assert "alerts" in data
        assert "provenance" in data


class TestRegistryEndpoints:
    """V1 Registry endpoints - /api/v1/registry"""

    def test_get_registry(self, auth_headers):
        """GET /api/v1/registry - returns user's model registry"""
        response = requests.get(f"{BASE_URL}/api/v1/registry", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "developers" in data
        
        # Verify registry structure
        developers = data["developers"]
        assert len(developers) >= 6
        
        for dev in developers:
            assert "developer_id" in dev
            assert "name" in dev
            assert "auth_type" in dev
            assert "models" in dev


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
