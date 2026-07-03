"""
Iteration 23: Testing archive/select-all/compare-popout features
- Instance archive action on each card
- Archived instance: undo archive + delete buttons
- Select all instances + bulk actions
- DELETE /api/v1/hub/instances/{instance_id} only deletes archived instances
- Response archive/undo archive buttons
- Select all responses + copy/share selected
- Compare popout for 2+ responses
"""

import os
import pytest
import requests
import time
import random

from tests.test_credentials import TEST_USER_ALT_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def test_user():
    """Register a fresh test user and return auth token"""
    username = f"archive_test_{random.randint(100000, 999999)}"
    password = TEST_USER_ALT_PASSWORD
    
    # Register
    response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": username,
        "password": password
    })
    assert response.status_code in [200, 201], f"Registration failed: {response.text}"
    
    # Login
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": username,
        "password": password
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    token = data.get("access_token") or data.get("token")
    assert token, "No token in login response"
    
    return {"username": username, "token": token}


@pytest.fixture(scope="module")
def auth_headers(test_user):
    """Return auth headers for API calls"""
    return {"Authorization": f"Bearer {test_user['token']}", "Content-Type": "application/json"}


class TestInstanceArchiveFeatures:
    """Test instance archive/unarchive/delete functionality"""
    
    def test_create_instance(self, auth_headers):
        """Create a test instance"""
        response = requests.post(f"{BASE_URL}/api/v1/hub/instances", headers=auth_headers, json={
            "name": "Archive Test Instance",
            "model_id": "gpt-4o"
        })
        assert response.status_code in [200, 201], f"Create instance failed: {response.text}"
        data = response.json()
        assert "instance_id" in data
        assert data["archived"] == False
        return data["instance_id"]
    
    def test_archive_instance(self, auth_headers):
        """Archive an instance"""
        # Create instance first
        create_resp = requests.post(f"{BASE_URL}/api/v1/hub/instances", headers=auth_headers, json={
            "name": "To Archive Instance",
            "model_id": "gpt-4o"
        })
        assert create_resp.status_code in [200, 201]
        instance_id = create_resp.json()["instance_id"]
        
        # Archive it
        archive_resp = requests.post(f"{BASE_URL}/api/v1/hub/instances/{instance_id}/archive", headers=auth_headers)
        assert archive_resp.status_code == 200, f"Archive failed: {archive_resp.text}"
        data = archive_resp.json()
        assert data["archived"] == True
        assert data["archived_at"] is not None
        return instance_id
    
    def test_unarchive_instance(self, auth_headers):
        """Unarchive an archived instance"""
        # Create and archive instance
        create_resp = requests.post(f"{BASE_URL}/api/v1/hub/instances", headers=auth_headers, json={
            "name": "To Unarchive Instance",
            "model_id": "gpt-4o"
        })
        instance_id = create_resp.json()["instance_id"]
        requests.post(f"{BASE_URL}/api/v1/hub/instances/{instance_id}/archive", headers=auth_headers)
        
        # Unarchive it
        unarchive_resp = requests.post(f"{BASE_URL}/api/v1/hub/instances/{instance_id}/unarchive", headers=auth_headers)
        assert unarchive_resp.status_code == 200, f"Unarchive failed: {unarchive_resp.text}"
        data = unarchive_resp.json()
        assert data["archived"] == False
        assert data["archived_at"] is None
    
    def test_delete_archived_instance_success(self, auth_headers):
        """DELETE should succeed for archived instances"""
        # Create and archive instance
        create_resp = requests.post(f"{BASE_URL}/api/v1/hub/instances", headers=auth_headers, json={
            "name": "To Delete Archived Instance",
            "model_id": "gpt-4o"
        })
        instance_id = create_resp.json()["instance_id"]
        requests.post(f"{BASE_URL}/api/v1/hub/instances/{instance_id}/archive", headers=auth_headers)
        
        # Delete it
        delete_resp = requests.delete(f"{BASE_URL}/api/v1/hub/instances/{instance_id}", headers=auth_headers)
        assert delete_resp.status_code == 200, f"Delete archived instance failed: {delete_resp.text}"
        
        # Verify it's gone
        get_resp = requests.get(f"{BASE_URL}/api/v1/hub/instances/{instance_id}", headers=auth_headers)
        assert get_resp.status_code == 404
    
    def test_delete_active_instance_rejected(self, auth_headers):
        """DELETE should be rejected for active (non-archived) instances"""
        # Create instance (not archived)
        create_resp = requests.post(f"{BASE_URL}/api/v1/hub/instances", headers=auth_headers, json={
            "name": "Active Instance Cannot Delete",
            "model_id": "gpt-4o"
        })
        instance_id = create_resp.json()["instance_id"]
        
        # Try to delete it (should fail)
        delete_resp = requests.delete(f"{BASE_URL}/api/v1/hub/instances/{instance_id}", headers=auth_headers)
        assert delete_resp.status_code == 400, f"Expected 400 for deleting active instance, got {delete_resp.status_code}"
        assert "archive" in delete_resp.text.lower(), "Error message should mention archiving"
    
    def test_list_instances_with_archived(self, auth_headers):
        """Test listing instances with include_archived flag"""
        # Create and archive an instance
        create_resp = requests.post(f"{BASE_URL}/api/v1/hub/instances", headers=auth_headers, json={
            "name": "Archived For List Test",
            "model_id": "gpt-4o"
        })
        instance_id = create_resp.json()["instance_id"]
        requests.post(f"{BASE_URL}/api/v1/hub/instances/{instance_id}/archive", headers=auth_headers)
        
        # List without archived
        list_resp = requests.get(f"{BASE_URL}/api/v1/hub/instances?include_archived=false", headers=auth_headers)
        assert list_resp.status_code == 200
        instances = list_resp.json()["instances"]
        archived_in_list = [i for i in instances if i["instance_id"] == instance_id]
        assert len(archived_in_list) == 0, "Archived instance should not appear without include_archived"
        
        # List with archived
        list_resp = requests.get(f"{BASE_URL}/api/v1/hub/instances?include_archived=true", headers=auth_headers)
        assert list_resp.status_code == 200
        instances = list_resp.json()["instances"]
        archived_in_list = [i for i in instances if i["instance_id"] == instance_id]
        assert len(archived_in_list) == 1, "Archived instance should appear with include_archived=true"


