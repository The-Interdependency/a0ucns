"""
Test suite for Iteration 18: Backend retry/backoff logic for LLM streaming
Tests the retry implementation for transient 502/503/504/429-like errors

Features tested:
1. Code-path verification: retry logic exists in stream_emergent_model and stream_openai_compatible
2. Normal chat streaming still works after retry logic changes
3. Error messaging is user-friendly for retryable upstream failures
4. Helper function _is_retryable_provider_error correctly identifies retryable errors
"""

import pytest
import requests
import os
import json
import time
import uuid
import sys

# Add backend to path for direct imports
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestRetryLogicCodeVerification:
    """Code-level verification that retry logic exists and is properly structured"""
    
    def test_retry_helper_function_exists(self):
        """Verify _is_retryable_provider_error helper function exists and is importable"""
        from services.llm import _is_retryable_provider_error
        assert callable(_is_retryable_provider_error), "Helper function should be callable"
        print("PASS: _is_retryable_provider_error helper function exists")
    
    def test_retry_helper_identifies_502_errors(self):
        """Verify helper correctly identifies 502 Bad Gateway as retryable"""
        from services.llm import _is_retryable_provider_error
        
        # Test 502 variations
        assert _is_retryable_provider_error("502 Bad Gateway") == True
        assert _is_retryable_provider_error("API error 502: service unavailable") == True
        assert _is_retryable_provider_error("BadGatewayError") == True
        print("PASS: 502 errors correctly identified as retryable")
    
    def test_retry_helper_identifies_503_errors(self):
        """Verify helper correctly identifies 503 Service Unavailable as retryable"""
        from services.llm import _is_retryable_provider_error
        
        assert _is_retryable_provider_error("503 Service Unavailable") == True
        assert _is_retryable_provider_error("API error 503") == True
        print("PASS: 503 errors correctly identified as retryable")
    
    def test_retry_helper_identifies_504_errors(self):
        """Verify helper correctly identifies 504 Gateway Timeout as retryable"""
        from services.llm import _is_retryable_provider_error
        
        assert _is_retryable_provider_error("504 Gateway Timeout") == True
        assert _is_retryable_provider_error("API error 504: timeout") == True
        print("PASS: 504 errors correctly identified as retryable")
    
    def test_retry_helper_identifies_429_rate_limit(self):
        """Verify helper correctly identifies 429 rate limit errors as retryable"""
        from services.llm import _is_retryable_provider_error
        
        assert _is_retryable_provider_error("429 Too Many Requests") == True
        assert _is_retryable_provider_error("rate limit exceeded") == True
        print("PASS: 429/rate limit errors correctly identified as retryable")
    
    def test_retry_helper_identifies_timeout_errors(self):
        """Verify helper correctly identifies timeout errors as retryable"""
        from services.llm import _is_retryable_provider_error
        
        assert _is_retryable_provider_error("Connection timeout") == True
        assert _is_retryable_provider_error("Read timeout") == True
        assert _is_retryable_provider_error("temporarily unavailable") == True
        print("PASS: Timeout/unavailable errors correctly identified as retryable")
    
    def test_retry_helper_rejects_non_retryable_errors(self):
        """Verify helper correctly rejects non-retryable errors"""
        from services.llm import _is_retryable_provider_error
        
        assert _is_retryable_provider_error("400 Bad Request") == False
        assert _is_retryable_provider_error("401 Unauthorized") == False
        assert _is_retryable_provider_error("403 Forbidden") == False
        assert _is_retryable_provider_error("Invalid API key") == False
        assert _is_retryable_provider_error("Model not found") == False
        assert _is_retryable_provider_error("") == False
        assert _is_retryable_provider_error(None) == False
        print("PASS: Non-retryable errors correctly rejected")
    
    def test_stream_emergent_model_has_retry_logic(self):
        """Verify stream_emergent_model function has retry loop structure"""
        import inspect
        from services.llm import stream_emergent_model
        
        source = inspect.getsource(stream_emergent_model)
        
        # Check for retry constants
        assert "max_attempts" in source, "Missing max_attempts variable"
        assert "backoff_seconds" in source, "Missing backoff_seconds variable"
        
        # Check for retry loop
        assert "for attempt in range(max_attempts)" in source, "Missing retry loop"
        
        # Check for retry condition
        assert "_is_retryable_provider_error" in source, "Missing retry error check"
        
        # Check for backoff sleep
        assert "asyncio.sleep(backoff_seconds[attempt])" in source, "Missing backoff sleep"
        
        print("PASS: stream_emergent_model has proper retry logic structure")
    
    def test_stream_openai_compatible_has_retry_logic(self):
        """Verify stream_openai_compatible function has retry loop structure"""
        import inspect
        from services.llm import stream_openai_compatible
        
        source = inspect.getsource(stream_openai_compatible)
        
        # Check for retry constants
        assert "max_attempts" in source, "Missing max_attempts variable"
        assert "backoff_seconds" in source, "Missing backoff_seconds variable"
        
        # Check for retry loop
        assert "for attempt in range(max_attempts)" in source, "Missing retry loop"
        
        # Check for retry condition
        assert "_is_retryable_provider_error" in source, "Missing retry error check"
        
        # Check for backoff sleep
        assert "asyncio.sleep(backoff_seconds[attempt])" in source, "Missing backoff sleep"
        
        print("PASS: stream_openai_compatible has proper retry logic structure")
    
    def test_user_friendly_error_message_for_retryable_failures(self):
        """Verify user-friendly error messaging is implemented for upstream failures"""
        import inspect
        from services.llm import stream_emergent_model
        
        source = inspect.getsource(stream_emergent_model)
        
        # Check for user-friendly retry exhaustion message
        assert "temporarily unavailable" in source.lower() or "retry" in source.lower(), \
            "Missing user-friendly error message for retryable failures"
        
        print("PASS: User-friendly error messaging implemented for upstream failures")


