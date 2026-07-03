# ratios: loc_comments=68:8 imports_exports=4:3 calls_definitions=33:3
"""
Detailed validation of checkout session response
"""

import requests
import json
import random
import string

BASE_URL = "https://aimmh-hub-1.preview.emergentagent.com"

def generate_test_user():
    random_suffix = ''.join(random.choices(string.digits, k=10))
    username = f"detailed_test_{random_suffix}"
    password = f"TestPass123_{random_suffix}"
    return username, password

def get_auth_token():
    username, password = generate_test_user()
    
    # Register
    register_data = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    
    if response.status_code != 200:
        print(f"Register failed: {response.text}")
        return None
    
    # Login
    login_data = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return None
        
    return response.json().get("access_token")

def main():
    print("🔍 Detailed Checkout Session Validation")
    print("=" * 50)
    
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    
    print("✅ Authentication successful")
    
    # Test checkout session with detailed response inspection
    headers = {"Authorization": f"Bearer {token}"}
    checkout_data = {
        "package_id": "supporter_monthly",
        "origin_url": BASE_URL
    }
    
    print(f"\n📋 Testing checkout session with:")
    print(f"   package_id: {checkout_data['package_id']}")
    print(f"   origin_url: {checkout_data['origin_url']}")
    
    response = requests.post(f"{BASE_URL}/api/payments/checkout/session", 
                           json=checkout_data, headers=headers)
    
    print(f"\n📊 Response Details:")
    print(f"   Status Code: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS - Response contains:")
        for key, value in data.items():
            if key == "url" and len(str(value)) > 100:
                print(f"   {key}: {str(value)[:100]}...")
            else:
                print(f"   {key}: {value}")
                
        # Validate required fields
        required_fields = ["session_id", "url"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"\n❌ Missing required fields: {missing_fields}")
        else:
            print(f"\n✅ All required fields present: {required_fields}")
            
        # Check if URL is a valid Stripe checkout URL
        url = data.get("url", "")
        if "checkout.stripe.com" in url:
            print("✅ URL is a valid Stripe checkout URL")
        else:
            print(f"⚠️  URL doesn't appear to be a Stripe checkout URL: {url}")
            
    else:
        print(f"\n❌ FAILED - Status {response.status_code}")
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    main()
# ratios: loc_comments=68:8 imports_exports=4:3 calls_definitions=33:3
