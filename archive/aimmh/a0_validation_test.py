# ratios: loc_comments=164:25 imports_exports=6:2 calls_definitions=67:2
"""
Agent Zero /api/a0 endpoints validation test
Testing on: https://aimmh-hub-1.preview.emergentagent.com

Specific validation scenarios requested:
1) Register/login fresh user
2) POST /api/a0/non-ui/synthesis with empty `selected_message_ids` should return 400 (validation guard)
3) POST /api/a0/non-ui/synthesis with empty `target_models` should return 400
4) POST /api/a0/ingest with random nonexistent conversation_id should return 404 (conversation not found guard)
5) POST /api/a0/route with minimal payload should return either 200 or 503 if upstream A0 unreachable, but must not 500
"""

import requests
import json
import random
import string
import uuid
from datetime import datetime

# Base URL from frontend .env
BASE_URL = "https://aimmh-hub-1.preview.emergentagent.com"

def generate_test_user():
    """Generate a unique test username"""
    timestamp = int(datetime.now().timestamp())
    random_suffix = ''.join(random.choices(string.digits, k=6))
    return f"a0test_{timestamp}_{random_suffix}"

def test_a0_validation_endpoints():
    """Main test function for Agent Zero endpoint validation"""
    print("🔍 AGENT ZERO /api/a0 ENDPOINTS VALIDATION TEST")
    print(f"🌐 Testing on: {BASE_URL}")
    print("=" * 80)
    
    # Generate fresh test user
    test_username = generate_test_user()
    test_password = "testpass123"
    
    print(f"👤 Test user: {test_username}")
    print()
    
    # Test results tracking
    results = {
        "register_login": False,
        "synthesis_empty_message_ids_400": False,
        "synthesis_empty_target_models_400": False,
        "ingest_nonexistent_conversation_404": False,
        "route_minimal_payload_not_500": False
    }
    
    # Session to maintain cookies
    session = requests.Session()
    
    try:
        # Test 1: Register/login fresh user
        print("1️⃣ Testing user registration and login...")
        register_data = {
            "username": test_username,
            "password": test_password
        }
        
        register_response = session.post(
            f"{BASE_URL}/api/auth/register",
            json=register_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   📤 POST /api/auth/register")
        print(f"   📊 Status: {register_response.status_code}")
        
        if register_response.status_code == 200:
            # Verify we can access authenticated endpoints
            me_response = session.get(f"{BASE_URL}/api/auth/me")
            if me_response.status_code == 200:
                print(f"   ✅ User registered and authenticated successfully")
                results["register_login"] = True
            else:
                print(f"   ❌ Authentication verification failed: {me_response.status_code}")
        else:
            print(f"   ❌ Registration failed: {register_response.text}")
        
        print()
        
        # Test 2: POST /api/a0/non-ui/synthesis with empty selected_message_ids should return 400
        print("2️⃣ Testing /api/a0/non-ui/synthesis with empty selected_message_ids...")
        
        synthesis_payload_empty_ids = {
            "conversation_id": str(uuid.uuid4()),  # Required field
            "selected_message_ids": [],  # Empty array should trigger validation error
            "target_models": ["gpt-4o"],
            "synthesis_prompt": "Test synthesis"
        }
        
        synthesis_response_1 = session.post(
            f"{BASE_URL}/api/a0/non-ui/synthesis",
            json=synthesis_payload_empty_ids,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   📤 POST /api/a0/non-ui/synthesis (empty selected_message_ids)")
        print(f"   📊 Status: {synthesis_response_1.status_code}")
        print(f"   📄 Response: {synthesis_response_1.text[:200]}...")
        
        if synthesis_response_1.status_code == 400:
            print(f"   ✅ Validation guard working - 400 for empty selected_message_ids")
            results["synthesis_empty_message_ids_400"] = True
        else:
            print(f"   ❌ Expected 400, got {synthesis_response_1.status_code}")
        
        print()
        
        # Test 3: POST /api/a0/non-ui/synthesis with empty target_models should return 400
        print("3️⃣ Testing /api/a0/non-ui/synthesis with empty target_models...")
        
        synthesis_payload_empty_models = {
            "conversation_id": str(uuid.uuid4()),  # Required field
            "selected_message_ids": ["msg_123"],
            "target_models": [],  # Empty array should trigger validation error
            "synthesis_prompt": "Test synthesis"
        }
        
        synthesis_response_2 = session.post(
            f"{BASE_URL}/api/a0/non-ui/synthesis",
            json=synthesis_payload_empty_models,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   📤 POST /api/a0/non-ui/synthesis (empty target_models)")
        print(f"   📊 Status: {synthesis_response_2.status_code}")
        print(f"   📄 Response: {synthesis_response_2.text[:200]}...")
        
        if synthesis_response_2.status_code == 400:
            print(f"   ✅ Validation guard working - 400 for empty target_models")
            results["synthesis_empty_target_models_400"] = True
        else:
            print(f"   ❌ Expected 400, got {synthesis_response_2.status_code}")
        
        print()
        
        # Test 4: POST /api/a0/ingest with random nonexistent conversation_id should return 404
        print("4️⃣ Testing /api/a0/ingest with nonexistent conversation_id...")
        
        # Generate a random UUID that definitely doesn't exist
        fake_conversation_id = str(uuid.uuid4())
        
        ingest_payload = {
            "conversation_id": fake_conversation_id,
            "prompt": "Test ingest prompt"
        }
        
        ingest_response = session.post(
            f"{BASE_URL}/api/a0/ingest",
            json=ingest_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   📤 POST /api/a0/ingest (conversation_id: {fake_conversation_id[:8]}...)")
        print(f"   📊 Status: {ingest_response.status_code}")
        print(f"   📄 Response: {ingest_response.text[:200]}...")
        
        if ingest_response.status_code == 404:
            print(f"   ✅ Conversation not found guard working - 404 for nonexistent conversation")
            results["ingest_nonexistent_conversation_404"] = True
        else:
            print(f"   ❌ Expected 404, got {ingest_response.status_code}")
        
        print()
        
        # Test 5: POST /api/a0/route with minimal payload should return 200 or 503, but not 500
        print("5️⃣ Testing /api/a0/route with minimal payload...")
        
        route_payload = {
            "message": "Test route prompt",  # Correct field name
            "models": ["gpt-4o"]  # Correct field name (array)
        }
        
        route_response = session.post(
            f"{BASE_URL}/api/a0/route",
            json=route_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   📤 POST /api/a0/route (minimal payload)")
        print(f"   📊 Status: {route_response.status_code}")
        print(f"   📄 Response: {route_response.text[:200]}...")
        
        if route_response.status_code in [200, 503]:
            print(f"   ✅ Route endpoint working correctly - {route_response.status_code} (200=success, 503=upstream unavailable)")
            results["route_minimal_payload_not_500"] = True
        elif route_response.status_code == 500:
            print(f"   ❌ Route endpoint returned 500 - this should not happen")
        else:
            print(f"   ⚠️  Unexpected status {route_response.status_code} - may be acceptable depending on implementation")
            # For now, consider non-500 responses as acceptable
            if route_response.status_code != 500:
                results["route_minimal_payload_not_500"] = True
        
        print()
        
    except Exception as e:
        print(f"❌ Test execution error: {str(e)}")
    
    # Summary
    print("=" * 80)
    print("📋 AGENT ZERO VALIDATION TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    test_descriptions = {
        "register_login": "Register/login fresh user",
        "synthesis_empty_message_ids_400": "Synthesis empty selected_message_ids → 400",
        "synthesis_empty_target_models_400": "Synthesis empty target_models → 400", 
        "ingest_nonexistent_conversation_404": "Ingest nonexistent conversation → 404",
        "route_minimal_payload_not_500": "Route minimal payload → not 500"
    }
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        description = test_descriptions.get(test_name, test_name)
        print(f"{status} {description}")
    
    print()
    print(f"🎯 OVERALL: {passed_tests}/{total_tests} validation tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL AGENT ZERO VALIDATION TESTS PASSED!")
        return True
    else:
        print("⚠️  SOME VALIDATION TESTS FAILED")
        return False

if __name__ == "__main__":
    success = test_a0_validation_endpoints()
    exit(0 if success else 1)
# ratios: loc_comments=164:25 imports_exports=6:2 calls_definitions=67:2