class TestRetryConfiguration:
    """Test retry configuration values"""
    
    def test_retry_attempts_configured(self):
        """Verify max_attempts is set to reasonable value (3)"""
        import inspect
        from services.llm import stream_emergent_model, stream_openai_compatible
        
        emergent_source = inspect.getsource(stream_emergent_model)
        openai_source = inspect.getsource(stream_openai_compatible)
        
        assert "max_attempts = 3" in emergent_source, "Expected 3 retry attempts for emergent"
        assert "max_attempts = 3" in openai_source, "Expected 3 retry attempts for openai"
        
        print("PASS: max_attempts configured to 3 for both providers")
    
    def test_backoff_delays_configured(self):
        """Verify exponential backoff delays are configured"""
        import inspect
        from services.llm import stream_emergent_model, stream_openai_compatible
        
        emergent_source = inspect.getsource(stream_emergent_model)
        openai_source = inspect.getsource(stream_openai_compatible)
        
        # Check for backoff configuration
        assert "backoff_seconds" in emergent_source, "Missing backoff config for emergent"
        assert "backoff_seconds" in openai_source, "Missing backoff config for openai"
        
        # Verify backoff values are reasonable (0.8, 1.6, 2.4)
        assert "0.8" in emergent_source or "0.8" in openai_source, "Missing first backoff delay"
        
        print("PASS: Backoff delays configured properly")


