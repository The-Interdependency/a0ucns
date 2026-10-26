# ratios: loc_comments=330:43 imports_exports=7:2 calls_definitions=95:12
"""
Service Account Authentication Flow Backend Test

Testing scenarios as per review request:
1) Register normal user and obtain JWT
2) POST /api/auth/service-account/create with JWT should create per-user service account
3) Same create endpoint without auth should return 401
4) POST /api/auth/service-account/token (public) with valid service-account username/password returns long-lived bearer token and expires_at
5) Invalid service-account credentials should return 401
6) Use returned service token on protected endpoints (/api/a0/non-ui/options and /api/conversations/search) and verify success
7) JWT and existing auth flows should remain functional

Target URL: https://aimmh-hub-1.preview.emergentagent.com
"""

import asyncio
import aiohttp
import json
import uuid
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class ServiceAccountAuthTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.jwt_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.service_account_username: Optional[str] = None
        self.service_account_token: Optional[str] = None
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "details": []
        }

    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results"""
        self.results["total_tests"] += 1
        if status == "PASS":
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
        
        self.results["details"].append({
            "test": test_name,
            "status": status,
            "details": details
        })
        print(f"[{status}] {test_name}: {details}")

    async def test_1_register_user_obtain_jwt(self, session: aiohttp.ClientSession) -> bool:
        """Test 1: Register normal user and obtain JWT"""
        try:
            # Generate unique test user
            timestamp = int(time.time())
            username = f"satest_{timestamp}"
            password = "ServiceTest123!"
            
            payload = {
                "username": username,
                "password": password
            }
            
            headers = {"Content-Type": "application/json"}
            async with session.post(f"{self.base_url}/api/auth/register", 
                                  headers=headers, json=payload) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify response structure
                    if "access_token" in data and "user" in data:
                        self.jwt_token = data["access_token"]
                        self.user_id = data["user"]["id"]
                        self.log_test("Register User & JWT", "PASS", 
                                    f"User {username} registered, JWT obtained")
                        return True
                    else:
                        self.log_test("Register User & JWT", "FAIL", 
                                    f"Invalid response structure: {data}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Register User & JWT", "FAIL", 
                                f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Register User & JWT", "FAIL", f"Exception: {str(e)}")
            return False

    async def test_2_create_service_account_with_jwt(self, session: aiohttp.ClientSession) -> bool:
        """Test 2: POST /api/auth/service-account/create with JWT should create per-user service account"""
        try:
            # Generate unique service account
            timestamp = int(time.time())
            self.service_account_username = f"sa_test_{timestamp}"
            service_password = "SAPassword123!"
            
            payload = {
                "username": self.service_account_username,
                "password": service_password,
                "label": "Test Service Account for Auth Flow"
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jwt_token}"
            }
            
            async with session.post(f"{self.base_url}/api/auth/service-account/create",
                                  headers=headers, json=payload) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify response structure
                    required_fields = ["id", "username", "owner_user_id", "active", "created_at"]
                    if all(field in data for field in required_fields):
                        if data["username"] == self.service_account_username and data["owner_user_id"] == self.user_id:
                            # Store password for later token testing
                            self.service_account_password = service_password
                            self.log_test("Create Service Account (JWT Auth)", "PASS",
                                        f"Service account {self.service_account_username} created for user {self.user_id}")
                            return True
                        else:
                            self.log_test("Create Service Account (JWT Auth)", "FAIL",
                                        f"Username/owner mismatch: expected {self.service_account_username}/{self.user_id}, got {data['username']}/{data['owner_user_id']}")
                            return False
                    else:
                        missing_fields = set(required_fields) - set(data.keys())
                        self.log_test("Create Service Account (JWT Auth)", "FAIL",
                                    f"Missing fields: {missing_fields}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Create Service Account (JWT Auth)", "FAIL",
                                f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Create Service Account (JWT Auth)", "FAIL", f"Exception: {str(e)}")
            return False

    async def test_3_create_service_account_without_auth(self, session: aiohttp.ClientSession) -> bool:
        """Test 3: Same create endpoint without auth should return 401"""
        try:
            payload = {
                "username": f"unauthorized_sa_{int(time.time())}",
                "password": "UnauthorizedPass123!"
            }
            
            headers = {"Content-Type": "application/json"}
            # No Authorization header - should fail
            
            async with session.post(f"{self.base_url}/api/auth/service-account/create",
                                  headers=headers, json=payload) as response:
                
                if response.status == 401:
                    self.log_test("Service Account Create (No Auth)", "PASS",
                                "Correctly returns 401 Unauthorized")
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("Service Account Create (No Auth)", "FAIL",
                                f"Expected 401, got HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Service Account Create (No Auth)", "FAIL", f"Exception: {str(e)}")
            return False

    async def test_4_service_account_token_valid_creds(self, session: aiohttp.ClientSession) -> bool:
        """Test 4: POST /api/auth/service-account/token with valid credentials returns token and expires_at"""
        try:
            payload = {
                "username": self.service_account_username,
                "password": self.service_account_password,
                "expires_in_days": 30
            }
            
            headers = {"Content-Type": "application/json"}
            
            async with session.post(f"{self.base_url}/api/auth/service-account/token",
                                  headers=headers, json=payload) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify response structure
                    required_fields = ["access_token", "token_type", "expires_at", "service_account_username"]
                    if all(field in data for field in required_fields):
                        # Verify token format and values
                        if (data["access_token"].startswith("sat_") and 
                            data["token_type"] == "bearer" and
                            data["service_account_username"] == self.service_account_username):
                            
                            # Store token for protected endpoint testing
                            self.service_account_token = data["access_token"]
                            
                            # Verify expires_at is in future
                            expires_at = datetime.fromisoformat(data["expires_at"].replace('Z', '+00:00'))
                            now = datetime.now(timezone.utc)
                            if expires_at > now:
                                self.log_test("Service Account Token (Valid Creds)", "PASS",
                                            f"Token issued successfully, expires {expires_at}")
                                return True
                            else:
                                self.log_test("Service Account Token (Valid Creds)", "FAIL",
                                            f"Token expires in past: {expires_at}")
                                return False
                        else:
                            self.log_test("Service Account Token (Valid Creds)", "FAIL",
                                        f"Invalid token format or values: {data}")
                            return False
                    else:
                        missing_fields = set(required_fields) - set(data.keys())
                        self.log_test("Service Account Token (Valid Creds)", "FAIL",
                                    f"Missing fields: {missing_fields}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Service Account Token (Valid Creds)", "FAIL",
                                f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Service Account Token (Valid Creds)", "FAIL", f"Exception: {str(e)}")
            return False

    async def test_5_service_account_token_invalid_creds(self, session: aiohttp.ClientSession) -> bool:
        """Test 5: Invalid service-account credentials should return 401"""
        try:
            # Test with wrong password
            payload = {
                "username": self.service_account_username,
                "password": "WrongPassword123!",
                "expires_in_days": 30
            }
            
            headers = {"Content-Type": "application/json"}
            
            async with session.post(f"{self.base_url}/api/auth/service-account/token",
                                  headers=headers, json=payload) as response:
                
                if response.status == 401:
                    wrong_pass_result = "PASS"
                else:
                    wrong_pass_result = f"FAIL (got {response.status})"
            
            # Test with non-existent username
            payload["username"] = f"nonexistent_sa_{int(time.time())}"
            payload["password"] = "AnyPassword123!"
            
            async with session.post(f"{self.base_url}/api/auth/service-account/token",
                                  headers=headers, json=payload) as response:
                
                if response.status == 401:
                    wrong_user_result = "PASS"
                else:
                    wrong_user_result = f"FAIL (got {response.status})"
            
            if wrong_pass_result == "PASS" and wrong_user_result == "PASS":
                self.log_test("Service Account Token (Invalid Creds)", "PASS",
                            "Both wrong password and wrong username return 401")
                return True
            else:
                self.log_test("Service Account Token (Invalid Creds)", "FAIL",
                            f"Wrong password: {wrong_pass_result}, Wrong username: {wrong_user_result}")
                return False
                    
        except Exception as e:
            self.log_test("Service Account Token (Invalid Creds)", "FAIL", f"Exception: {str(e)}")
            return False

    async def test_6_protected_endpoints_with_service_token(self, session: aiohttp.ClientSession) -> bool:
        """Test 6: Use service token on protected endpoints and verify success"""
        try:
            headers = {
                "Authorization": f"Bearer {self.service_account_token}",
                "Content-Type": "application/json"
            }
            
            success_count = 0
            total_endpoints = 2
            
            # Test 6a: /api/a0/non-ui/options
            async with session.get(f"{self.base_url}/api/a0/non-ui/options", 
                                 headers=headers) as response:
                
                if response.status == 200:
                    data = await response.json()
                    required_keys = ["input_options", "output_options", "available_models", "non_ui_endpoints"]
                    
                    if all(key in data for key in required_keys):
                        success_count += 1
                        print(f"  ✅ /api/a0/non-ui/options: Success (200 OK)")
                    else:
                        print(f"  ❌ /api/a0/non-ui/options: Invalid response structure")
                else:
                    print(f"  ❌ /api/a0/non-ui/options: HTTP {response.status}")
            
            # Test 6b: /api/conversations/search
            async with session.get(f"{self.base_url}/api/conversations/search?q=test&offset=0&limit=10", 
                                 headers=headers) as response:
                
                if response.status == 200:
                    data = await response.json()
                    required_fields = ["query", "offset", "limit", "total", "conversations"]
                    
                    if all(field in data for field in required_fields):
                        success_count += 1
                        print(f"  ✅ /api/conversations/search: Success (200 OK)")
                    else:
                        print(f"  ❌ /api/conversations/search: Invalid response structure")
                else:
                    print(f"  ❌ /api/conversations/search: HTTP {response.status}")
            
            if success_count == total_endpoints:
                self.log_test("Protected Endpoints (Service Token)", "PASS",
                            f"All {total_endpoints} protected endpoints work with service token")
                return True
            else:
                self.log_test("Protected Endpoints (Service Token)", "FAIL",
                            f"Only {success_count}/{total_endpoints} endpoints worked")
                return False
                    
        except Exception as e:
            self.log_test("Protected Endpoints (Service Token)", "FAIL", f"Exception: {str(e)}")
            return False

    async def test_7_jwt_auth_flows_still_functional(self, session: aiohttp.ClientSession) -> bool:
        """Test 7: JWT and existing auth flows should remain functional"""
        try:
            headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "Content-Type": "application/json"
            }
            
            success_count = 0
            total_checks = 3
            
            # Test 7a: /api/auth/me with JWT
            async with session.get(f"{self.base_url}/api/auth/me", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if "user_id" in data or "email" in data:
                        success_count += 1
                        print(f"  ✅ /api/auth/me with JWT: Success")
                    else:
                        print(f"  ❌ /api/auth/me with JWT: Invalid response")
                else:
                    print(f"  ❌ /api/auth/me with JWT: HTTP {response.status}")
            
            # Test 7b: /api/conversations/search with JWT
            async with session.get(f"{self.base_url}/api/conversations/search", headers=headers) as response:
                if response.status == 200:
                    success_count += 1
                    print(f"  ✅ /api/conversations/search with JWT: Success")
                else:
                    print(f"  ❌ /api/conversations/search with JWT: HTTP {response.status}")
            
            # Test 7c: /api/a0/non-ui/options with JWT
            async with session.get(f"{self.base_url}/api/a0/non-ui/options", headers=headers) as response:
                if response.status == 200:
                    success_count += 1
                    print(f"  ✅ /api/a0/non-ui/options with JWT: Success")
                else:
                    print(f"  ❌ /api/a0/non-ui/options with JWT: HTTP {response.status}")
            
            if success_count == total_checks:
                self.log_test("JWT Auth Flows Still Functional", "PASS",
                            f"All {total_checks} JWT auth checks passed")
                return True
            else:
                self.log_test("JWT Auth Flows Still Functional", "FAIL",
                            f"Only {success_count}/{total_checks} JWT auth checks passed")
                return False
                    
        except Exception as e:
            self.log_test("JWT Auth Flows Still Functional", "FAIL", f"Exception: {str(e)}")
            return False

    async def run_service_account_auth_tests(self) -> bool:
        """Run all service account authentication tests"""
        print("🚀 SERVICE ACCOUNT AUTHENTICATION BACKEND VALIDATION")
        print("=" * 80)
        print(f"Target: {self.base_url}")
        print()
        
        success = True
        
        # Run tests with aiohttp session
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            
            # Define test sequence
            tests = [
                ("1. Register User & Obtain JWT", self.test_1_register_user_obtain_jwt),
                ("2. Create Service Account (JWT Auth)", self.test_2_create_service_account_with_jwt),
                ("3. Create Service Account (No Auth)", self.test_3_create_service_account_without_auth),
                ("4. Service Account Token (Valid Creds)", self.test_4_service_account_token_valid_creds),
                ("5. Service Account Token (Invalid Creds)", self.test_5_service_account_token_invalid_creds),
                ("6. Protected Endpoints (Service Token)", self.test_6_protected_endpoints_with_service_token),
                ("7. JWT Auth Flows Still Functional", self.test_7_jwt_auth_flows_still_functional)
            ]
            
            for test_name, test_func in tests:
                print(f"\n🧪 Running: {test_name}")
                if not await test_func(session):
                    success = False
                    # Continue with other tests to get full picture
        
        # Print final results
        print("\n" + "=" * 80)
        print("📊 SERVICE ACCOUNT AUTH TEST RESULTS")
        print("=" * 80)
        
        for result in self.results["details"]:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {result['test']}: {result['details']}")
        
        print(f"\n📈 Summary: {self.results['passed']}/{self.results['total_tests']} tests passed")
        
        if success and self.results["passed"] == self.results["total_tests"]:
            print("🎉 ALL SERVICE ACCOUNT AUTH TESTS PASSED!")
            return True
        else:
            print("💥 SOME SERVICE ACCOUNT AUTH TESTS FAILED!")
            return False


async def main():
    """Main test runner"""
    BASE_URL = "https://aimmh-hub-1.preview.emergentagent.com"
    
    tester = ServiceAccountAuthTester(BASE_URL)
    success = await tester.run_service_account_auth_tests()
    
    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
# ratios: loc_comments=330:43 imports_exports=7:2 calls_definitions=95:12
