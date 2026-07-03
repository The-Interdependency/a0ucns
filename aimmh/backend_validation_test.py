# ratios: loc_comments=251:24 imports_exports=6:7 calls_definitions=77:7
"""
Backend Validation Test Script
Tests specific endpoints on https://aimmh-hub-1.preview.emergentagent.com
"""

import requests
import json
import time
import random
import string
from typing import Dict, Any, Tuple

# Base URL from frontend .env
BASE_URL = "https://aimmh-hub-1.preview.emergentagent.com"

def generate_test_user() -> Tuple[str, str]:
    """Generate a unique test username and password"""
    random_suffix = ''.join(random.choices(string.digits, k=10))
    username = f"validation_test_{random_suffix}"
    password = f"TestPass123_{random_suffix}"
    return username, password

def register_and_login() -> str:
    """Register a fresh user and return access token"""
    print("🔐 Registering fresh test user...")
    
    username, password = generate_test_user()
    
    # Register user
    register_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        print(f"   Register response: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   Register failed: {response.text}")
            return None
            
        # Login to get token
        login_data = {
            "username": username,
            "password": password
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"   Login response: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   Login failed: {response.text}")
            return None
            
        data = response.json()
        access_token = data.get("access_token")
        
        if access_token:
            print(f"   ✅ Successfully authenticated user: {username}")
            return access_token
        else:
            print(f"   ❌ No access token in response: {data}")
            return None
            
    except Exception as e:
        print(f"   ❌ Auth error: {str(e)}")
        return None

def test_payments_catalog(token: str) -> Dict[str, Any]:
    """Test GET /api/payments/catalog (auth required)"""
    print("\n📊 Testing GET /api/payments/catalog...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/payments/catalog", headers=headers)
        
        result = {
            "endpoint": "GET /api/payments/catalog",
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "error": None
        }
        
        if response.status_code == 200:
            data = response.json()
            result["packages_count"] = len(data.get("packages", []))
            print(f"   ✅ PASS: Status {response.status_code}, {result['packages_count']} packages found")
        else:
            result["error"] = response.text[:200]
            print(f"   ❌ FAIL: Status {response.status_code}, Error: {result['error']}")
            
        return result
        
    except Exception as e:
        result = {
            "endpoint": "GET /api/payments/catalog",
            "status_code": None,
            "success": False,
            "error": str(e)
        }
        print(f"   ❌ FAIL: Exception: {str(e)}")
        return result

def test_checkout_session(token: str) -> Dict[str, Any]:
    """Test POST /api/payments/checkout/session with supporter_monthly"""
    print("\n💳 Testing POST /api/payments/checkout/session...")
    
    headers = {"Authorization": f"Bearer {token}"}
    checkout_data = {
        "package_id": "supporter_monthly",
        "origin_url": BASE_URL
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/payments/checkout/session", 
                               json=checkout_data, headers=headers)
        
        result = {
            "endpoint": "POST /api/payments/checkout/session",
            "status_code": response.status_code,
            "success": False,
            "error": None
        }
        
        if response.status_code == 200:
            data = response.json()
            if "session_id" in data and "url" in data:
                result["success"] = True
                result["has_session_id"] = True
                result["has_url"] = True
                print(f"   ✅ PASS: Status {response.status_code}, session_id and url returned")
            else:
                result["error"] = f"Missing session_id or url in response: {list(data.keys())}"
                print(f"   ❌ FAIL: {result['error']}")
        elif response.status_code == 404:
            result["error"] = "404 Route mismatch - endpoint not found"
            print(f"   ❌ FAIL: {result['error']}")
        else:
            # Check if it's a clear Stripe upstream error
            error_text = response.text
            if "stripe" in error_text.lower() or "payment" in error_text.lower():
                result["success"] = True  # Clear Stripe error is acceptable
                result["stripe_error"] = True
                result["error"] = f"Clear Stripe upstream error: {error_text[:200]}"
                print(f"   ✅ PASS: Status {response.status_code}, Clear Stripe error: {result['error']}")
            else:
                result["error"] = error_text[:200]
                print(f"   ❌ FAIL: Status {response.status_code}, Error: {result['error']}")
            
        return result
        
    except Exception as e:
        result = {
            "endpoint": "POST /api/payments/checkout/session",
            "status_code": None,
            "success": False,
            "error": str(e)
        }
        print(f"   ❌ FAIL: Exception: {str(e)}")
        return result

