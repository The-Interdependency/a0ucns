"""
Backend API Tests - Iteration 4 Features
Tests: Per-model prompt customization, attachments, Agent Zero non-UI endpoints
"""
import pytest
import requests
import os
import uuid

from tests.test_credentials import TEST_USER_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
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


# ============== Agent Zero Non-UI API Tests ==============

class TestAgentZeroNonUIEndpoints:
    """Agent Zero non-UI access endpoints - allows A0 programmatic access"""
    
    def test_get_non_ui_options(self, authenticated_client):
        """Test GET /api/a0/non-ui/options returns all input/output options"""
        response = authenticated_client.get(f"{BASE_URL}/api/a0/non-ui/options")
        
        assert response.status_code == 200, f"Failed to get non-UI options: {response.text}"
        data = response.json()
        
        # Verify expected fields
        assert "input_options" in data, "Missing input_options"
        assert "output_options" in data, "Missing output_options"
        assert "available_models" in data, "Missing available_models"
        assert "non_ui_endpoints" in data, "Missing non_ui_endpoints"
        
        # Verify input options structure
        input_opts = data["input_options"]
        assert "context_mode" in input_opts
        assert "supports_global_context" in input_opts
        assert "supports_model_roles" in input_opts
        assert "supports_per_model_messages" in input_opts
        assert "supports_attachments" in input_opts
        assert "attachment_target_modes" in input_opts
        assert input_opts["attachment_target_modes"] == ["all", "selected"]
        
        # Verify output options
        output_opts = data["output_options"]
        assert output_opts["streaming"] == "SSE"
        assert "export_formats" in output_opts
        
        # Verify non-UI endpoints reference
        endpoints = data["non_ui_endpoints"]
        assert "chat_stream" in endpoints
        assert "options" in endpoints
        assert "transcript" in endpoints
        assert "conversations" in endpoints
        
        print(f"✓ GET /api/a0/non-ui/options returned complete schema")
        print(f"  Input options: {list(input_opts.keys())}")
        print(f"  Available models: {list(data['available_models'].keys())}")
    
    def test_get_non_ui_options_requires_auth(self, api_client):
        """Test that non-UI options endpoint requires authentication"""
        # Remove auth header for this test
        unauthenticated_session = requests.Session()
        unauthenticated_session.headers.update({"Content-Type": "application/json"})
        
        response = unauthenticated_session.get(f"{BASE_URL}/api/a0/non-ui/options")
        
        # Should fail without auth
        assert response.status_code in [401, 403], f"Expected auth error, got: {response.status_code}"
        print("✓ Non-UI options endpoint requires authentication")
    
    def test_get_non_ui_conversations(self, authenticated_client):
        """Test GET /api/a0/non-ui/conversations lists user conversations"""
        response = authenticated_client.get(f"{BASE_URL}/api/a0/non-ui/conversations")
        
        assert response.status_code == 200, f"Failed to get conversations: {response.text}"
        data = response.json()
        
        assert "conversations" in data, "Missing conversations field"
        assert isinstance(data["conversations"], list), "conversations should be a list"
        
        print(f"✓ GET /api/a0/non-ui/conversations returned {len(data['conversations'])} conversations")
    
    def test_get_non_ui_transcript_not_found(self, authenticated_client):
        """Test GET /api/a0/non-ui/transcript/{id} returns 404 for invalid conversation"""
        fake_conv_id = f"fake_conv_{uuid.uuid4()}"
        response = authenticated_client.get(f"{BASE_URL}/api/a0/non-ui/transcript/{fake_conv_id}")
        
        assert response.status_code == 404, f"Expected 404, got: {response.status_code}"
        print("✓ Non-UI transcript endpoint returns 404 for invalid ID")


# ============== Chat Request with Attachments Tests ==============

class TestChatAttachments:
    """Test attachment handling in chat endpoint"""
    
    def test_chat_stream_accepts_attachments_payload(self, authenticated_client):
        """Test /api/chat/stream accepts attachments field in request"""
        conversation_id = f"test_attach_{uuid.uuid4()}"
        
        payload = {
            "message": "Test message with attachment reference",
            "models": ["gpt-4o"],
            "conversation_id": conversation_id,
            "context_mode": "compartmented",
            "attachments": [
                {
                    "id": f"att_{uuid.uuid4()}",
                    "name": "test_document.txt",
                    "mime_type": "text/plain",
                    "kind": "text",
                    "size": 1024,
                    "content": "This is test content from a text file attachment.",
                    "target_mode": "all",
                    "target_models": []
                }
            ]
        }
        
        # We expect stream to start even if API key is missing (will return error in stream)
        response = authenticated_client.post(
            f"{BASE_URL}/api/chat/stream",
            json=payload,
            stream=True
        )
        
        # The endpoint should accept the request format
        assert response.status_code == 200, f"Chat stream with attachments failed: {response.status_code}"
        print(f"✓ POST /api/chat/stream accepts attachments payload")
    
    def test_chat_stream_with_selected_target_mode(self, authenticated_client):
        """Test attachments with selected target mode validation"""
        conversation_id = f"test_attach_selected_{uuid.uuid4()}"
        
        payload = {
            "message": "Test with targeted attachment",
            "models": ["gpt-4o", "claude-sonnet-4-5-20250929"],
            "conversation_id": conversation_id,
            "context_mode": "compartmented",
            "attachments": [
                {
                    "id": f"att_{uuid.uuid4()}",
                    "name": "targeted_doc.txt",
                    "mime_type": "text/plain",
                    "kind": "text",
                    "size": 512,
                    "content": "This attachment targets only gpt-4o.",
                    "target_mode": "selected",
                    "target_models": ["gpt-4o"]
                }
            ]
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/chat/stream",
            json=payload,
            stream=True
        )
        
        assert response.status_code == 200, f"Chat stream with targeted attachment failed: {response.status_code}"
        print("✓ POST /api/chat/stream accepts targeted (selected) attachments")
    
    def test_chat_stream_with_image_attachment(self, authenticated_client):
        """Test attachments with image type"""
        conversation_id = f"test_attach_image_{uuid.uuid4()}"
        
        # Simulated base64 image (just metadata test, not real image)
        payload = {
            "message": "What is in this image?",
            "models": ["gpt-4o"],
            "conversation_id": conversation_id,
            "attachments": [
                {
                    "id": f"img_{uuid.uuid4()}",
                    "name": "screenshot.png",
                    "mime_type": "image/png",
                    "kind": "image",
                    "size": 50000,
                    "content": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...",
                    "target_mode": "all",
                    "target_models": []
                }
            ]
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/chat/stream",
            json=payload,
            stream=True
        )
        
        assert response.status_code == 200, f"Chat stream with image attachment failed: {response.status_code}"
        print("✓ POST /api/chat/stream accepts image attachments")