class TestBulkInstanceOperations:
    """Test bulk archive/restore/delete operations"""
    
    def test_bulk_archive_instances(self, auth_headers):
        """Create multiple instances and archive them in bulk"""
        instance_ids = []
        for i in range(3):
            resp = requests.post(f"{BASE_URL}/api/v1/hub/instances", headers=auth_headers, json={
                "name": f"Bulk Archive Test {i}",
                "model_id": "gpt-4o"
            })
            assert resp.status_code in [200, 201]
            instance_ids.append(resp.json()["instance_id"])
        
        # Archive each one
        for instance_id in instance_ids:
            archive_resp = requests.post(f"{BASE_URL}/api/v1/hub/instances/{instance_id}/archive", headers=auth_headers)
            assert archive_resp.status_code == 200
        
        # Verify all are archived
        for instance_id in instance_ids:
            get_resp = requests.get(f"{BASE_URL}/api/v1/hub/instances/{instance_id}", headers=auth_headers)
            assert get_resp.status_code == 200
            assert get_resp.json()["archived"] == True
    
    def test_bulk_restore_instances(self, auth_headers):
        """Create, archive, then restore multiple instances"""
        instance_ids = []
        for i in range(2):
            resp = requests.post(f"{BASE_URL}/api/v1/hub/instances", headers=auth_headers, json={
                "name": f"Bulk Restore Test {i}",
                "model_id": "gpt-4o"
            })
            instance_ids.append(resp.json()["instance_id"])
            requests.post(f"{BASE_URL}/api/v1/hub/instances/{instance_ids[-1]}/archive", headers=auth_headers)
        
        # Restore each one
        for instance_id in instance_ids:
            unarchive_resp = requests.post(f"{BASE_URL}/api/v1/hub/instances/{instance_id}/unarchive", headers=auth_headers)
            assert unarchive_resp.status_code == 200
        
        # Verify all are restored
        for instance_id in instance_ids:
            get_resp = requests.get(f"{BASE_URL}/api/v1/hub/instances/{instance_id}", headers=auth_headers)
            assert get_resp.status_code == 200
            assert get_resp.json()["archived"] == False
    
    def test_bulk_delete_archived_instances(self, auth_headers):
        """Create, archive, then delete multiple instances"""
        instance_ids = []
        for i in range(2):
            resp = requests.post(f"{BASE_URL}/api/v1/hub/instances", headers=auth_headers, json={
                "name": f"Bulk Delete Test {i}",
                "model_id": "gpt-4o"
            })
            instance_ids.append(resp.json()["instance_id"])
            requests.post(f"{BASE_URL}/api/v1/hub/instances/{instance_ids[-1]}/archive", headers=auth_headers)
        
        # Delete each one
        for instance_id in instance_ids:
            delete_resp = requests.delete(f"{BASE_URL}/api/v1/hub/instances/{instance_id}", headers=auth_headers)
            assert delete_resp.status_code == 200
        
        # Verify all are gone
        for instance_id in instance_ids:
            get_resp = requests.get(f"{BASE_URL}/api/v1/hub/instances/{instance_id}", headers=auth_headers)
            assert get_resp.status_code == 404


