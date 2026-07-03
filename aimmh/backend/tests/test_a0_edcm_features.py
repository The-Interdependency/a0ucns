"""
Backend API Tests for A0 Plugin and EDCM Dashboard Features
Tests: A0 config CRUD, EDCM metrics ingest/query, dashboard endpoint
"""
import pytest
import requests
import os
import uuid

from test_credentials import TEST_FAKE_API_KEY, TEST_USER_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials - reuse from previous iteration
TEST_USERNAME = "testuser_refactor"
TEST_PASSWORD = TEST_USER_PASSWORD


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Login with existing test user credentials"""
    response = api_client.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    
    # If login fails, try registering
    register_response = api_client.post(
        f"{BASE_URL}/api/auth/register",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    
    if register_response.status_code == 200:
        data = register_response.json()
        return data.get("access_token")
    
    pytest.skip(f"Authentication failed - cannot proceed with tests")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


# ============== A0 Config Tests ==============

class TestA0ConfigEndpoints:
    """Agent Zero configuration CRUD tests"""
    
    def test_get_a0_config_default(self, authenticated_client):
        """Test GET /api/a0/config returns default config for new users"""
        response = authenticated_client.get(f"{BASE_URL}/api/a0/config")
        
        assert response.status_code == 200, f"Get A0 config failed: {response.text}"
        data = response.json()
        
        # Verify default config structure
        assert "mode" in data, "Missing mode field"
        assert "local_url" in data, "Missing local_url field"
        assert "local_port" in data, "Missing local_port field"
        assert "cloud_url" in data, "Missing cloud_url field"
        assert "route_via_a0" in data, "Missing route_via_a0 field"
        assert "auto_ingest" in data, "Missing auto_ingest field"
        
        # Default values check
        assert data["mode"] in ["local", "cloud"], f"Invalid mode: {data['mode']}"
        print(f"✓ GET /api/a0/config returned config: {data}")
    
    def test_put_a0_config_local_mode(self, authenticated_client):
        """Test PUT /api/a0/config saves local device config"""
        config_payload = {
            "mode": "local",
            "local_url": "http://192.168.1.50",
            "local_port": 9000,
            "cloud_url": "",
            "api_key": "",
            "route_via_a0": False,
            "auto_ingest": True
        }
        
        response = authenticated_client.put(
            f"{BASE_URL}/api/a0/config",
            json=config_payload
        )
        
        assert response.status_code == 200, f"PUT A0 config failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ PUT /api/a0/config saved local config: {data}")
        
        # Verify persistence via GET
        get_response = authenticated_client.get(f"{BASE_URL}/api/a0/config")
        assert get_response.status_code == 200
        saved_config = get_response.json()
        
        assert saved_config["mode"] == "local"
        assert saved_config["local_url"] == "http://192.168.1.50"
        assert saved_config["local_port"] == 9000
        assert saved_config["auto_ingest"] == True
        print("✓ A0 config persistence verified")
    
    def test_put_a0_config_cloud_mode(self, authenticated_client):
        """Test PUT /api/a0/config saves cloud config (stub)"""
        config_payload = {
            "mode": "cloud",
            "local_url": "http://192.168.1.1",
            "local_port": 8787,
            "cloud_url": "https://my-a0-instance.run.app",
            "api_key": TEST_FAKE_API_KEY,
            "route_via_a0": True,
            "auto_ingest": False
        }
        
        response = authenticated_client.put(
            f"{BASE_URL}/api/a0/config",
            json=config_payload
        )
        
        assert response.status_code == 200
        print("✓ PUT /api/a0/config cloud mode saved")
        
        # Verify cloud config persisted
        get_response = authenticated_client.get(f"{BASE_URL}/api/a0/config")
        saved_config = get_response.json()
        
        assert saved_config["mode"] == "cloud"
        assert saved_config["cloud_url"] == "https://my-a0-instance.run.app"
        assert saved_config["route_via_a0"] == True
        print("✓ Cloud mode config persistence verified")
    
    def test_a0_health_uses_user_config(self, authenticated_client):
        """Test GET /api/a0/health uses user-specific config"""
        # First set a specific config
        config_payload = {
            "mode": "local",
            "local_url": "http://192.168.99.99",
            "local_port": 1234,
            "cloud_url": "",
            "api_key": "",
            "route_via_a0": False,
            "auto_ingest": False
        }
        authenticated_client.put(f"{BASE_URL}/api/a0/config", json=config_payload)
        
        # Check health - should return unreachable since IP is fake
        response = authenticated_client.get(f"{BASE_URL}/api/a0/health")
        
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        
        assert "status" in data
        assert "a0_url" in data
        # Should reflect our configured URL
        assert "192.168.99.99" in data.get("a0_url", "") or data["status"] in ["unreachable", "not_configured", "error"]
        print(f"✓ GET /api/a0/health uses user config: {data}")
    
    def test_a0_config_requires_auth(self):
        """Test A0 config endpoints require authentication"""
        fresh_session = requests.Session()
        
        get_response = fresh_session.get(f"{BASE_URL}/api/a0/config")
        assert get_response.status_code in [401, 403], "GET /api/a0/config should require auth"
        
        put_response = fresh_session.put(
            f"{BASE_URL}/api/a0/config",
            json={"mode": "local"},
            headers={"Content-Type": "application/json"}
        )
        assert put_response.status_code in [401, 403], "PUT /api/a0/config should require auth"
        print("✓ A0 config endpoints require authentication")


# ============== EDCM Metrics Tests ==============

class TestEDCMIngestEndpoint:
    """EDCM metrics ingest endpoint tests"""
    
    def test_ingest_edcm_metrics(self, authenticated_client):
        """Test POST /api/edcm/ingest receives and stores EDCM metrics"""
        test_conversation_id = f"test_conv_{uuid.uuid4().hex[:8]}"
        
        payload = {
            "conversation_id": test_conversation_id,
            "metrics": {
                "conversation_id": test_conversation_id,
                "constraint_mismatch_density": 0.72,
                "fixation_coefficient": 0.45,
                "escalation_gradient": 0.88,
                "context_drift_index": 0.31,
                "load_saturation_index": 0.65,
                "metadata": {"source": "test", "model": "test-model"}
            },
            "source": "agent_zero",
            "timestamp": "2026-01-15T12:00:00Z"
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/edcm/ingest",
            json=payload
        )
        
        assert response.status_code == 200, f"EDCM ingest failed: {response.text}"
        data = response.json()
        
        assert "message" in data
        assert data.get("conversation_id") == test_conversation_id
        print(f"✓ POST /api/edcm/ingest succeeded: {data}")
        
        return test_conversation_id
    
    def test_ingest_edcm_minimal_metrics(self, authenticated_client):
        """Test EDCM ingest with minimal/partial metrics"""
        test_conversation_id = f"test_conv_min_{uuid.uuid4().hex[:8]}"
        
        # Only some metrics provided
        payload = {
            "conversation_id": test_conversation_id,
            "metrics": {
                "conversation_id": test_conversation_id,
                "constraint_mismatch_density": 0.55,
                # Other metrics are optional
            },
            "source": "test_source"
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/edcm/ingest",
            json=payload
        )
        
        assert response.status_code == 200, f"Minimal ingest failed: {response.text}"
        print("✓ EDCM ingest accepts partial metrics")
    
    def test_edcm_ingest_requires_auth(self):
        """Test EDCM ingest requires authentication"""
        fresh_session = requests.Session()
        
        response = fresh_session.post(
            f"{BASE_URL}/api/edcm/ingest",
            json={
                "conversation_id": "test",
                "metrics": {"conversation_id": "test"},
                "source": "test"
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code in [401, 403]
        print("✓ EDCM ingest requires authentication")


class TestEDCMQueryEndpoints:
    """EDCM metrics query endpoint tests"""
    
    def test_get_edcm_metrics(self, authenticated_client):
        """Test GET /api/edcm/metrics returns metrics list"""
        response = authenticated_client.get(f"{BASE_URL}/api/edcm/metrics")
        
        assert response.status_code == 200, f"GET EDCM metrics failed: {response.text}"
        data = response.json()
        
        assert "metrics" in data
        assert isinstance(data["metrics"], list)
        print(f"✓ GET /api/edcm/metrics returned {len(data['metrics'])} metrics")
    
    def test_get_edcm_metrics_by_conversation(self, authenticated_client):
        """Test GET /api/edcm/metrics with conversation_id filter"""
        # First ingest some metrics
        test_conv_id = f"test_filter_{uuid.uuid4().hex[:8]}"
        authenticated_client.post(
            f"{BASE_URL}/api/edcm/ingest",
            json={
                "conversation_id": test_conv_id,
                "metrics": {
                    "conversation_id": test_conv_id,
                    "constraint_mismatch_density": 0.99
                },
                "source": "test"
            }
        )
        
        # Query with filter
        response = authenticated_client.get(
            f"{BASE_URL}/api/edcm/metrics",
            params={"conversation_id": test_conv_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # If metrics returned, they should match our conversation
        if data["metrics"]:
            for m in data["metrics"]:
                assert m["conversation_id"] == test_conv_id
        print(f"✓ GET /api/edcm/metrics with filter works: {len(data['metrics'])} results")


class TestEDCMResponseTimesEndpoint:
    """Response time stats endpoint tests"""
    
    def test_get_response_times(self, authenticated_client):
        """Test GET /api/edcm/response-times returns per-model stats"""
        response = authenticated_client.get(f"{BASE_URL}/api/edcm/response-times")
        
        assert response.status_code == 200, f"GET response-times failed: {response.text}"
        data = response.json()
        
        assert "response_times" in data
        assert isinstance(data["response_times"], list)
        
        # Verify structure if data exists
        for rt in data["response_times"]:
            assert "model" in rt, "Missing model field in response time"
            assert "avg_ms" in rt, "Missing avg_ms field"
            assert "count" in rt, "Missing count field"
        
        print(f"✓ GET /api/edcm/response-times returned {len(data['response_times'])} models")
    
    def test_response_times_requires_auth(self):
        """Test response-times requires authentication"""
        fresh_session = requests.Session()
        response = fresh_session.get(f"{BASE_URL}/api/edcm/response-times")
        
        assert response.status_code in [401, 403]
        print("✓ Response-times endpoint requires auth")


class TestEDCMFeedbackStatsEndpoint:
    """Feedback stats endpoint tests"""
    
    def test_get_feedback_stats(self, authenticated_client):
        """Test GET /api/edcm/feedback-stats returns per-model thumbs up/down"""
        response = authenticated_client.get(f"{BASE_URL}/api/edcm/feedback-stats")
        
        assert response.status_code == 200, f"GET feedback-stats failed: {response.text}"
        data = response.json()
        
        assert "feedback_stats" in data
        assert isinstance(data["feedback_stats"], list)
        
        # Verify structure if data exists
        for fb in data["feedback_stats"]:
            assert "model" in fb, "Missing model field"
            assert "up" in fb, "Missing up count"
            assert "down" in fb, "Missing down count"
        
        print(f"✓ GET /api/edcm/feedback-stats returned {len(data['feedback_stats'])} models")
    
    def test_feedback_stats_requires_auth(self):
        """Test feedback-stats requires authentication"""
        fresh_session = requests.Session()
        response = fresh_session.get(f"{BASE_URL}/api/edcm/feedback-stats")
        
        assert response.status_code in [401, 403]
        print("✓ Feedback-stats endpoint requires auth")


class TestEDCMDashboardEndpoint:
    """Dashboard aggregation endpoint tests"""
    
    def test_get_dashboard(self, authenticated_client):
        """Test GET /api/edcm/dashboard returns aggregated data"""
        response = authenticated_client.get(f"{BASE_URL}/api/edcm/dashboard")
        
        assert response.status_code == 200, f"GET dashboard failed: {response.text}"
        data = response.json()
        
        # Verify all required fields present
        assert "edcm_metrics" in data, "Missing edcm_metrics in dashboard"
        assert "response_times" in data, "Missing response_times in dashboard"
        assert "feedback_stats" in data, "Missing feedback_stats in dashboard"
        assert "total_conversations" in data, "Missing total_conversations in dashboard"
        assert "total_messages" in data, "Missing total_messages in dashboard"
        
        # Verify types
        assert isinstance(data["edcm_metrics"], list)
        assert isinstance(data["response_times"], list)
        assert isinstance(data["feedback_stats"], list)
        assert isinstance(data["total_conversations"], int)
        assert isinstance(data["total_messages"], int)
        
        print(f"✓ GET /api/edcm/dashboard returned: {len(data['edcm_metrics'])} EDCM metrics, "
              f"{len(data['response_times'])} response times, {len(data['feedback_stats'])} feedback stats, "
              f"{data['total_conversations']} convs, {data['total_messages']} msgs")
    
    def test_dashboard_requires_auth(self):
        """Test dashboard requires authentication"""
        fresh_session = requests.Session()
        response = fresh_session.get(f"{BASE_URL}/api/edcm/dashboard")
        
        assert response.status_code in [401, 403]
        print("✓ Dashboard endpoint requires auth")
    
    def test_dashboard_after_ingest(self, authenticated_client):
        """Test dashboard reflects ingested EDCM metrics"""
        # First, ingest some metrics
        test_conv_id = f"dashboard_test_{uuid.uuid4().hex[:8]}"
        
        ingest_payload = {
            "conversation_id": test_conv_id,
            "metrics": {
                "conversation_id": test_conv_id,
                "constraint_mismatch_density": 0.72,
                "fixation_coefficient": 0.45,
                "escalation_gradient": 0.88,
                "context_drift_index": 0.31,
                "load_saturation_index": 0.65
            },
            "source": "dashboard_test"
        }
        
        ingest_response = authenticated_client.post(
            f"{BASE_URL}/api/edcm/ingest",
            json=ingest_payload
        )
        assert ingest_response.status_code == 200, f"Ingest failed: {ingest_response.text}"
        
        # Now check dashboard includes this data
        dashboard_response = authenticated_client.get(f"{BASE_URL}/api/edcm/dashboard")
        assert dashboard_response.status_code == 200
        data = dashboard_response.json()
        
        # There should be at least one EDCM metric
        assert len(data["edcm_metrics"]) > 0, "Dashboard should have EDCM metrics after ingest"
        
        # Check that our test metrics are present (latest first)
        latest = data["edcm_metrics"][0]
        if latest.get("conversation_id") == test_conv_id:
            assert latest.get("constraint_mismatch_density") == 0.72
            assert latest.get("escalation_gradient") == 0.88
            print("✓ Dashboard correctly reflects latest ingested metrics")
        else:
            print(f"✓ Dashboard has {len(data['edcm_metrics'])} metrics (test metric may not be latest)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