# ============== Per-Model Messages / Prompt Properties Tests ==============

class TestPerModelMessages:
    """Test per-model prompt customization via per_model_messages"""
    
    def test_chat_stream_accepts_per_model_messages(self, authenticated_client):
        """Test /api/chat/stream accepts per_model_messages field"""
        conversation_id = f"test_permodel_{uuid.uuid4()}"
        
        payload = {
            "message": "Base prompt",
            "models": ["gpt-4o", "claude-sonnet-4-5-20250929"],
            "conversation_id": conversation_id,
            "per_model_messages": {
                "gpt-4o": "[ROLE]: Technical expert\n[VERBOSITY]: 3/10\nBase prompt",
                "claude-sonnet-4-5-20250929": "[ROLE]: Creative writer\n[VERBOSITY]: 7/10\nBase prompt"
            }
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/chat/stream",
            json=payload,
            stream=True
        )
        
        assert response.status_code == 200, f"Chat stream with per_model_messages failed: {response.status_code}"
        print("✓ POST /api/chat/stream accepts per_model_messages for prompt customization")
    
    def test_chat_stream_with_global_context(self, authenticated_client):
        """Test /api/chat/stream with global_context field"""
        conversation_id = f"test_context_{uuid.uuid4()}"
        
        payload = {
            "message": "What is the answer?",
            "models": ["gpt-4o"],
            "conversation_id": conversation_id,
            "global_context": "You are assisting with a coding interview. Be concise and technical.",
            "context_mode": "compartmented"
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/chat/stream",
            json=payload,
            stream=True
        )
        
        assert response.status_code == 200, f"Chat stream with global_context failed: {response.status_code}"
        print("✓ POST /api/chat/stream accepts global_context field")


# ============== A0 Settings Endpoint List Verification ==============

class TestA0SettingsEndpoints:
    """Verify A0 settings includes non-UI endpoints"""
    
    def test_non_ui_endpoints_in_options_response(self, authenticated_client):
        """Verify that non-UI endpoints are listed in /api/a0/non-ui/options response"""
        response = authenticated_client.get(f"{BASE_URL}/api/a0/non-ui/options")
        
        assert response.status_code == 200
        data = response.json()
        
        endpoints = data.get("non_ui_endpoints", {})
        
        # Expected endpoints
        assert "chat_stream" in endpoints, "Missing chat_stream endpoint"
        assert "options" in endpoints, "Missing options endpoint"
        assert "transcript" in endpoints, "Missing transcript endpoint"
        assert "conversations" in endpoints, "Missing conversations endpoint"
        
        # Verify paths are correct
        assert "/api/a0/non-ui/chat/stream" in endpoints["chat_stream"]
        assert "/api/a0/non-ui/options" in endpoints["options"]
        assert "/api/a0/non-ui/transcript" in endpoints["transcript"]
        assert "/api/a0/non-ui/conversations" in endpoints["conversations"]
        
        print("✓ Non-UI endpoints correctly listed in options response")
        print(f"  Endpoints: {endpoints}")


# ============== Basic Health / Connectivity ==============

class TestBasicConnectivity:
    """Basic API connectivity tests"""
    
    def test_auth_endpoint_available(self, api_client):
        """Test auth endpoint responds (not 404)"""
        # Use a fresh session without auth
        fresh_session = requests.Session()
        fresh_session.headers.update({"Content-Type": "application/json"})
        response = fresh_session.get(f"{BASE_URL}/api/auth/me")
        # Should not return 404 - endpoint exists (401/403/200 are all valid)
        assert response.status_code != 404, f"Auth endpoint not found: {response.status_code}"
        print(f"✓ Auth endpoint is available (status: {response.status_code})")
    
    def test_a0_config_endpoint_available(self, authenticated_client):
        """Test A0 config endpoint responds"""
        response = authenticated_client.get(f"{BASE_URL}/api/a0/config")
        assert response.status_code == 200, f"A0 config endpoint failed: {response.status_code}"
        print("✓ A0 config endpoint is available")
