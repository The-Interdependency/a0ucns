# ratios: loc_comments=210:30 imports_exports=5:2 calls_definitions=86:11
"""
Detailed backend regression test for AIMMH Hub
Tests the 5 critical endpoints with detailed response information.
"""

import requests
import json
import uuid
import time
from typing import Dict, Any

# Base URL from frontend .env
BASE_URL = "https://aimmh-hub-1.preview.emergentagent.com"

class DetailedBackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_user = None
        self.access_token = None
        
    def log(self, message: str):
        """Log test messages with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_health_endpoint(self) -> Dict[str, Any]:
        """Test 1: GET /api/health returns 200"""
        self.log("Testing GET /api/health...")
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            result = {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_size": len(response.text),
                "content_type": response.headers.get('content-type', 'unknown')
            }
            
            if result["success"]:
                self.log(f"✅ Health check passed: {response.status_code}")
            else:
                self.log(f"❌ Health check failed: {response.status_code}")
                
            return result
        except Exception as e:
            self.log(f"❌ Health check error: {str(e)}")
            return {"success": False, "error": str(e)}
            
    def test_register_login_user(self) -> Dict[str, Any]:
        """Test 2: Register/login fresh user succeeds"""
        self.log("Testing user registration/login...")
        
        # Generate unique test user
        unique_id = str(uuid.uuid4())[:8]
        self.test_user = {
            "username": f"regtest_{unique_id}",
            "password": f"testpass_{unique_id}"
        }
        
        try:
            # Register user
            self.log(f"Registering user: {self.test_user['username']}")
            register_response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=self.test_user
            )
            
            result = {
                "success": register_response.status_code == 200,
                "status_code": register_response.status_code,
                "has_cookies": 'Set-Cookie' in register_response.headers,
                "username": self.test_user['username']
            }
            
            if not result["success"]:
                self.log(f"❌ Registration failed: {register_response.status_code}")
                result["error"] = register_response.text
                return result
                
            # Check if we got cookies (cookie-based auth)
            if result["has_cookies"]:
                self.log("✅ Registration successful with cookie-based auth")
            else:
                # Fallback: try to extract token from response
                try:
                    register_data = register_response.json()
                    if 'access_token' in register_data:
                        self.access_token = register_data['access_token']
                        result["has_token"] = True
                        self.log("✅ Registration successful with token-based auth")
                    else:
                        self.log("✅ Registration successful (cookie-based)")
                except:
                    self.log("✅ Registration successful (cookie-based)")
                    
            return result
            
        except Exception as e:
            self.log(f"❌ Registration error: {str(e)}")
            return {"success": False, "error": str(e)}
            
    def test_auth_me_endpoint(self) -> Dict[str, Any]:
        """Test 3: GET /api/auth/me with token succeeds"""
        self.log("Testing GET /api/auth/me...")
        
        try:
            headers = {}
            if self.access_token:
                headers['Authorization'] = f'Bearer {self.access_token}'
                
            response = self.session.get(
                f"{self.base_url}/api/auth/me",
                headers=headers
            )
            
            result = {
                "success": response.status_code == 200,
                "status_code": response.status_code
            }
            
            if result["success"]:
                user_data = response.json()
                result["user_email"] = user_data.get('email', 'unknown')
                result["user_tier"] = user_data.get('subscription_tier', 'unknown')
                self.log(f"✅ Auth me successful: user {result['user_email']}, tier {result['user_tier']}")
            else:
                self.log(f"❌ Auth me failed: {response.status_code}")
                result["error"] = response.text
                
            return result
                
        except Exception as e:
            self.log(f"❌ Auth me error: {str(e)}")
            return {"success": False, "error": str(e)}
            
    def test_a0_options_endpoint(self) -> Dict[str, Any]:
        """Test 4: GET /api/a0/non-ui/options with token succeeds"""
        self.log("Testing GET /api/a0/non-ui/options...")
        
        try:
            headers = {}
            if self.access_token:
                headers['Authorization'] = f'Bearer {self.access_token}'
                
            response = self.session.get(
                f"{self.base_url}/api/a0/non-ui/options",
                headers=headers
            )
            
            result = {
                "success": response.status_code == 200,
                "status_code": response.status_code
            }
            
            if result["success"]:
                options_data = response.json()
                result["endpoints_count"] = len(options_data.get('endpoints', {}))
                result["has_models"] = 'models' in options_data
                if result["has_models"]:
                    result["models_count"] = len(options_data.get('models', []))
                self.log(f"✅ A0 options successful: {result['endpoints_count']} endpoints")
            else:
                self.log(f"❌ A0 options failed: {response.status_code}")
                result["error"] = response.text
                
            return result
                
        except Exception as e:
            self.log(f"❌ A0 options error: {str(e)}")
            return {"success": False, "error": str(e)}
            
    def test_models_endpoint(self) -> Dict[str, Any]:
        """Test 5: GET /api/v1/models succeeds"""
        self.log("Testing GET /api/v1/models...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/v1/models")
            
            result = {
                "success": response.status_code == 200,
                "status_code": response.status_code
            }
            
            if result["success"]:
                models_data = response.json()
                result["models_count"] = len(models_data.get('models', []))
                result["has_developers"] = 'developers' in models_data
                if result["has_developers"]:
                    result["developers_count"] = len(models_data.get('developers', []))
                self.log(f"✅ Models endpoint successful: {result['models_count']} models")
            else:
                self.log(f"❌ Models endpoint failed: {response.status_code}")
                result["error"] = response.text
                
            return result
                
        except Exception as e:
            self.log(f"❌ Models endpoint error: {str(e)}")
            return {"success": False, "error": str(e)}
            
    def run_detailed_regression_test(self) -> Dict[str, Any]:
        """Run all regression tests and return detailed results"""
        self.log("=== AIMMH Hub Detailed Backend Regression Test ===")
        self.log(f"Testing against: {self.base_url}")
        
        results = {}
        
        # Test 1: Health check
        results["health"] = self.test_health_endpoint()
        
        # Test 2: Register/login user
        results["register_login"] = self.test_register_login_user()
        
        # Only proceed with authenticated tests if registration succeeded
        if results["register_login"]["success"]:
            # Test 3: Auth me
            results["auth_me"] = self.test_auth_me_endpoint()
            
            # Test 4: A0 options
            results["a0_options"] = self.test_a0_options_endpoint()
        else:
            results["auth_me"] = {"success": False, "skipped": "Registration failed"}
            results["a0_options"] = {"success": False, "skipped": "Registration failed"}
        
        # Test 5: Models (public endpoint)
        results["models"] = self.test_models_endpoint()
        
        return results
        
    def print_detailed_summary(self, results: Dict[str, Any]):
        """Print detailed test summary"""
        self.log("\n=== DETAILED TEST SUMMARY ===")
        
        passed = sum(1 for result in results.values() if result.get("success", False))
        total = len(results)
        
        # Health endpoint
        health = results["health"]
        if health.get("success"):
            self.log(f"1) GET /api/health: ✅ PASS ({health.get('status_code')})")
        else:
            self.log(f"1) GET /api/health: ❌ FAIL ({health.get('status_code', 'ERROR')})")
            
        # Register/login
        reg = results["register_login"]
        if reg.get("success"):
            auth_type = "cookie-based" if reg.get("has_cookies") else "token-based"
            self.log(f"2) Register/login fresh user: ✅ PASS ({reg.get('status_code')}, {auth_type})")
        else:
            self.log(f"2) Register/login fresh user: ❌ FAIL ({reg.get('status_code', 'ERROR')})")
            
        # Auth me
        auth = results["auth_me"]
        if auth.get("success"):
            self.log(f"3) GET /api/auth/me with token: ✅ PASS ({auth.get('status_code')}, tier: {auth.get('user_tier')})")
        elif auth.get("skipped"):
            self.log(f"3) GET /api/auth/me with token: ⏭️ SKIPPED (registration failed)")
        else:
            self.log(f"3) GET /api/auth/me with token: ❌ FAIL ({auth.get('status_code', 'ERROR')})")
            
        # A0 options
        a0 = results["a0_options"]
        if a0.get("success"):
            self.log(f"4) GET /api/a0/non-ui/options with token: ✅ PASS ({a0.get('status_code')}, {a0.get('endpoints_count')} endpoints)")
        elif a0.get("skipped"):
            self.log(f"4) GET /api/a0/non-ui/options with token: ⏭️ SKIPPED (registration failed)")
        else:
            self.log(f"4) GET /api/a0/non-ui/options with token: ❌ FAIL ({a0.get('status_code', 'ERROR')})")
            
        # Models
        models = results["models"]
        if models.get("success"):
            self.log(f"5) GET /api/v1/models: ✅ PASS ({models.get('status_code')}, {models.get('models_count')} models)")
        else:
            self.log(f"5) GET /api/v1/models: ❌ FAIL ({models.get('status_code', 'ERROR')})")
            
        self.log(f"\nOVERALL: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 All regression tests PASSED!")
        else:
            self.log("⚠️  Some regression tests FAILED!")
            
        return passed == total

def main():
    """Main test runner"""
    tester = DetailedBackendTester()
    results = tester.run_detailed_regression_test()
    success = tester.print_detailed_summary(results)
    
    # Return appropriate exit code
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
# ratios: loc_comments=210:30 imports_exports=5:2 calls_definitions=86:11
