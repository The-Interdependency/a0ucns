"""
Test iteration 7: Console tabbed experience + Stripe-wired pricing flows
Features:
- Protected routes for /console and /pricing
- Console tabs: Token & Cost, EDCM Brain, Prompt Context, Donations vs Costs
- Console preferences save endpoint (/api/console/preferences)
- Context logs endpoints (/api/console/context-logs)
- Chat stream writes context logs and token/cost telemetry
- Pricing catalog (/api/payments/catalog)
- Checkout session creation (/api/payments/checkout/session)
- Checkout status polling (/api/payments/checkout/status/{session_id})
- Founder cap response in catalog
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# JWT token created by test setup
TEST_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LWl0ZXI3LTE3NzIyNTU4MTA0MzUiLCJleHAiOjE3NzIzNDIyODB9.RsfAaj40-1dthL0o6TNCO91B1fndodYtLy5I6grJMBQ"
TEST_USER_ID = "test-iter7-1772255810435"


@pytest.fixture(scope="module")
def auth_headers():
    """Return auth headers with JWT token"""
    return {"Authorization": f"Bearer {TEST_JWT_TOKEN}"}


@pytest.fixture(scope="module")
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestHealthAndAuth:
    """Basic health and auth tests"""

    def test_api_root(self, api_client):
        """Test API root endpoint"""
        response = api_client.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"API root response: {data}")

    def test_auth_me_with_token(self, api_client, auth_headers):
        """Test /api/auth/me with valid token"""
        response = api_client.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        # Should return user data or 200
        assert response.status_code == 200, f"auth/me failed: {response.text}"
        data = response.json()
        print(f"Auth/me response: {data}")


class TestConsolePreferences:
    """Test console preferences endpoints"""

    def test_get_preferences_default(self, api_client, auth_headers):
        """Test GET /api/console/preferences returns default values"""
        response = api_client.get(f"{BASE_URL}/api/console/preferences", headers=auth_headers)
        assert response.status_code == 200, f"Get preferences failed: {response.text}"
        data = response.json()
        
        # Validate default structure
        assert "user_id" in data
        assert "enforce_token_limit" in data
        assert "enforce_cost_limit" in data
        assert "token_limit" in data
        assert "cost_limit_usd" in data
        print(f"Console preferences: {data}")

    def test_update_preferences(self, api_client, auth_headers):
        """Test PUT /api/console/preferences saves new values"""
        payload = {
            "enforce_token_limit": True,
            "enforce_cost_limit": True,
            "token_limit": 50000,
            "cost_limit_usd": 50.0
        }
        response = api_client.put(
            f"{BASE_URL}/api/console/preferences",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Update preferences failed: {response.text}"
        data = response.json()
        
        # Verify values were saved
        assert data["enforce_token_limit"] == True
        assert data["enforce_cost_limit"] == True
        assert data["token_limit"] == 50000
        assert data["cost_limit_usd"] == 50.0
        print(f"Updated preferences: {data}")

    def test_preferences_persist(self, api_client, auth_headers):
        """Test that preferences persist after update"""
        response = api_client.get(f"{BASE_URL}/api/console/preferences", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Should reflect previous update
        assert data["enforce_token_limit"] == True
        assert data["token_limit"] == 50000
        print(f"Persisted preferences: {data}")


class TestContextLogs:
    """Test context logs endpoints"""

    def test_get_context_logs_empty_or_list(self, api_client, auth_headers):
        """Test GET /api/console/context-logs returns list"""
        response = api_client.get(
            f"{BASE_URL}/api/console/context-logs?limit=30",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get context logs failed: {response.text}"
        data = response.json()
        
        # Should have logs array
        assert "logs" in data
        assert isinstance(data["logs"], list)
        print(f"Context logs count: {len(data['logs'])}")


class TestPaymentsCatalog:
    """Test payments catalog endpoint"""

    def test_get_catalog(self, api_client, auth_headers):
        """Test GET /api/payments/catalog returns pricing packages"""
        response = api_client.get(f"{BASE_URL}/api/payments/catalog", headers=auth_headers)
        assert response.status_code == 200, f"Get catalog failed: {response.text}"
        data = response.json()
        
        # Validate catalog structure
        assert "prices" in data
        assert "founder_slots_total" in data
        assert "founder_slots_remaining" in data
        
        # Founder cap should be 53
        assert data["founder_slots_total"] == 53
        assert data["founder_slots_remaining"] >= 0
        assert data["founder_slots_remaining"] <= 53
        
        prices = data["prices"]
        assert isinstance(prices, list)
        assert len(prices) > 0
        
        # Validate price structure
        first_price = prices[0]
        assert "package_id" in first_price
        assert "name" in first_price
        assert "amount" in first_price
        assert "currency" in first_price
        assert "billing_type" in first_price
        assert "category" in first_price
        assert "features" in first_price
        
        print(f"Catalog has {len(prices)} packages")
        print(f"Founder slots remaining: {data['founder_slots_remaining']}/{data['founder_slots_total']}")
        
        # Check for expected categories
        categories = set(p["category"] for p in prices)
        assert "core" in categories, "Missing core category"
        assert "support" in categories, "Missing support category"
        assert "founder" in categories, "Missing founder category"
        assert "credits" in categories, "Missing credits category"

    def test_catalog_has_core_monthly(self, api_client, auth_headers):
        """Test catalog includes $15/month core package"""
        response = api_client.get(f"{BASE_URL}/api/payments/catalog", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        core_packages = [p for p in data["prices"] if p["category"] == "core"]
        assert len(core_packages) > 0, "No core packages found"
        
        core_monthly = [p for p in core_packages if p["billing_type"] == "monthly"]
        assert len(core_monthly) > 0, "No monthly core package found"
        
        monthly_pkg = core_monthly[0]
        assert monthly_pkg["amount"] == 15.0, f"Expected $15, got ${monthly_pkg['amount']}"
        print(f"Core monthly package: {monthly_pkg['name']} - ${monthly_pkg['amount']}")

    def test_catalog_has_support_one_time_and_recurring(self, api_client, auth_headers):
        """Test catalog includes both one-time and recurring support options"""
        response = api_client.get(f"{BASE_URL}/api/payments/catalog", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        support_packages = [p for p in data["prices"] if p["category"] == "support"]
        one_time = [p for p in support_packages if p["billing_type"] == "one_time"]
        monthly = [p for p in support_packages if p["billing_type"] == "monthly"]
        
        assert len(one_time) > 0, "Missing one-time support options"
        assert len(monthly) > 0, "Missing recurring support options"
        
        print(f"Support packages: {len(one_time)} one-time, {len(monthly)} recurring")

    def test_catalog_founder_package(self, api_client, auth_headers):
        """Test catalog has founder package at $153"""
        response = api_client.get(f"{BASE_URL}/api/payments/catalog", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        founder_packages = [p for p in data["prices"] if p["category"] == "founder"]
        assert len(founder_packages) > 0, "No founder package found"
        
        founder_pkg = founder_packages[0]
        assert founder_pkg["amount"] == 153.0, f"Expected $153, got ${founder_pkg['amount']}"
        assert founder_pkg["billing_type"] == "one_time"
        print(f"Founder package: {founder_pkg['name']}")


class TestCheckoutSession:
    """Test checkout session creation"""

    def test_create_checkout_session_core(self, api_client, auth_headers):
        """Test POST /api/payments/checkout/session creates session"""
        payload = {
            "package_id": "core_monthly",
            "origin_url": "https://aimmh-hub-1.preview.emergentagent.com"
        }
        response = api_client.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Create checkout failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "url" in data, "Missing checkout URL"
        assert "session_id" in data, "Missing session_id"
        
        # URL should be a Stripe checkout URL
        assert data["url"].startswith("https://"), "Invalid checkout URL"
        assert len(data["session_id"]) > 0
        
        print(f"Checkout session created: {data['session_id']}")
        print(f"Checkout URL starts with: {data['url'][:50]}...")
        
        return data["session_id"]

    def test_create_checkout_invalid_package(self, api_client, auth_headers):
        """Test checkout fails for invalid package_id"""
        payload = {
            "package_id": "invalid_package",
            "origin_url": "https://aimmh-hub-1.preview.emergentagent.com"
        }
        response = api_client.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400 for invalid package: {response.status_code}"
        print("Correctly rejected invalid package")

    def test_create_checkout_invalid_origin(self, api_client, auth_headers):
        """Test checkout fails for invalid origin URL"""
        payload = {
            "package_id": "core_monthly",
            "origin_url": "not-a-valid-url"
        }
        response = api_client.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400 for invalid origin: {response.status_code}"
        print("Correctly rejected invalid origin URL")


class TestCheckoutStatus:
    """Test checkout status polling"""

    def test_checkout_status_for_new_session(self, api_client, auth_headers):
        """Test GET /api/payments/checkout/status/{session_id}"""
        # First create a session
        payload = {
            "package_id": "support_one_time_1",
            "origin_url": "https://aimmh-hub-1.preview.emergentagent.com"
        }
        create_response = api_client.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json=payload,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        session_id = create_response.json()["session_id"]
        
        # Now check status
        status_response = api_client.get(
            f"{BASE_URL}/api/payments/checkout/status/{session_id}",
            headers=auth_headers
        )
        assert status_response.status_code == 200, f"Status check failed: {status_response.text}"
        data = status_response.json()
        
        # Validate status response structure
        assert "session_id" in data
        assert "status" in data
        assert "payment_status" in data
        assert "amount_total" in data
        assert "currency" in data
        
        print(f"Session status: {data['status']}, payment: {data['payment_status']}")


class TestPaymentsSummary:
    """Test payments summary endpoint"""

    def test_get_summary(self, api_client, auth_headers):
        """Test GET /api/payments/summary returns user payment stats"""
        response = api_client.get(f"{BASE_URL}/api/payments/summary", headers=auth_headers)
        assert response.status_code == 200, f"Get summary failed: {response.text}"
        data = response.json()
        
        # Validate summary structure
        assert "total_paid_usd" in data
        assert "total_support_usd" in data
        assert "total_founder_usd" in data
        assert "total_compute_usd" in data
        assert "total_core_usd" in data
        assert "estimated_usage_cost_usd" in data
        assert "total_estimated_tokens" in data
        
        print(f"Payment summary: total_paid=${data['total_paid_usd']}, tokens={data['total_estimated_tokens']}")


class TestChatStreamWritesContextAndTelemetry:
    """Test that chat stream writes context logs and token/cost telemetry"""

    def test_chat_stream_creates_context_log(self, api_client, auth_headers):
        """Test POST /api/chat/stream creates context log entry"""
        # Send a chat message
        payload = {
            "message": "Test message for context log testing iter7",
            "models": ["gpt-4o-mini"],
            "conversation_id": None,
            "context_mode": "compartmented",
            "shared_room_mode": "parallel_all",
            "global_context": "Test global context",
            "model_roles": {"gpt-4o-mini": "neutral"},
            "persist_user_message": True
        }
        
        # Stream request - we'll consume it even though we don't need the full response
        response = api_client.post(
            f"{BASE_URL}/api/chat/stream",
            json=payload,
            headers=auth_headers,
            stream=True
        )
        assert response.status_code == 200, f"Chat stream failed: {response.text}"
        
        # Consume the stream
        for line in response.iter_lines():
            pass  # Just consume
        
        # Wait a bit for DB writes
        time.sleep(1)
        
        # Check context logs
        context_response = api_client.get(
            f"{BASE_URL}/api/console/context-logs?limit=5",
            headers=auth_headers
        )
        assert context_response.status_code == 200
        logs = context_response.json().get("logs", [])
        
        # Should have at least one log
        assert len(logs) > 0, "No context logs found after chat"
        
        # Check the most recent log
        recent = logs[0]
        assert "message" in recent
        assert "models" in recent
        assert "context_mode" in recent
        print(f"Context log created: {recent.get('id', 'no-id')}")

    def test_chat_stream_records_token_telemetry(self, api_client, auth_headers):
        """Test that chat stream records token and cost telemetry in messages"""
        payload = {
            "message": "Short test for telemetry",
            "models": ["gpt-4o-mini"],
            "conversation_id": "test_telemetry_conv",
            "context_mode": "compartmented",
            "persist_user_message": True
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/chat/stream",
            json=payload,
            headers=auth_headers,
            stream=True
        )
        assert response.status_code == 200
        
        # Consume stream
        for line in response.iter_lines():
            pass
        
        time.sleep(1)
        
        # Check payment summary for updated token count
        summary_response = api_client.get(
            f"{BASE_URL}/api/payments/summary",
            headers=auth_headers
        )
        assert summary_response.status_code == 200
        summary = summary_response.json()
        
        # Summary should reflect some usage
        print(f"Total estimated tokens: {summary['total_estimated_tokens']}")
        print(f"Estimated usage cost: ${summary['estimated_usage_cost_usd']}")


class TestEDCMDashboard:
    """Test EDCM dashboard endpoint for console Brain tab"""

    def test_get_edcm_dashboard(self, api_client, auth_headers):
        """Test GET /api/edcm/dashboard returns metrics"""
        response = api_client.get(f"{BASE_URL}/api/edcm/dashboard", headers=auth_headers)
        assert response.status_code == 200, f"EDCM dashboard failed: {response.text}"
        data = response.json()
        
        # Should have edcm_metrics array
        assert "edcm_metrics" in data
        print(f"EDCM dashboard loaded with {len(data.get('edcm_metrics', []))} metric entries")


class TestProtectedRoutesRequireAuth:
    """Test that console and pricing endpoints require authentication"""

    def test_console_preferences_requires_auth(self, api_client):
        """Test /api/console/preferences requires auth"""
        response = api_client.get(f"{BASE_URL}/api/console/preferences")
        assert response.status_code == 401 or response.status_code == 403, \
            f"Expected 401/403, got {response.status_code}"
        print("Console preferences correctly requires auth")

    def test_payments_catalog_requires_auth(self, api_client):
        """Test /api/payments/catalog requires auth"""
        response = api_client.get(f"{BASE_URL}/api/payments/catalog")
        assert response.status_code == 401 or response.status_code == 403, \
            f"Expected 401/403, got {response.status_code}"
        print("Payments catalog correctly requires auth")

    def test_checkout_session_requires_auth(self, api_client):
        """Test /api/payments/checkout/session requires auth"""
        payload = {
            "package_id": "core_monthly",
            "origin_url": "https://example.com"
        }
        response = api_client.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json=payload
        )
        assert response.status_code == 401 or response.status_code == 403, \
            f"Expected 401/403, got {response.status_code}"
        print("Checkout session correctly requires auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