class TestChatPromptResponses:
    """Test chat prompt and response functionality for archive/select features"""
    
    def test_send_chat_prompt_and_get_responses(self, auth_headers):
        """Send a chat prompt to multiple instances and verify responses"""
        # Create 2 instances
        instance_ids = []
        for i in range(2):
            resp = requests.post(f"{BASE_URL}/api/v1/hub/instances", headers=auth_headers, json={
                "name": f"Chat Test Instance {i}",
                "model_id": "gpt-4o-mini"
            })
            assert resp.status_code in [200, 201]
            instance_ids.append(resp.json()["instance_id"])
        
        # Send chat prompt
        prompt_resp = requests.post(f"{BASE_URL}/api/v1/hub/chat/prompts", headers=auth_headers, json={
            "prompt": "Say hello in one word.",
            "instance_ids": instance_ids
        }, timeout=60)
        assert prompt_resp.status_code in [200, 201], f"Chat prompt failed: {prompt_resp.text}"
        data = prompt_resp.json()
        assert "prompt_id" in data
        assert "responses" in data
        assert len(data["responses"]) >= 1  # At least one response
        return data
    
    def test_list_chat_prompts(self, auth_headers):
        """List chat prompts"""
        resp = requests.get(f"{BASE_URL}/api/v1/hub/chat/prompts", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "prompts" in data
        assert isinstance(data["prompts"], list)


class TestHubOptions:
    """Test hub options endpoint for feature flags"""
    
    def test_hub_options_includes_archive_support(self, auth_headers):
        """Verify hub options includes archive-related support flags"""
        resp = requests.get(f"{BASE_URL}/api/v1/hub/options", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        
        # Check supports flags
        supports = data.get("supports", {})
        assert supports.get("instance_archival") == True, "instance_archival should be True"
        assert supports.get("run_archival") == True, "run_archival should be True"
        
        # Check fastapi_connections includes delete endpoint
        connections = data.get("fastapi_connections", {})
        instances_endpoints = connections.get("instances", {})
        assert "delete" in instances_endpoints, "delete endpoint should be in instances connections"
        assert "archive" in instances_endpoints, "archive endpoint should be in instances connections"
        assert "unarchive" in instances_endpoints, "unarchive endpoint should be in instances connections"


class TestAuthProtection:
    """Test that all endpoints require authentication"""
    
    def test_instance_endpoints_require_auth(self):
        """All instance endpoints should require authentication"""
        endpoints = [
            ("GET", "/api/v1/hub/instances"),
            ("POST", "/api/v1/hub/instances"),
            ("GET", "/api/v1/hub/instances/fake-id"),
            ("DELETE", "/api/v1/hub/instances/fake-id"),
            ("POST", "/api/v1/hub/instances/fake-id/archive"),
            ("POST", "/api/v1/hub/instances/fake-id/unarchive"),
        ]
        
        for method, path in endpoints:
            if method == "GET":
                resp = requests.get(f"{BASE_URL}{path}")
            elif method == "POST":
                resp = requests.post(f"{BASE_URL}{path}", json={})
            elif method == "DELETE":
                resp = requests.delete(f"{BASE_URL}{path}")
            
            assert resp.status_code == 401, f"{method} {path} should require auth, got {resp.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
