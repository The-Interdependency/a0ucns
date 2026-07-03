"""
Test iteration 8: Chat history persistence, Pricing page, Checkout flows
Features to test:
- Chat refresh persistence for current conversation only
- Manual refresh from logs behavior when no active conversation
- Pricing page loads catalog and summary under auth
- Checkout session creation from pricing package buttons returns redirect URL
- Checkout status polling flow works when session_id exists in URL
- Support recurring switch updates shown support packages
- Founder package card disabled when slots are 0
- Thumbs up feedback API flow from chat
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://aimmh-hub-1.preview.emergentagent.com").rstrip("/")

# Test user credentials
TEST_USER_ID = "test-iter8-1772297459823"
TEST_SESSION_TOKEN = "test_session_iter8_1772297459823"
TEST_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LWl0ZXI4LTE3NzIyOTc0NTk4MjMiLCJleHAiOjE3NzIzODM4NjR9.iZrQLSZ5P7tdpgulSu3nl2BhZPX_NCXgKqYxyF8bZMk"
TEST_CONVERSATION_ID = "test_conv_iter8_1772297459839"


@pytest.fixture(scope="module")
def auth_headers():
    """Return auth headers with JWT token"""
    return {"Authorization": f"Bearer {TEST_JWT_TOKEN}"}


@pytest.fixture(scope="module")
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestConversationMessagesPersistence:
    """Test chat refresh persistence - GET /api/conversations/{id}/messages"""

    def test_get_conversation_messages_returns_persisted_messages(self, api_client, auth_headers):
        """Test that GET /api/conversations/{id}/messages returns previously stored messages"""
        response = api_client.get(
            f"{BASE_URL}/api/conversations/{TEST_CONVERSATION_ID}/messages",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get messages failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Expected list of messages"
        assert len(data) >= 2, f"Expected at least 2 seeded messages, got {len(data)}"
        
        # Verify message structure
        user_messages = [m for m in data if m.get("role") == "user"]
        assistant_messages = [m for m in data if m.get("role") == "assistant"]
        
        assert len(user_messages) >= 1, "Expected at least 1 user message"
        assert len(assistant_messages) >= 1, "Expected at least 1 assistant message"
        
        # Verify message fields
        for msg in data:
            assert "id" in msg
            assert "role" in msg
            assert "content" in msg
            assert "conversation_id" in msg
            
        print(f"Retrieved {len(data)} messages from conversation")
        print(f"User messages: {len(user_messages)}, Assistant messages: {len(assistant_messages)}")

    def test_get_conversation_messages_nonexistent_returns_empty(self, api_client, auth_headers):
        """Test that getting messages from non-existent conversation returns empty list"""
        response = api_client.get(
            f"{BASE_URL}/api/conversations/nonexistent_conv_id_12345/messages",
            headers=auth_headers
        )
        # Should return 200 with empty array (not 404)
        assert response.status_code == 200, f"Expected 200 for nonexistent conv: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected empty list"
        assert len(data) == 0, "Expected empty list for nonexistent conversation"
        print("Correctly returns empty list for nonexistent conversation")

    def test_conversation_messages_requires_auth(self, api_client):
        """Test that /api/conversations/{id}/messages requires authentication"""
        response = api_client.get(
            f"{BASE_URL}/api/conversations/{TEST_CONVERSATION_ID}/messages"
        )
        assert response.status_code in [401, 403], \
            f"Expected 401/403, got {response.status_code}"
        print("Conversation messages endpoint correctly requires auth")


class TestChatFeedbackEndpoint:
    """Test thumbs up/down feedback API - POST /api/chat/feedback"""

    def test_submit_feedback_thumbs_up(self, api_client, auth_headers):
        """Test submitting thumbs up feedback for a message"""
        # First get messages to find a valid message ID
        msg_response = api_client.get(
            f"{BASE_URL}/api/conversations/{TEST_CONVERSATION_ID}/messages",
            headers=auth_headers
        )
        assert msg_response.status_code == 200
        messages = msg_response.json()
        
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]
        if not assistant_messages:
            pytest.skip("No assistant messages to test feedback on")
        
        message_id = assistant_messages[0]["id"]
        
        # Submit thumbs up feedback
        feedback_payload = {
            "message_id": message_id,
            "feedback": "up"
        }
        response = api_client.post(
            f"{BASE_URL}/api/chat/feedback",
            json=feedback_payload,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Feedback submission failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"Successfully submitted thumbs up for message {message_id}")

    def test_submit_feedback_thumbs_down(self, api_client, auth_headers):
        """Test submitting thumbs down feedback for a message"""
        # Create a new message to test feedback
        unique_id = f"msg_feedback_test_{uuid.uuid4().hex[:8]}"
        
        # Insert a test message first via chat stream
        chat_payload = {
            "message": "Test message for feedback testing",
            "models": ["gpt-4o-mini"],
            "conversation_id": f"feedback_test_conv_{uuid.uuid4().hex[:8]}",
            "context_mode": "compartmented",
            "persist_user_message": True
        }
        
        stream_response = api_client.post(
            f"{BASE_URL}/api/chat/stream",
            json=chat_payload,
            headers=auth_headers,
            stream=True
        )
        
        # Consume the stream to get message ID
        message_id = None
        for line in stream_response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data:'):
                    try:
                        import json
                        data = json.loads(line_str[5:].strip())
                        if data.get("message_id"):
                            message_id = data["message_id"]
                    except:
                        pass
        
        if message_id:
            time.sleep(0.5)
            feedback_payload = {
                "message_id": message_id,
                "feedback": "down"
            }
            response = api_client.post(
                f"{BASE_URL}/api/chat/feedback",
                json=feedback_payload,
                headers=auth_headers
            )
            assert response.status_code == 200, f"Feedback submission failed: {response.text}"
            print(f"Successfully submitted thumbs down for message {message_id}")
        else:
            # Fallback to existing message
            msg_response = api_client.get(
                f"{BASE_URL}/api/conversations/{TEST_CONVERSATION_ID}/messages",
                headers=auth_headers
            )
            messages = msg_response.json()
            assistant_messages = [m for m in messages if m.get("role") == "assistant"]
            if assistant_messages:
                message_id = assistant_messages[0]["id"]
                feedback_payload = {
                    "message_id": message_id,
                    "feedback": "down"
                }
                response = api_client.post(
                    f"{BASE_URL}/api/chat/feedback",
                    json=feedback_payload,
                    headers=auth_headers
                )
                assert response.status_code == 200
                print(f"Successfully submitted thumbs down for existing message {message_id}")

    def test_feedback_nonexistent_message_returns_404(self, api_client, auth_headers):
        """Test that feedback on nonexistent message returns 404"""
        feedback_payload = {
            "message_id": "nonexistent_message_id_xyz",
            "feedback": "up"
        }
        response = api_client.post(
            f"{BASE_URL}/api/chat/feedback",
            json=feedback_payload,
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404 for nonexistent message: {response.status_code}"
        print("Correctly returns 404 for feedback on nonexistent message")

    def test_feedback_requires_auth(self, api_client):
        """Test that /api/chat/feedback requires authentication"""
        feedback_payload = {
            "message_id": "any_message_id",
            "feedback": "up"
        }
        response = api_client.post(
            f"{BASE_URL}/api/chat/feedback",
            json=feedback_payload
        )
        assert response.status_code in [401, 403], \
            f"Expected 401/403, got {response.status_code}"
        print("Feedback endpoint correctly requires auth")


class TestPricingCatalogAndSummary:
    """Test pricing page data loading - catalog and summary endpoints"""

    def test_catalog_loads_all_package_categories(self, api_client, auth_headers):
        """Test GET /api/payments/catalog returns all package categories"""
        response = api_client.get(f"{BASE_URL}/api/payments/catalog", headers=auth_headers)
        assert response.status_code == 200, f"Catalog load failed: {response.text}"
        data = response.json()
        
        assert "prices" in data
        assert "founder_slots_total" in data
        assert "founder_slots_remaining" in data
        
        prices = data["prices"]
        categories = set(p["category"] for p in prices)
        
        # Verify all expected categories exist
        assert "core" in categories, "Missing core packages"
        assert "support" in categories, "Missing support packages"
        assert "founder" in categories, "Missing founder packages"
        assert "credits" in categories, "Missing credits packages"
        
        print(f"Catalog loaded with {len(prices)} packages across {len(categories)} categories")
        print(f"Categories: {categories}")

    def test_catalog_support_has_one_time_and_monthly(self, api_client, auth_headers):
        """Test support packages include both one_time and monthly billing types"""
        response = api_client.get(f"{BASE_URL}/api/payments/catalog", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        support_packages = [p for p in data["prices"] if p["category"] == "support"]
        one_time = [p for p in support_packages if p["billing_type"] == "one_time"]
        monthly = [p for p in support_packages if p["billing_type"] == "monthly"]
        
        assert len(one_time) >= 3, f"Expected at least 3 one-time support options, got {len(one_time)}"
        assert len(monthly) >= 3, f"Expected at least 3 monthly support options, got {len(monthly)}"
        
        # Verify amounts - $1, $2, $5 options
        one_time_amounts = sorted([p["amount"] for p in one_time])
        monthly_amounts = sorted([p["amount"] for p in monthly])
        
        assert 1.0 in one_time_amounts, "Missing $1 one-time support"
        assert 2.0 in one_time_amounts, "Missing $2 one-time support"
        assert 5.0 in one_time_amounts, "Missing $5 one-time support"
        
        assert 1.0 in monthly_amounts, "Missing $1/month recurring support"
        assert 2.0 in monthly_amounts, "Missing $2/month recurring support"
        assert 5.0 in monthly_amounts, "Missing $5/month recurring support"
        
        print(f"Support packages: {len(one_time)} one-time ({one_time_amounts}), {len(monthly)} monthly ({monthly_amounts})")

    def test_summary_loads_user_payment_stats(self, api_client, auth_headers):
        """Test GET /api/payments/summary returns user payment statistics"""
        response = api_client.get(f"{BASE_URL}/api/payments/summary", headers=auth_headers)
        assert response.status_code == 200, f"Summary load failed: {response.text}"
        data = response.json()
        
        # Verify all expected fields exist
        required_fields = [
            "total_paid_usd",
            "total_support_usd",
            "total_founder_usd",
            "total_compute_usd",
            "total_core_usd",
            "estimated_usage_cost_usd",
            "total_estimated_tokens"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
            
        # Values should be numbers
        assert isinstance(data["total_paid_usd"], (int, float))
        assert isinstance(data["total_estimated_tokens"], int)
        
        print(f"Summary loaded: total_paid=${data['total_paid_usd']}, tokens={data['total_estimated_tokens']}")

    def test_founder_slots_count(self, api_client, auth_headers):
        """Test catalog returns founder slot information"""
        response = api_client.get(f"{BASE_URL}/api/payments/catalog", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["founder_slots_total"] == 53, "Founder total should be 53"
        assert 0 <= data["founder_slots_remaining"] <= 53, "Founder remaining out of range"
        
        print(f"Founder slots: {data['founder_slots_remaining']}/{data['founder_slots_total']}")


class TestCheckoutSessionAndStatus:
    """Test checkout session creation and status polling"""

    def test_checkout_session_returns_url_and_session_id(self, api_client, auth_headers):
        """Test POST /api/payments/checkout/session returns redirect URL"""
        payload = {
            "package_id": "core_monthly",
            "origin_url": "https://aimmh-hub-1.preview.emergentagent.com"
        }
        response = api_client.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Checkout session creation failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "url" in data, "Missing checkout URL"
        assert "session_id" in data, "Missing session_id"
        
        # URL should be a valid Stripe checkout URL
        assert data["url"].startswith("https://"), "Invalid URL format"
        assert "checkout.stripe.com" in data["url"] or "stripe.com" in data["url"], \
            "URL should be Stripe checkout URL"
        
        # Session ID should not be empty
        assert len(data["session_id"]) > 0, "Empty session_id"
        
        print(f"Checkout session created: {data['session_id']}")
        print(f"URL prefix: {data['url'][:60]}...")
        
        return data["session_id"]

    def test_checkout_status_polling_works(self, api_client, auth_headers):
        """Test GET /api/payments/checkout/status/{session_id} returns status"""
        # First create a session
        create_payload = {
            "package_id": "support_one_time_1",
            "origin_url": "https://aimmh-hub-1.preview.emergentagent.com"
        }
        create_response = api_client.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json=create_payload,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        session_id = create_response.json()["session_id"]
        
        # Now poll status
        status_response = api_client.get(
            f"{BASE_URL}/api/payments/checkout/status/{session_id}",
            headers=auth_headers
        )
        assert status_response.status_code == 200, f"Status polling failed: {status_response.text}"
        data = status_response.json()
        
        # Verify status response structure
        assert "session_id" in data
        assert "status" in data
        assert "payment_status" in data
        assert "amount_total" in data
        assert "currency" in data
        
        # For a fresh session, status should be open/pending
        assert data["session_id"] == session_id
        assert data["status"] in ["open", "complete", "expired"], f"Unexpected status: {data['status']}"
        assert data["payment_status"] in ["unpaid", "paid", "pending", "no_payment_required"], \
            f"Unexpected payment_status: {data['payment_status']}"
        
        print(f"Session {session_id} status: {data['status']}, payment: {data['payment_status']}")

    def test_checkout_different_packages(self, api_client, auth_headers):
        """Test checkout works for different package types"""
        package_ids = ["credits_10", "support_monthly_2", "founder_one_time"]
        
        for package_id in package_ids:
            payload = {
                "package_id": package_id,
                "origin_url": "https://aimmh-hub-1.preview.emergentagent.com"
            }
            response = api_client.post(
                f"{BASE_URL}/api/payments/checkout/session",
                json=payload,
                headers=auth_headers
            )
            assert response.status_code == 200, f"Checkout failed for {package_id}: {response.text}"
            data = response.json()
            assert "url" in data
            assert "session_id" in data
            print(f"Checkout session for {package_id}: {data['session_id'][:20]}...")

    def test_checkout_requires_auth(self, api_client):
        """Test checkout session creation requires authentication"""
        payload = {
            "package_id": "core_monthly",
            "origin_url": "https://aimmh-hub-1.preview.emergentagent.com"
        }
        response = api_client.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json=payload
        )
        assert response.status_code in [401, 403], \
            f"Expected 401/403, got {response.status_code}"
        print("Checkout correctly requires auth")


class TestChatStreamPersistence:
    """Test chat stream persists messages and creates conversation"""

    def test_chat_stream_persists_and_retrievable(self, api_client, auth_headers):
        """Test that chat stream persists messages that can be retrieved later"""
        # Create a unique conversation
        conv_id = f"test_persist_{uuid.uuid4().hex[:8]}"
        
        # Send a chat message
        chat_payload = {
            "message": "Test persistence message iter8",
            "models": ["gpt-4o-mini"],
            "conversation_id": conv_id,
            "context_mode": "compartmented",
            "persist_user_message": True
        }
        
        stream_response = api_client.post(
            f"{BASE_URL}/api/chat/stream",
            json=chat_payload,
            headers=auth_headers,
            stream=True
        )
        assert stream_response.status_code == 200
        
        # Consume stream
        for line in stream_response.iter_lines():
            pass
        
        time.sleep(1)  # Wait for persistence
        
        # Now retrieve messages
        get_response = api_client.get(
            f"{BASE_URL}/api/conversations/{conv_id}/messages",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        messages = get_response.json()
        
        assert len(messages) >= 2, f"Expected at least 2 messages (user + assistant), got {len(messages)}"
        
        roles = [m["role"] for m in messages]
        assert "user" in roles, "Missing user message in persisted conversation"
        assert "assistant" in roles, "Missing assistant message in persisted conversation"
        
        print(f"Chat stream persisted {len(messages)} messages to conversation {conv_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
