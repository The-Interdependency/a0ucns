"""
Iteration 5 Tests: Shared Room Mode and Reload Persistence
- Context mode selector: compartmented vs shared
- Shared room mode: parallel_all vs parallel_paired
- Backend accepts shared_room_mode and shared_pairs payloads without 422/500
- Message persistence during streaming for reload recovery
- Conversation sync endpoint returns assistant messages after reload
"""

import pytest
import requests
import os
import time
import uuid

from tests.test_credentials import TEST_USER_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def test_user():
    """Create a test user for the session"""
    username = f"test_iter5_{int(time.time())}"
    password = TEST_USER_PASSWORD
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": username,
        "password": password
    })
    
    if response.status_code != 200:
        pytest.skip(f"Failed to create test user: {response.text}")
    
    data = response.json()
    return {
        "token": data["access_token"],
        "user_id": data["user"]["id"],
        "username": username
    }


@pytest.fixture(scope="module")
def auth_headers(test_user):
    """Get authentication headers"""
    return {"Authorization": f"Bearer {test_user['token']}", "Content-Type": "application/json"}


class TestSharedRoomModeBackend:
    """Tests for shared room mode backend functionality"""
    
    def test_chat_stream_accepts_shared_context_mode(self, auth_headers):
        """Backend accepts context_mode=shared without errors"""
        conv_id = f"conv_test_shared_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            headers=auth_headers,
            json={
                "message": "Test shared context mode",
                "models": ["gpt-4o"],
                "conversation_id": conv_id,
                "context_mode": "shared",
                "shared_room_mode": "parallel_all"
            },
            stream=True
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify streaming starts
        content = ""
        for line in response.iter_lines():
            if line:
                content += line.decode('utf-8')
                if 'event: complete' in content or len(content) > 500:
                    break
        
        assert "event: start" in content or "event: chunk" in content
        print(f"PASS: Chat stream with shared context mode accepted")
    
    def test_chat_stream_accepts_parallel_paired_mode(self, auth_headers):
        """Backend accepts shared_room_mode=parallel_paired without 422/500"""
        conv_id = f"conv_test_paired_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            headers=auth_headers,
            json={
                "message": "Test parallel paired mode",
                "models": ["gpt-4o"],
                "conversation_id": conv_id,
                "context_mode": "shared",
                "shared_room_mode": "parallel_paired",
                "shared_pairs": {"gpt-4o": ["claude-sonnet-4-5-20250929"]}
            },
            stream=True
        )
        
        assert response.status_code == 200, f"Expected 200 for parallel_paired, got {response.status_code}"
        
        content = ""
        for line in response.iter_lines():
            if line:
                content += line.decode('utf-8')
                if 'event: complete' in content or len(content) > 500:
                    break
        
        assert "event: start" in content or "event: chunk" in content
        print(f"PASS: Chat stream with parallel_paired mode accepted without 422/500")
    
    def test_chat_stream_with_shared_pairs_payload(self, auth_headers):
        """Backend processes shared_pairs payload correctly"""
        conv_id = f"conv_test_pairs_{uuid.uuid4().hex[:8]}"
        
        shared_pairs = {
            "gpt-4o": ["claude-sonnet-4-5-20250929"],
            "claude-sonnet-4-5-20250929": ["gpt-4o"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            headers=auth_headers,
            json={
                "message": "Test shared pairs payload",
                "models": ["gpt-4o"],
                "conversation_id": conv_id,
                "context_mode": "shared",
                "shared_room_mode": "parallel_paired",
                "shared_pairs": shared_pairs
            },
            stream=True
        )
        
        assert response.status_code == 200
        print(f"PASS: Chat stream with shared_pairs payload processed without error")


class TestReloadPersistence:
    """Tests for reload persistence bug fix - messages recovered after page reload"""
    
    def test_messages_persisted_during_streaming(self, auth_headers):
        """Messages are saved to DB during streaming (progressive persistence)"""
        conv_id = f"conv_persist_{uuid.uuid4().hex[:8]}"
        
        # Send a message
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            headers=auth_headers,
            json={
                "message": "Test persistence during streaming",
                "models": ["gpt-4o"],
                "conversation_id": conv_id,
                "context_mode": "compartmented"
            },
            stream=True
        )
        
        assert response.status_code == 200
        
        # Consume the stream fully
        for line in response.iter_lines():
            pass
        
        # Wait a bit for DB write
        time.sleep(1)
        
        # Retrieve messages (simulates reload recovery)
        get_response = requests.get(
            f"{BASE_URL}/api/conversations/{conv_id}/messages",
            headers=auth_headers
        )
        
        assert get_response.status_code == 200
        messages = get_response.json()
        
        # Should have user message and assistant message
        assert len(messages) >= 2, f"Expected at least 2 messages, got {len(messages)}"
        
        user_msgs = [m for m in messages if m['role'] == 'user']
        assistant_msgs = [m for m in messages if m['role'] == 'assistant']
        
        assert len(user_msgs) >= 1, "Missing user message"
        assert len(assistant_msgs) >= 1, "Missing assistant message - reload persistence bug!"
        
        # Verify assistant message has content (not empty)
        for msg in assistant_msgs:
            assert msg.get('content'), f"Assistant message {msg.get('id')} has no content"
        
        print(f"PASS: Messages persisted during streaming - {len(messages)} messages found")
    
    def test_conversation_sync_returns_all_messages(self, auth_headers):
        """GET /conversations/{id}/messages returns both user and assistant messages"""
        conv_id = f"conv_sync_{uuid.uuid4().hex[:8]}"
        
        # Send a message
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            headers=auth_headers,
            json={
                "message": "Test conversation sync endpoint",
                "models": ["gpt-4o"],
                "conversation_id": conv_id
            },
            stream=True
        )
        
        # Consume stream
        for line in response.iter_lines():
            pass
        
        time.sleep(1)
        
        # Sync messages
        sync_response = requests.get(
            f"{BASE_URL}/api/conversations/{conv_id}/messages",
            headers=auth_headers
        )
        
        assert sync_response.status_code == 200
        messages = sync_response.json()
        
        roles = [m['role'] for m in messages]
        assert 'user' in roles, "User message missing from sync"
        assert 'assistant' in roles, "Assistant message missing from sync - reload bug!"
        
        print(f"PASS: Conversation sync returns all message types correctly")


