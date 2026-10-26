"""
Iteration 22 Backend Tests - NEW Interaction Patterns
Tests for: shared-room, daisy-chain, synthesize endpoints, context settings
"""

import os
import pytest
import requests
import time

from tests.test_credentials import TEST_USER_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_USER = {"username": "testbot01", "password": TEST_USER_PASSWORD}

# ---- Fixtures ----

@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for testing"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json().get("access_token")
    assert token, "No access_token in response"
    return token

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

# ---- Health & Basic ----

class TestBasicEndpoints:
    """Verify basic endpoints are working"""
    
    def test_health_check(self):
        """GET /api/v1/health - health endpoint"""
        response = requests.get(f"{BASE_URL}/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"Health check passed: {data}")
    
    def test_models_endpoint(self, auth_headers):
        """GET /api/v1/models - returns available models"""
        response = requests.get(f"{BASE_URL}/api/v1/models", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "developers" in data
        assert len(data["developers"]) > 0
        print(f"Models endpoint returned {len(data['developers'])} developers")

# ---- Shared Room Endpoint Tests ----

class TestSharedRoomEndpoint:
    """POST /api/v1/a0/shared-room - Models respond then see each other's responses"""
    
    def test_shared_room_basic(self, auth_headers):
        """Test shared room with 2 models, 1 round"""
        payload = {
            "message": "What is 1+1? Answer in one word.",
            "models": ["gpt-4o-mini", "gemini-2.0-flash"],
            "rounds": 1,
            "mode": "all"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/a0/shared-room",
            json=payload,
            headers=auth_headers,
            timeout=120  # LLM calls can be slow
        )
        assert response.status_code == 200, f"Shared room failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "thread_id" in data
        assert "responses" in data
        assert len(data["responses"]) >= 2, f"Expected at least 2 responses, got {len(data['responses'])}"
        
        # Verify each response has required fields
        for resp in data["responses"]:
            assert "model" in resp
            assert "message_id" in resp
            assert "content" in resp
            assert len(resp["content"]) > 0
            print(f"Shared room response from {resp['model']}: {resp['content'][:100]}...")
        
        print(f"Shared room test PASSED - thread_id: {data['thread_id']}")
        return data
    
    def test_shared_room_with_context(self, auth_headers):
        """Test shared room with global and per-model context"""
        payload = {
            "message": "What is the capital of France?",
            "models": ["gpt-4o-mini"],
            "rounds": 1,
            "mode": "all",
            "global_context": "Answer in exactly one word.",
            "per_model_context": {
                "gpt-4o-mini": {
                    "role": "geography expert",
                    "prompt_modifier": "Be concise"
                }
            }
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/a0/shared-room",
            json=payload,
            headers=auth_headers,
            timeout=60
        )
        assert response.status_code == 200, f"Shared room with context failed: {response.text}"
        data = response.json()
        assert len(data["responses"]) >= 1
        print(f"Shared room with context PASSED: {data['responses'][0]['content'][:50]}...")

# ---- Daisy Chain Endpoint Tests ----

class TestDaisyChainEndpoint:
    """POST /api/v1/a0/daisy-chain - Sequential model→model responses"""
    
    def test_daisy_chain_basic(self, auth_headers):
        """Test daisy chain with 2 models"""
        payload = {
            "message": "Name one prime number.",
            "models": ["gpt-4o-mini", "gemini-2.0-flash"],
            "rounds": 1
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/a0/daisy-chain",
            json=payload,
            headers=auth_headers,
            timeout=120  # Sequential calls take longer
        )
        assert response.status_code == 200, f"Daisy chain failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "thread_id" in data
        assert "responses" in data
        # With 2 models and 1 round, we should get 2 sequential responses
        assert len(data["responses"]) == 2, f"Expected 2 responses, got {len(data['responses'])}"
        
        # First response should be from first model
        assert data["responses"][0]["model"] == "gpt-4o-mini"
        # Second response should be from second model
        assert data["responses"][1]["model"] == "gemini-2.0-flash"
        
        for resp in data["responses"]:
            assert len(resp["content"]) > 0
            print(f"Daisy chain response from {resp['model']}: {resp['content'][:80]}...")
        
        print(f"Daisy chain test PASSED - thread_id: {data['thread_id']}")
        return data
    
    def test_daisy_chain_with_context(self, auth_headers):
        """Test daisy chain with per-model context"""
        payload = {
            "message": "Say hello in one word.",
            "models": ["gpt-4o-mini"],
            "rounds": 1,
            "global_context": "Be extremely brief.",
            "per_model_context": {
                "gpt-4o-mini": {
                    "role": "friendly assistant"
                }
            }
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/a0/daisy-chain",
            json=payload,
            headers=auth_headers,
            timeout=60
        )
        assert response.status_code == 200, f"Daisy chain with context failed: {response.text}"
        data = response.json()
        assert len(data["responses"]) >= 1
        print(f"Daisy chain with context PASSED: {data['responses'][0]['content'][:50]}...")

# ---- Synthesize Endpoint Tests ----

class TestSynthesizeEndpoint:
    """POST /api/v1/a0/synthesize - Feed responses into other models"""
    
    def test_synthesize_basic(self, auth_headers):
        """First get some responses, then synthesize them"""
        # Step 1: Get responses from normal prompt
        prompt_payload = {
            "message": "What is 2+2? Answer in one word.",
            "models": ["gpt-4o-mini", "gemini-2.0-flash"]
        }
        prompt_response = requests.post(
            f"{BASE_URL}/api/v1/a0/prompt",
            json=prompt_payload,
            headers=auth_headers,
            timeout=120
        )
        assert prompt_response.status_code == 200, f"Initial prompt failed: {prompt_response.text}"
        prompt_data = prompt_response.json()
        
        # Extract message IDs from responses
        message_ids = [r["message_id"] for r in prompt_data["responses"]]
        assert len(message_ids) >= 2, "Need at least 2 message IDs for synthesis test"
        
        print(f"Got {len(message_ids)} message IDs for synthesis: {message_ids}")
        
        # Step 2: Synthesize these responses
        synth_payload = {
            "source_message_ids": message_ids,
            "target_models": ["gpt-4o-mini"],
            "synthesis_prompt": "Summarize these AI responses in one sentence:",
            "thread_id": prompt_data["thread_id"]
        }
        synth_response = requests.post(
            f"{BASE_URL}/api/v1/a0/synthesize",
            json=synth_payload,
            headers=auth_headers,
            timeout=60
        )
        assert synth_response.status_code == 200, f"Synthesis failed: {synth_response.text}"
        synth_data = synth_response.json()
        
        # Verify synthesis response
        assert "thread_id" in synth_data
        assert "responses" in synth_data
        assert len(synth_data["responses"]) >= 1
        
        synth_content = synth_data["responses"][0]["content"]
        assert len(synth_content) > 0
        print(f"Synthesis PASSED: {synth_content[:100]}...")
        
        return synth_data
    
    def test_synthesize_invalid_ids(self, auth_headers):
        """Test synthesis with non-existent message IDs"""
        payload = {
            "source_message_ids": ["nonexistent_id_123", "fake_id_456"],
            "target_models": ["gpt-4o-mini"],
            "synthesis_prompt": "Test"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/a0/synthesize",
            json=payload,
            headers=auth_headers,
            timeout=30
        )
        # Should return 404 when no source messages found
        assert response.status_code == 404, f"Expected 404 for invalid IDs, got {response.status_code}"
        print("Synthesis with invalid IDs correctly returns 404")

# ---- Normal Prompt with Context ----

class TestPromptWithContext:
    """POST /api/v1/a0/prompt with global_context and per_model_context"""
    
    def test_prompt_with_global_context(self, auth_headers):
        """Test prompt with global context"""
        payload = {
            "message": "What color is the sky?",
            "models": ["gpt-4o-mini"],
            "global_context": "Answer in exactly one word, no punctuation."
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/a0/prompt",
            json=payload,
            headers=auth_headers,
            timeout=60
        )
        assert response.status_code == 200, f"Prompt with global context failed: {response.text}"
        data = response.json()
        assert len(data["responses"]) >= 1
        print(f"Prompt with global context PASSED: {data['responses'][0]['content'][:50]}...")
    
    def test_prompt_with_per_model_context(self, auth_headers):
        """Test prompt with per-model context (role, system_message, prompt_modifier)"""
        payload = {
            "message": "Explain gravity.",
            "models": ["gpt-4o-mini"],
            "per_model_context": {
                "gpt-4o-mini": {
                    "role": "physics teacher for 5-year-olds",
                    "system_message": "Use simple words only.",
                    "prompt_modifier": "Keep it under 20 words."
                }
            }
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/a0/prompt",
            json=payload,
            headers=auth_headers,
            timeout=60
        )
        assert response.status_code == 200, f"Prompt with per-model context failed: {response.text}"
        data = response.json()
        assert len(data["responses"]) >= 1
        content = data["responses"][0]["content"]
        assert len(content) > 0
        print(f"Prompt with per-model context PASSED: {content[:80]}...")

# ---- Thread History Persistence ----

class TestThreadPersistence:
    """Verify threads from different modes appear in history"""
    
    def test_history_shows_threads(self, auth_headers):
        """GET /api/v1/a0/history - should show threads from all modes"""
        response = requests.get(
            f"{BASE_URL}/api/v1/a0/history",
            headers=auth_headers,
            params={"limit": 20}
        )
        assert response.status_code == 200, f"History failed: {response.text}"
        data = response.json()
        
        assert "threads" in data
        assert "total" in data
        
        if data["total"] > 0:
            # Check thread structure
            thread = data["threads"][0]
            assert "thread_id" in thread
            assert "title" in thread
            assert "models_used" in thread
            print(f"History shows {data['total']} threads")
            
            # Print some thread titles to verify different modes
            for t in data["threads"][:5]:
                print(f"  - {t['title'][:60]} (models: {t.get('models_used', [])})")
        
        print(f"Thread history test PASSED - total threads: {data['total']}")

# ---- Auth Required Tests ----

class TestAuthRequired:
    """Verify all new endpoints require authentication"""
    
    def test_shared_room_requires_auth(self):
        """Shared room without auth should fail"""
        payload = {"message": "test", "models": ["gpt-4o-mini"], "rounds": 1, "mode": "all"}
        response = requests.post(f"{BASE_URL}/api/v1/a0/shared-room", json=payload)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Shared room correctly requires auth")
    
    def test_daisy_chain_requires_auth(self):
        """Daisy chain without auth should fail"""
        payload = {"message": "test", "models": ["gpt-4o-mini"], "rounds": 1}
        response = requests.post(f"{BASE_URL}/api/v1/a0/daisy-chain", json=payload)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Daisy chain correctly requires auth")
    
    def test_synthesize_requires_auth(self):
        """Synthesize without auth should fail"""
        payload = {"source_message_ids": ["test"], "target_models": ["gpt-4o-mini"]}
        response = requests.post(f"{BASE_URL}/api/v1/a0/synthesize", json=payload)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Synthesize correctly requires auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
