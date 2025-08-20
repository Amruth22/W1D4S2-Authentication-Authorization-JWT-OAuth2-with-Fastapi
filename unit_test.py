"""
Comprehensive Unit Tests for Simple Blog API with JWT Authentication
Tests all API endpoints, security features, and edge cases
"""

import unittest
import requests
import json
import time
from typing import Optional

class BlogAPITestCase(unittest.TestCase):
    """Unit tests for the Simple Blog API"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test configuration - runs once before all tests"""
        cls.base_url = "http://localhost:8000"
        cls.author_token = None
        cls.reader_token = None
        cls.test_post_id = None
        
        # Test data
        cls.author_data = {
            "username": "test_author",
            "password": "secure123",
            "role": "author"
        }
        
        cls.reader_data = {
            "username": "test_reader", 
            "password": "secure456",
            "role": "reader"
        }
        
        cls.post_data = {
            "title": "Test Blog Post",
            "content": "This is a test blog post content for unit testing."
        }
        
        cls.updated_post_data = {
            "title": "Updated Test Blog Post",
            "content": "This is updated content for the test blog post."
        }
        
        print(f"\n🚀 Starting Blog API Unit Tests")
        print(f"📍 Testing API at: {cls.base_url}")
        
    def setUp(self):
        """Set up before each test method"""
        pass
        
    def tearDown(self):
        """Clean up after each test method"""
        pass
    
    def make_request(self, method: str, endpoint: str, data: dict = None, headers: dict = None) -> requests.Response:
        """Helper method to make HTTP requests"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                return requests.get(url, headers=headers)
            elif method.upper() == "POST":
                return requests.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                return requests.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                return requests.delete(url, headers=headers)
        except requests.exceptions.ConnectionError:
            self.fail("Could not connect to API server. Make sure it's running on http://localhost:8000")
    
    def get_auth_headers(self, token: str) -> dict:
        """Helper method to create authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    # Test 1: User Registration and Login
    def test_01_user_registration_and_login(self):
        """Test complete authentication flow: registration and login"""
        print("\n1️⃣ Testing user registration and login...")
        
        # Register author
        response = self.make_request("POST", "/register", self.author_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())
        self.assertIn("author", response.json()["message"])
        print(f"   ✅ Author registration: {response.status_code} - {response.json()}")
        
        # Register reader
        response = self.make_request("POST", "/register", self.reader_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())
        self.assertIn("reader", response.json()["message"])
        print(f"   ✅ Reader registration: {response.status_code} - {response.json()}")
        
        # Login author
        login_data = {
            "username": self.author_data["username"],
            "password": self.author_data["password"]
        }
        
        response = self.make_request("POST", "/login", login_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())
        self.assertIn("token_type", response.json())
        self.assertEqual(response.json()["token_type"], "bearer")
        
        # Store token for future tests
        BlogAPITestCase.author_token = response.json()["access_token"]
        print(f"   ✅ Author login successful! Token: {self.author_token[:50]}...")
        
        # Login reader
        login_data = {
            "username": self.reader_data["username"],
            "password": self.reader_data["password"]
        }
        
        response = self.make_request("POST", "/login", login_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())
        
        # Store token for future tests
        BlogAPITestCase.reader_token = response.json()["access_token"]
        print(f"   ✅ Reader login successful! Token: {self.reader_token[:50]}...")
    
    # Test 2: Invalid Login and Rate Limiting
    def test_02_invalid_login_and_rate_limiting(self):
        """Test login security: invalid credentials and rate limiting"""
        print("\n2️⃣ Testing login security...")
        
        # Test invalid login
        invalid_login = {
            "username": self.author_data["username"],
            "password": "wrong_password"
        }
        
        response = self.make_request("POST", "/login", invalid_login)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid username or password", response.json()["detail"])
        print(f"   ✅ Invalid login blocked: {response.status_code} - {response.json()}")
        
        # Test rate limiting
        rate_limit_user = {
            "username": "rate_limit_test",
            "password": "password123",
            "role": "reader"
        }
        
        # Register user for rate limit testing
        self.make_request("POST", "/register", rate_limit_user)
        
        # Make multiple failed login attempts
        bad_login = {
            "username": "rate_limit_test",
            "password": "wrong_password"
        }
        
        rate_limited = False
        for i in range(6):  # Try 6 times (limit is 5)
            response = self.make_request("POST", "/login", bad_login)
            print(f"   Attempt {i+1}: {response.status_code}")
            
            if response.status_code == 429:
                self.assertIn("Too many login attempts", response.json()["detail"])
                rate_limited = True
                print("   ✅ Rate limiting working! Too many attempts blocked.")
                break
        
        self.assertTrue(rate_limited, "Rate limiting should have been triggered")
    
    # Test 3: Authentication Required
    def test_03_authentication_required(self):
        """Test that authentication is required for protected endpoints"""
        print("\n3️⃣ Testing authentication requirements...")
        
        # Try accessing posts without token
        response = self.make_request("GET", "/posts")
        self.assertEqual(response.status_code, 403)
        print(f"   ✅ No token blocked: {response.status_code}")
        
        # Try with invalid token
        bad_headers = {"Authorization": "Bearer invalid_token"}
        response = self.make_request("GET", "/posts", headers=bad_headers)
        self.assertEqual(response.status_code, 401)
        print(f"   ✅ Invalid token blocked: {response.status_code}")
    
    # Test 4: Create Blog Posts (Role-based Access)
    def test_04_create_blog_posts(self):
        """Test blog post creation with role-based access control"""
        print("\n4️⃣ Testing blog post creation...")
        
        # Author creating post (should succeed)
        headers = self.get_auth_headers(self.author_token)
        response = self.make_request("POST", "/posts", self.post_data, headers)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("message", response_data)
        self.assertIn("post_id", response_data)
        self.assertEqual(response_data["title"], self.post_data["title"])
        
        # Store post ID for future tests
        BlogAPITestCase.test_post_id = response_data["post_id"]
        print(f"   ✅ Author created post: {response.status_code} - {response_data}")
        
        # Reader trying to create post (should fail)
        headers = self.get_auth_headers(self.reader_token)
        response = self.make_request("POST", "/posts", self.post_data, headers)
        
        self.assertEqual(response.status_code, 403)
        self.assertIn("Only authors can perform this action", response.json()["detail"])
        print(f"   ✅ Reader blocked from creating post: {response.status_code} - {response.json()}")
    
    # Test 5: View Blog Posts
    def test_05_view_blog_posts(self):
        """Test viewing blog posts (accessible to all authenticated users)"""
        print("\n5️⃣ Testing blog post viewing...")
        
        # Author viewing posts
        headers = self.get_auth_headers(self.author_token)
        response = self.make_request("GET", "/posts", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        posts = response.json()
        self.assertIsInstance(posts, list)
        self.assertGreater(len(posts), 0)
        
        # Check post structure
        post = posts[0]
        self.assertIn("post_id", post)
        self.assertIn("title", post)
        self.assertIn("content", post)
        self.assertIn("author", post)
        self.assertIn("created_at", post)
        
        print(f"   ✅ Author can see {len(posts)} posts")
        for p in posts:
            print(f"      - Post {p['post_id']}: '{p['title']}' by {p['author']}")
        
        # Reader viewing posts
        headers = self.get_auth_headers(self.reader_token)
        response = self.make_request("GET", "/posts", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        posts = response.json()
        self.assertIsInstance(posts, list)
        print(f"   ✅ Reader can see {len(posts)} posts")
    
    # Test 6: Update Blog Posts (Ownership Validation)
    def test_06_update_blog_posts(self):
        """Test blog post updating with ownership validation"""
        print("\n6️⃣ Testing blog post updating...")
        
        if self.test_post_id is None:
            self.fail("No test post ID available. Post creation test may have failed.")
        
        # Author updating own post (should succeed)
        headers = self.get_auth_headers(self.author_token)
        response = self.make_request("PUT", f"/posts/{self.test_post_id}", self.updated_post_data, headers)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("message", response_data)
        self.assertEqual(response_data["post_id"], self.test_post_id)
        print(f"   ✅ Author updated own post: {response.status_code} - {response_data}")
        
        # Reader trying to update post (should fail)
        headers = self.get_auth_headers(self.reader_token)
        response = self.make_request("PUT", f"/posts/{self.test_post_id}", self.updated_post_data, headers)
        
        self.assertEqual(response.status_code, 403)
        self.assertIn("Only authors can perform this action", response.json()["detail"])
        print(f"   ✅ Reader blocked from updating post: {response.status_code} - {response.json()}")
    
    # Test 7: Delete Blog Posts (Ownership Validation)
    def test_07_delete_blog_posts(self):
        """Test blog post deletion with ownership validation"""
        print("\n7️⃣ Testing blog post deletion...")
        
        if self.test_post_id is None:
            self.fail("No test post ID available. Post creation test may have failed.")
        
        # Reader trying to delete post (should fail)
        headers = self.get_auth_headers(self.reader_token)
        response = self.make_request("DELETE", f"/posts/{self.test_post_id}", headers=headers)
        
        self.assertEqual(response.status_code, 403)
        self.assertIn("Only authors can perform this action", response.json()["detail"])
        print(f"   ✅ Reader blocked from deleting post: {response.status_code} - {response.json()}")
        
        # Author deleting own post (should succeed)
        headers = self.get_auth_headers(self.author_token)
        response = self.make_request("DELETE", f"/posts/{self.test_post_id}", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("message", response_data)
        self.assertEqual(response_data["post_id"], self.test_post_id)
        print(f"   ✅ Author deleted own post: {response.status_code} - {response_data}")
    
    # Test 8: Post Ownership Between Authors
    def test_08_post_ownership_validation(self):
        """Test that authors can only modify their own posts"""
        print("\n8️⃣ Testing post ownership validation...")
        
        # Register second author
        second_author = {
            "username": "second_author",
            "password": "secure789",
            "role": "author"
        }
        
        response = self.make_request("POST", "/register", second_author)
        self.assertEqual(response.status_code, 200)
        
        # Login second author
        login_data = {
            "username": "second_author",
            "password": "secure789"
        }
        
        response = self.make_request("POST", "/login", login_data)
        self.assertEqual(response.status_code, 200)
        second_author_token = response.json()["access_token"]
        
        # First author creates a post
        headers = self.get_auth_headers(self.author_token)
        post_data = {
            "title": "First Author's Post",
            "content": "This post belongs to the first author."
        }
        
        response = self.make_request("POST", "/posts", post_data, headers)
        self.assertEqual(response.status_code, 200)
        first_author_post_id = response.json()["post_id"]
        
        # Second author tries to update first author's post (should fail)
        headers = self.get_auth_headers(second_author_token)
        update_data = {"title": "Hacked Title"}
        
        response = self.make_request("PUT", f"/posts/{first_author_post_id}", update_data, headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("You can only update your own posts", response.json()["detail"])
        print(f"   ✅ Second author blocked from updating first author's post: {response.status_code}")
        
        # Second author tries to delete first author's post (should fail)
        response = self.make_request("DELETE", f"/posts/{first_author_post_id}", headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("You can only delete your own posts", response.json()["detail"])
        print(f"   ✅ Second author blocked from deleting first author's post: {response.status_code}")
    
    # Test 9: User Info and Basic Validation
    def test_09_user_info_and_validation(self):
        """Test user information retrieval and basic validation"""
        print("\n9️⃣ Testing user info and validation...")
        
        # Get author info
        headers = self.get_auth_headers(self.author_token)
        response = self.make_request("GET", "/me", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        user_info = response.json()
        self.assertEqual(user_info["username"], self.author_data["username"])
        self.assertEqual(user_info["role"], "author")
        self.assertIn("user_id", user_info)
        print(f"   ✅ Author info: {user_info}")
        
        # Get reader info
        headers = self.get_auth_headers(self.reader_token)
        response = self.make_request("GET", "/me", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        user_info = response.json()
        self.assertEqual(user_info["username"], self.reader_data["username"])
        self.assertEqual(user_info["role"], "reader")
        print(f"   ✅ Reader info: {user_info}")
        
        # Test with malformed token
        bad_headers = {"Authorization": "Bearer malformed.token.here"}
        response = self.make_request("GET", "/me", headers=bad_headers)
        
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid authentication credentials", response.json()["detail"])
        print(f"   ✅ Malformed token rejected: {response.status_code}")

def run_tests():
    """Run all unit tests"""
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(BlogAPITestCase)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=None)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print(f"\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if not result.failures and not result.errors:
        print(f"\n🎉 ALL TESTS PASSED! 🎉")
    
    print(f"{'='*60}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("🧪 Blog API Unit Test Suite")
    print("=" * 60)
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("Run: python main.py")
    print("=" * 60)
    
    try:
        success = run_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        exit(1)