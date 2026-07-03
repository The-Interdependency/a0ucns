"""
Iteration 21 Tests: Transcript Analysis API, Layout Toggle, Chat Persistence
Focus: Testing NEW features added in this iteration:
- POST /api/v1/analysis/transcript - Submit transcript for EDCM analysis
- GET /api/v1/analysis/reports - List user's analysis reports
- GET /api/v1/analysis/reports/{id} - Get specific report
"""

import pytest
import requests
import os
import time

from tests.test_credentials import TEST_USER_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable is required")

# Test credentials
TEST_USERNAME = "testbot01"
TEST_PASSWORD = TEST_USER_PASSWORD

# Sample transcript for testing
SAMPLE_TRANSCRIPT = """Speaker A: I agree the contract is fair.
Speaker B: Actually, I think several clauses are problematic.
Speaker A: Which clauses specifically?
Speaker B: The liability section contradicts the warranty terms."""


class TestAuth:
    """Authentication tests to get auth token for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in login response"
        return data["access_token"]
    
    def test_login_success(self):
        """Test login returns access token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        print(f"✓ Login successful, got access_token")


class TestAnalysisEndpoints:
    """Tests for the new transcript analysis endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for API requests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_analysis_transcript_endpoint(self, auth_headers):
        """Test POST /api/v1/analysis/transcript - submit transcript for analysis"""
        payload = {
            "transcript_text": SAMPLE_TRANSCRIPT,
            "model": "gpt-4o-mini",
            "goal_text": "Contract negotiation",
            "declared_constraints": ["accuracy", "honesty"]
        }
        
        # This endpoint makes 2 LLM calls, so use longer timeout
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/transcript",
            json=payload,
            headers=auth_headers,
            timeout=90
        )
        
        assert response.status_code == 200, f"Analysis failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "analysis_id" in data, "Missing analysis_id"
        assert "turns" in data, "Missing turns"
        assert "summary_metrics" in data, "Missing summary_metrics"
        assert "narrative_summary" in data, "Missing narrative_summary"
        assert "flagged_turns" in data, "Missing flagged_turns"
        assert "turn_count" in data, "Missing turn_count"
        
        # Verify turns have EDCM metrics
        if len(data["turns"]) > 0:
            turn = data["turns"][0]
            assert "speaker" in turn, "Turn missing speaker"
            assert "content" in turn, "Turn missing content"
            assert "metrics" in turn, "Turn missing metrics"
            # Check for EDCM metrics
            metrics = turn["metrics"]
            for metric_name in ["CM", "DA", "DRIFT", "DVG", "INT", "TBF"]:
                assert metric_name in metrics, f"Missing metric {metric_name}"
        
        print(f"✓ Analysis endpoint works: {data['turn_count']} turns analyzed")
        print(f"  Analysis ID: {data['analysis_id']}")
        print(f"  Flagged turns: {len(data.get('flagged_turns', []))}")
        
        return data["analysis_id"]
    
    def test_analysis_reports_list(self, auth_headers):
        """Test GET /api/v1/analysis/reports - list user's reports"""
        response = requests.get(
            f"{BASE_URL}/api/v1/analysis/reports",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"List reports failed: {response.text}"
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list), "Reports should be a list"
        
        if len(data) > 0:
            report = data[0]
            assert "analysis_id" in report, "Report missing analysis_id"
            assert "title" in report, "Report missing title"
            assert "model_used" in report, "Report missing model_used"
            assert "turn_count" in report, "Report missing turn_count"
            print(f"✓ Reports list works: {len(data)} reports found")
            return report["analysis_id"]
        else:
            print("✓ Reports list works: No reports yet (empty list)")
            return None
    
    def test_analysis_report_by_id(self, auth_headers):
        """Test GET /api/v1/analysis/reports/{id} - get specific report"""
        # First create a report
        payload = {
            "transcript_text": SAMPLE_TRANSCRIPT,
            "model": "gpt-4o-mini",
            "goal_text": "Test goal",
            "declared_constraints": []
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/v1/analysis/transcript",
            json=payload,
            headers=auth_headers,
            timeout=90
        )
        
        if create_response.status_code != 200:
            pytest.skip(f"Could not create report: {create_response.text}")
        
        analysis_id = create_response.json()["analysis_id"]
        
        # Now fetch it by ID
        response = requests.get(
            f"{BASE_URL}/api/v1/analysis/reports/{analysis_id}",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Get report failed: {response.text}"
        data = response.json()
        
        assert data["analysis_id"] == analysis_id, "Analysis ID mismatch"
        assert "turns" in data, "Full report missing turns"
        assert "narrative_summary" in data, "Full report missing narrative_summary"
        
        print(f"✓ Get report by ID works: {analysis_id}")
    
    def test_analysis_report_not_found(self, auth_headers):
        """Test GET /api/v1/analysis/reports/{id} with invalid ID returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/v1/analysis/reports/invalid_id_12345",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Report not found returns 404 correctly")
    
    def test_analysis_requires_auth(self):
        """Test that analysis endpoints require authentication"""
        # No auth header
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis/transcript",
            json={"transcript_text": "test"},
            timeout=30
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Analysis endpoint requires auth")


class TestChatPersistence:
    """Tests for chat thread persistence"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for API requests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_prompt_creates_thread(self, auth_headers):
        """Test that sending a prompt creates a persistent thread"""
        payload = {
            "message": "Hello, this is a test message for persistence testing.",
            "model": "gpt-4o-mini"  # prompt-single uses singular 'model' not 'models'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/a0/prompt-single",
            json=payload,
            headers=auth_headers,
            timeout=60
        )
        
        assert response.status_code == 200, f"Prompt failed: {response.text}"
        data = response.json()
        
        assert "thread_id" in data, "Response missing thread_id"
        thread_id = data["thread_id"]
        
        # Now fetch history to verify thread exists
        history_response = requests.get(
            f"{BASE_URL}/api/v1/a0/history?limit=50",
            headers=auth_headers,
            timeout=30
        )
        
        assert history_response.status_code == 200
        threads = history_response.json().get("threads", [])
        
        thread_ids = [t["thread_id"] for t in threads]
        assert thread_id in thread_ids, f"Thread {thread_id} not found in history"
        
        print(f"✓ Thread created and persisted: {thread_id}")
        return thread_id
    
    def test_thread_messages_persist(self, auth_headers):
        """Test that messages in a thread persist and can be retrieved"""
        # Create a new thread with a prompt
        payload = {
            "message": "Testing persistence - can you see this?",
            "model": "gpt-4o-mini"  # prompt-single uses singular 'model'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/a0/prompt-single",
            json=payload,
            headers=auth_headers,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        thread_id = data["thread_id"]
        
        # Fetch thread messages
        thread_response = requests.get(
            f"{BASE_URL}/api/v1/a0/thread/{thread_id}",
            headers=auth_headers,
            timeout=30
        )
        
        assert thread_response.status_code == 200, f"Thread fetch failed: {thread_response.text}"
        messages = thread_response.json()
        
        assert len(messages) >= 2, f"Expected at least 2 messages, got {len(messages)}"
        
        # Verify we have user and assistant messages
        roles = [m["role"] for m in messages]
        assert "user" in roles, "Missing user message"
        assert "assistant" in roles, "Missing assistant message"
        
        print(f"✓ Thread messages persist: {len(messages)} messages in thread {thread_id}")


class TestExistingFeatures:
    """Verify existing features still work (regression tests)"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for API requests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_health_endpoint(self):
        """Test /api/v1/health works"""
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("✓ Health endpoint works")
    
    def test_models_endpoint(self, auth_headers):
        """Test /api/v1/models returns model registry"""
        response = requests.get(
            f"{BASE_URL}/api/v1/models",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "developers" in data
        assert len(data["developers"]) > 0
        print(f"✓ Models endpoint works: {len(data['developers'])} developers")
    
    def test_keys_status(self, auth_headers):
        """Test /api/v1/keys returns key status"""
        response = requests.get(
            f"{BASE_URL}/api/v1/keys",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        # API returns a list of developer key statuses directly
        assert isinstance(data, list), "Keys endpoint should return list"
        assert len(data) > 0, "Should have key status for developers"
        # Verify structure
        first_key = data[0]
        assert "developer_id" in first_key
        assert "status" in first_key
        print(f"✓ Keys status endpoint works: {len(data)} developers")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