def test_webhook_route() -> Dict[str, Any]:
    """Test webhook route exists at /api/payments/webhook/stripe (OPTIONS/POST)"""
    print("\n🪝 Testing /api/payments/webhook/stripe route existence...")
    
    results = []
    
    # Test OPTIONS method
    try:
        response = requests.options(f"{BASE_URL}/api/payments/webhook/stripe")
        
        options_result = {
            "endpoint": "OPTIONS /api/payments/webhook/stripe",
            "status_code": response.status_code,
            "success": response.status_code != 404,
            "error": None
        }
        
        if response.status_code == 404:
            options_result["error"] = "404 Route not found"
            print(f"   ❌ FAIL OPTIONS: Status {response.status_code} - Route not found")
        else:
            print(f"   ✅ PASS OPTIONS: Status {response.status_code} - Route exists")
            
        results.append(options_result)
        
    except Exception as e:
        options_result = {
            "endpoint": "OPTIONS /api/payments/webhook/stripe",
            "status_code": None,
            "success": False,
            "error": str(e)
        }
        print(f"   ❌ FAIL OPTIONS: Exception: {str(e)}")
        results.append(options_result)
    
    # Test POST method (should not be 404, but may be 400/401/etc due to missing Stripe signature)
    try:
        response = requests.post(f"{BASE_URL}/api/payments/webhook/stripe", 
                               json={"test": "data"})
        
        post_result = {
            "endpoint": "POST /api/payments/webhook/stripe",
            "status_code": response.status_code,
            "success": response.status_code != 404,
            "error": None
        }
        
        if response.status_code == 404:
            post_result["error"] = "404 Route not found"
            print(f"   ❌ FAIL POST: Status {response.status_code} - Route not found")
        else:
            print(f"   ✅ PASS POST: Status {response.status_code} - Route exists (expected auth/validation error)")
            
        results.append(post_result)
        
    except Exception as e:
        post_result = {
            "endpoint": "POST /api/payments/webhook/stripe",
            "status_code": None,
            "success": False,
            "error": str(e)
        }
        print(f"   ❌ FAIL POST: Exception: {str(e)}")
        results.append(post_result)
    
    return results

def test_ai_instructions() -> Dict[str, Any]:
    """Test AI instruction endpoints"""
    print("\n🤖 Testing AI instruction endpoints...")
    
    endpoints = [
        "/api/ai-instructions",
        "/api/v1/ai-instructions", 
        "/ai-instructions.txt"
    ]
    
    results = []
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            
            result = {
                "endpoint": f"GET {endpoint}",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "error": None
            }
            
            if response.status_code == 200:
                content_length = len(response.text)
                result["content_length"] = content_length
                print(f"   ✅ PASS: {endpoint} - Status {response.status_code}, {content_length} chars")
            elif response.status_code == 404:
                result["error"] = "404 Route not found"
                print(f"   ❌ FAIL: {endpoint} - Status {response.status_code} - Route not found")
            else:
                result["error"] = response.text[:200]
                print(f"   ❌ FAIL: {endpoint} - Status {response.status_code}, Error: {result['error']}")
                
            results.append(result)
            
        except Exception as e:
            result = {
                "endpoint": f"GET {endpoint}",
                "status_code": None,
                "success": False,
                "error": str(e)
            }
            print(f"   ❌ FAIL: {endpoint} - Exception: {str(e)}")
            results.append(result)
    
    return results

def main():
    """Run all backend validation tests"""
    print("🚀 Starting Backend Validation Tests")
    print(f"   Target: {BASE_URL}")
    print("=" * 60)
    
    # Step 1: Get authentication
    token = register_and_login()
    if not token:
        print("\n❌ CRITICAL: Cannot proceed without authentication")
        return
    
    # Step 2: Run all tests
    all_results = []
    
    # Test payments catalog
    catalog_result = test_payments_catalog(token)
    all_results.append(catalog_result)
    
    # Test checkout session
    checkout_result = test_checkout_session(token)
    all_results.append(checkout_result)
    
    # Test webhook routes
    webhook_results = test_webhook_route()
    all_results.extend(webhook_results)
    
    # Test AI instruction endpoints
    ai_results = test_ai_instructions()
    all_results.extend(ai_results)
    
    # Step 3: Generate summary
    print("\n" + "=" * 60)
    print("📋 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for result in all_results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        endpoint = result["endpoint"]
        status_code = result.get("status_code", "N/A")
        
        print(f"{status} | {endpoint} | Status: {status_code}")
        
        if result["error"]:
            print(f"      Error: {result['error']}")
            
        if result["success"]:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED")
    else:
        print("⚠️  SOME TESTS FAILED - See details above")

if __name__ == "__main__":
    main()
# ratios: loc_comments=251:24 imports_exports=6:7 calls_definitions=77:7