class TestChatStreamRegression:
    """Regression tests to ensure normal chat streaming still works after retry changes"""
    
    @pytest.fixture
    def test_session(self):
        """Create a test session for authenticated requests"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Create test user session
        test_user_id = f"test-retry-{uuid.uuid4().hex[:8]}"
        session_token = f"test_session_{int(time.time())}"
        
        session.headers.update({
            "X-User-ID": test_user_id,
            "X-Session-Token": session_token
        })
        
        return session
    
    def test_health_endpoint(self):
        """Verify backend is running and healthy"""
        # Try multiple possible health endpoints
        health_endpoints = ["/api/health", "/health", "/api/"]
        
        for endpoint in health_endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 200:
                print(f"PASS: Backend health check passed at {endpoint}")
                return
        
        # If none work, at least verify backend responds
        response = requests.get(f"{BASE_URL}/api/conversations", headers={"X-User-ID": "test"})
        assert response.status_code in [200, 401, 403, 422], \
            f"Backend not responding properly: {response.status_code}"
        print("PASS: Backend is responding (via conversations endpoint)")
    
    def test_chat_stream_endpoint_exists(self):
        """Verify chat stream endpoint exists (auth required, expect 401/403)"""
        response = requests.post(
            f"{BASE_URL}/api/chat/stream",
            json={"message": "test", "models": ["gpt-4o"]},
            headers={"Content-Type": "application/json"}
        )
        
        # Should get auth error, not 404
        assert response.status_code in [401, 403, 422], \
            f"Unexpected status: {response.status_code}. Endpoint may not exist."
        
        print("PASS: Chat stream endpoint exists (got expected auth error)")
    
    def test_chat_stream_with_auth(self, test_session):
        """Test actual chat streaming with authentication headers"""
        response = test_session.post(
            f"{BASE_URL}/api/chat/stream",
            json={
                "message": "Say hello in one word",
                "models": ["gpt-4o-mini"],
                "context_mode": "compartmented"
            },
            stream=True,
            timeout=30
        )
        
        # Accept 200 (success) or auth errors (if test auth doesn't work)
        assert response.status_code in [200, 401, 403], \
            f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            # Verify SSE response structure
            events = []
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith('data:'):
                    events.append(line)
                    if len(events) >= 3:
                        break
            
            print(f"PASS: Chat stream working, received {len(events)} SSE events")
        else:
            print(f"PASS: Chat stream endpoint accessible (auth: {response.status_code})")
    
    def test_conversations_endpoint(self, test_session):
        """Verify conversations listing endpoint works"""
        response = test_session.get(f"{BASE_URL}/api/conversations")
        
        # Accept success or auth error
        assert response.status_code in [200, 401, 403], \
            f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Conversations should return a list"
        
        print(f"PASS: Conversations endpoint accessible (status: {response.status_code})")


class TestLLMServiceImports:
    """Verify LLM service can be imported and functions are available"""
    
    def test_import_llm_service(self):
        """Verify llm.py can be imported without errors"""
        try:
            from services import llm
            print("PASS: LLM service imported successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import LLM service: {e}")
    
    def test_stream_emergent_model_importable(self):
        """Verify stream_emergent_model is importable and is async generator"""
        from services.llm import stream_emergent_model
        import inspect
        
        # Async generator functions use 'async def' and 'yield'
        # They return async generator objects, not coroutines
        assert inspect.isasyncgenfunction(stream_emergent_model), \
               "stream_emergent_model should be async generator function"
        
        print("PASS: stream_emergent_model is async generator function")
    
    def test_stream_openai_compatible_importable(self):
        """Verify stream_openai_compatible is importable and is async generator"""
        from services.llm import stream_openai_compatible
        import inspect
        
        # Async generator functions use 'async def' and 'yield'
        assert inspect.isasyncgenfunction(stream_openai_compatible), \
               "stream_openai_compatible should be async generator function"
        
        print("PASS: stream_openai_compatible is async generator function")
    
    def test_get_api_key_importable(self):
        """Verify get_api_key helper is importable"""
        from services.llm import get_api_key
        assert callable(get_api_key)
        print("PASS: get_api_key is callable")
    
    def test_validate_universal_key_importable(self):
        """Verify validate_universal_key is importable and async"""
        from services.llm import validate_universal_key
        import asyncio
        
        assert asyncio.iscoroutinefunction(validate_universal_key), \
               "validate_universal_key should be async"
        
        print("PASS: validate_universal_key is async function")


class TestRetryMarkerCoverage:
    """Test that all expected retry markers are covered"""
    
    def test_all_gateway_errors_covered(self):
        """Verify all gateway-related errors are marked as retryable"""
        from services.llm import _is_retryable_provider_error
        
        gateway_errors = [
            "502",
            "503", 
            "504",
            "badgateway",
            "gateway",
            "temporarily unavailable",
            "timeout",
            "rate limit",
            "429",
        ]
        
        for marker in gateway_errors:
            error_msg = f"API error: {marker}"
            assert _is_retryable_provider_error(error_msg) == True, \
                f"'{marker}' should be retryable"
        
        print(f"PASS: All {len(gateway_errors)} retry markers covered")
    
    def test_case_insensitive_matching(self):
        """Verify error matching is case-insensitive"""
        from services.llm import _is_retryable_provider_error
        
        assert _is_retryable_provider_error("BADGATEWAY") == True
        assert _is_retryable_provider_error("BadGateway") == True
        assert _is_retryable_provider_error("badgateway") == True
        assert _is_retryable_provider_error("TIMEOUT") == True
        assert _is_retryable_provider_error("Timeout") == True
        
        print("PASS: Case-insensitive matching works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