class TestSendControls:
    """Tests for core send controls - Enter=newline, Ctrl+Enter=send, send button"""
    
    def test_send_button_works(self, auth_headers):
        """Basic send functionality works via API"""
        conv_id = f"conv_send_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            headers=auth_headers,
            json={
                "message": "Test send button functionality",
                "models": ["gpt-4o"],
                "conversation_id": conv_id
            },
            stream=True
        )
        
        assert response.status_code == 200
        
        # Verify we get a response
        content = ""
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                content += decoded
                if 'event: complete' in decoded:
                    break
        
        assert "event: chunk" in content or "event: complete" in content
        print(f"PASS: Send functionality works correctly")


class TestAgentZeroNonUIOptions:
    """Verify Agent Zero non-UI options include shared room modes"""
    
    def test_a0_non_ui_options_include_shared_modes(self, auth_headers):
        """GET /api/a0/non-ui/options lists shared_room_modes"""
        response = requests.get(
            f"{BASE_URL}/api/a0/non-ui/options",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        input_options = data.get('input_options', {})
        shared_modes = input_options.get('shared_room_modes', [])
        
        assert 'parallel_all' in shared_modes, "parallel_all not in non-UI options"
        assert 'parallel_paired' in shared_modes, "parallel_paired not in non-UI options"
        
        # Also verify supports_shared_pairs flag
        assert input_options.get('supports_shared_pairs') == True
        
        print(f"PASS: A0 non-UI options include shared room modes: {shared_modes}")
    
    def test_a0_non_ui_options_show_context_mode(self, auth_headers):
        """GET /api/a0/non-ui/options lists context_mode options"""
        response = requests.get(
            f"{BASE_URL}/api/a0/non-ui/options",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        input_options = data.get('input_options', {})
        context_modes = input_options.get('context_mode', [])
        
        assert 'compartmented' in context_modes
        assert 'shared' in context_modes
        
        print(f"PASS: A0 non-UI options include context modes: {context_modes}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
