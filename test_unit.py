import unittest
import os
import sys
import tempfile
import shutil
import asyncio
import time
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Add the current directory to Python path to import project modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

class CoreJWTAuthTests(unittest.TestCase):
    """Core 5 unit tests for JWT Authentication & Authorization Implementation with real components"""
    
    @classmethod
    def setUpClass(cls):
        """Load configuration and validate setup"""
        # Note: This system doesn't require external APIs - it's a local JWT auth system
        print("Setting up JWT Authentication System tests...")
        
        # Initialize JWT Auth components (classes only, no heavy initialization)
        try:
            # Import main application components
            from main import app, users_db, posts_db, login_attempts
            from main import (
                hash_password, verify_password, create_access_token,
                check_rate_limit, increment_login_attempts, get_current_user,
                require_author_role
            )
            
            # Import Pydantic models
            from main import UserRegister, UserLogin, BlogPost, BlogPostUpdate, Token, User
            
            # Import FastAPI testing client
            from fastapi.testclient import TestClient
            
            cls.app = app
            cls.client = TestClient(app)
            cls.users_db = users_db
            cls.posts_db = posts_db
            cls.login_attempts = login_attempts
            
            # Store utility functions
            cls.hash_password = hash_password
            cls.verify_password = verify_password
            cls.create_access_token = create_access_token
            cls.check_rate_limit = check_rate_limit
            cls.increment_login_attempts = increment_login_attempts
            cls.get_current_user = get_current_user
            cls.require_author_role = require_author_role
            
            # Store models
            cls.UserRegister = UserRegister
            cls.UserLogin = UserLogin
            cls.BlogPost = BlogPost
            cls.BlogPostUpdate = BlogPostUpdate
            cls.Token = Token
            cls.User = User
            
            print("JWT authentication components loaded successfully")
        except ImportError as e:
            raise unittest.SkipTest(f"Required JWT authentication components not found: {e}")

    def setUp(self):
        """Set up test fixtures"""
        # Clear databases before each test
        self.users_db.clear()
        self.posts_db.clear()
        self.login_attempts.clear()
        
        # Reset counters
        import main
        main.user_counter = 1
        main.post_counter = 1
        
        # Test data
        self.test_author = {
            "username": "test_author",
            "password": "secure123",
            "role": "author"
        }
        
        self.test_reader = {
            "username": "test_reader",
            "password": "secure456", 
            "role": "reader"
        }
        
        self.test_post = {
            "title": "Test Blog Post",
            "content": "This is a test blog post content."
        }

    def tearDown(self):
        """Clean up test fixtures"""
        # Clear databases after each test
        self.users_db.clear()
        self.posts_db.clear()
        self.login_attempts.clear()

    def test_01_jwt_authentication_setup(self):
        """Test 1: JWT Authentication Setup and Configuration"""
        print("Running Test 1: JWT Authentication Setup")
        
        # Test FastAPI app initialization
        self.assertIsNotNone(self.app)
        self.assertEqual(self.app.title, "Simple Blog API")
        
        # Test utility functions exist
        self.assertTrue(callable(self.hash_password))
        self.assertTrue(callable(self.verify_password))
        self.assertTrue(callable(self.create_access_token))
        self.assertTrue(callable(self.check_rate_limit))
        self.assertTrue(callable(self.increment_login_attempts))
        
        # Import functions directly for testing
        from main import hash_password, verify_password, create_access_token, check_rate_limit, increment_login_attempts
        
        # Test password hashing functionality
        test_password = "test_password_123"
        hashed = hash_password(test_password)
        self.assertIsInstance(hashed, str)
        self.assertNotEqual(hashed, test_password)
        self.assertGreater(len(hashed), 50)  # bcrypt hashes are long
        
        # Test password verification
        self.assertTrue(verify_password(test_password, hashed))
        self.assertFalse(verify_password("wrong_password", hashed))
        
        # Test JWT token creation
        test_data = {"sub": "test_user"}
        token = create_access_token(test_data)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 100)  # JWT tokens are long
        
        # Test token contains expected parts (header.payload.signature)
        token_parts = token.split('.')
        self.assertEqual(len(token_parts), 3)
        
        # Test rate limiting functions
        self.assertTrue(check_rate_limit("new_user"))
        increment_login_attempts("test_user")
        self.assertIn("test_user", self.login_attempts)
        
        print("PASS: FastAPI application initialized")
        print("PASS: Password hashing and verification working")
        print("PASS: JWT token creation working")
        print("PASS: Rate limiting functions working")
        print("PASS: JWT authentication setup validated")

    def test_02_user_registration_operations(self):
        """Test 2: User Registration and Validation"""
        print("Running Test 2: User Registration Operations")
        
        # Test Pydantic models
        author_model = self.UserRegister(**self.test_author)
        self.assertEqual(author_model.username, "test_author")
        self.assertEqual(author_model.password, "secure123")
        self.assertEqual(author_model.role, "author")
        
        reader_model = self.UserRegister(**self.test_reader)
        self.assertEqual(reader_model.role, "reader")
        
        # Test successful author registration
        response = self.client.post("/register", json=self.test_author)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("message", response_data)
        self.assertIn("test_author", response_data["message"])
        self.assertIn("author", response_data["message"])
        
        # Verify user was stored in database
        self.assertIn("test_author", self.users_db)
        stored_user = self.users_db["test_author"]
        self.assertEqual(stored_user["role"], "author")
        self.assertIn("password_hash", stored_user)
        self.assertIn("user_id", stored_user)
        self.assertNotEqual(stored_user["password_hash"], "secure123")  # Should be hashed
        
        # Test successful reader registration
        response = self.client.post("/register", json=self.test_reader)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("reader", response_data["message"])
        
        # Test duplicate username registration (should fail)
        response = self.client.post("/register", json=self.test_author)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Username already registered", response.json()["detail"])
        
        # Test invalid role registration (should fail)
        invalid_user = {
            "username": "invalid_user",
            "password": "password123",
            "role": "invalid_role"
        }
        response = self.client.post("/register", json=invalid_user)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Role must be either 'reader' or 'author'", response.json()["detail"])
        
        print(f"PASS: User registration - {len(self.users_db)} users registered")
        print("PASS: Password hashing during registration")
        print("PASS: Duplicate username validation")
        print("PASS: Role validation")
        print("PASS: User registration operations validated")

    def test_03_jwt_login_operations(self):
        """Test 3: JWT Login and Token Generation"""
        print("Running Test 3: JWT Login Operations")
        
        # First register a user
        self.client.post("/register", json=self.test_author)
        
        # Test successful login
        login_data = {
            "username": self.test_author["username"],
            "password": self.test_author["password"]
        }
        response = self.client.post("/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertIn("access_token", response_data)
        self.assertIn("token_type", response_data)
        self.assertEqual(response_data["token_type"], "bearer")
        
        # Validate token structure
        token = response_data["access_token"]
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 100)
        token_parts = token.split('.')
        self.assertEqual(len(token_parts), 3)
        
        # Test invalid username login
        invalid_login = {
            "username": "nonexistent_user",
            "password": "password123"
        }
        response = self.client.post("/login", json=invalid_login)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid username or password", response.json()["detail"])
        
        # Test invalid password login
        invalid_password = {
            "username": self.test_author["username"],
            "password": "wrong_password"
        }
        response = self.client.post("/login", json=invalid_password)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid username or password", response.json()["detail"])
        
        # Test rate limiting
        rate_limit_user = {
            "username": "rate_test_user",
            "password": "password123",
            "role": "reader"
        }
        self.client.post("/register", json=rate_limit_user)
        
        # Make multiple failed login attempts
        bad_login = {
            "username": "rate_test_user",
            "password": "wrong_password"
        }
        
        rate_limited = False
        for i in range(6):  # Try 6 times (limit is 5)
            response = self.client.post("/login", json=bad_login)
            if response.status_code == 429:
                self.assertIn("Too many login attempts", response.json()["detail"])
                rate_limited = True
                break
        
        self.assertTrue(rate_limited, "Rate limiting should have been triggered")
        
        print("PASS: Successful JWT token generation")
        print("PASS: Invalid login attempts blocked")
        print("PASS: Rate limiting working")
        print("PASS: JWT login operations validated")

    def test_04_role_based_authorization(self):
        """Test 4: Role-based Authorization and Access Control"""
        print("Running Test 4: Role-based Authorization")
        
        # Register and login both author and reader
        self.client.post("/register", json=self.test_author)
        self.client.post("/register", json=self.test_reader)
        
        # Get tokens
        author_login = {"username": "test_author", "password": "secure123"}
        reader_login = {"username": "test_reader", "password": "secure456"}
        
        author_response = self.client.post("/login", json=author_login)
        reader_response = self.client.post("/login", json=reader_login)
        
        author_token = author_response.json()["access_token"]
        reader_token = reader_response.json()["access_token"]
        
        author_headers = {"Authorization": f"Bearer {author_token}"}
        reader_headers = {"Authorization": f"Bearer {reader_token}"}
        
        # Test authentication required for protected endpoints
        response = self.client.get("/posts")
        self.assertEqual(response.status_code, 403)  # No token
        
        response = self.client.get("/posts", headers={"Authorization": "Bearer invalid_token"})
        self.assertEqual(response.status_code, 401)  # Invalid token
        
        # Test both roles can view posts
        response = self.client.get("/posts", headers=author_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        
        response = self.client.get("/posts", headers=reader_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        
        # Test only authors can create posts
        response = self.client.post("/posts", json=self.test_post, headers=author_headers)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("post_id", response_data)
        post_id = response_data["post_id"]
        
        # Reader trying to create post should fail
        response = self.client.post("/posts", json=self.test_post, headers=reader_headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("Only authors can perform this action", response.json()["detail"])
        
        # Test only authors can update posts (and only their own)
        update_data = {"title": "Updated Title"}
        response = self.client.put(f"/posts/{post_id}", json=update_data, headers=author_headers)
        self.assertEqual(response.status_code, 200)
        
        # Reader trying to update should fail
        response = self.client.put(f"/posts/{post_id}", json=update_data, headers=reader_headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("Only authors can perform this action", response.json()["detail"])
        
        # Test only authors can delete posts (and only their own)
        response = self.client.delete(f"/posts/{post_id}", headers=author_headers)
        self.assertEqual(response.status_code, 200)
        
        # Test user info endpoint
        response = self.client.get("/me", headers=author_headers)
        self.assertEqual(response.status_code, 200)
        user_info = response.json()
        self.assertEqual(user_info["username"], "test_author")
        self.assertEqual(user_info["role"], "author")
        self.assertIn("user_id", user_info)
        
        response = self.client.get("/me", headers=reader_headers)
        self.assertEqual(response.status_code, 200)
        user_info = response.json()
        self.assertEqual(user_info["role"], "reader")
        
        print("PASS: Authentication required for protected endpoints")
        print("PASS: Both roles can view posts")
        print("PASS: Only authors can create posts")
        print("PASS: Only authors can update/delete posts")
        print("PASS: User info endpoint working")
        print("PASS: Role-based authorization validated")

    def test_05_blog_post_ownership_validation(self):
        """Test 5: Blog Post Ownership and Complete CRUD Operations"""
        print("Running Test 5: Blog Post Ownership Validation")
        
        # Register two authors
        author1 = {"username": "author1", "password": "pass123", "role": "author"}
        author2 = {"username": "author2", "password": "pass456", "role": "author"}
        
        self.client.post("/register", json=author1)
        self.client.post("/register", json=author2)
        
        # Login both authors
        author1_response = self.client.post("/login", json={"username": "author1", "password": "pass123"})
        author2_response = self.client.post("/login", json={"username": "author2", "password": "pass456"})
        
        author1_token = author1_response.json()["access_token"]
        author2_token = author2_response.json()["access_token"]
        
        author1_headers = {"Authorization": f"Bearer {author1_token}"}
        author2_headers = {"Authorization": f"Bearer {author2_token}"}
        
        # Author1 creates a post
        post1_data = {"title": "Author1's Post", "content": "Content by author1"}
        response = self.client.post("/posts", json=post1_data, headers=author1_headers)
        self.assertEqual(response.status_code, 200)
        post1_id = response.json()["post_id"]
        
        # Author2 creates a post
        post2_data = {"title": "Author2's Post", "content": "Content by author2"}
        response = self.client.post("/posts", json=post2_data, headers=author2_headers)
        self.assertEqual(response.status_code, 200)
        post2_id = response.json()["post_id"]
        
        # Verify posts are in database
        self.assertIn(post1_id, self.posts_db)
        self.assertIn(post2_id, self.posts_db)
        self.assertEqual(self.posts_db[post1_id]["title"], "Author1's Post")
        self.assertEqual(self.posts_db[post2_id]["title"], "Author2's Post")
        
        # Test viewing all posts
        response = self.client.get("/posts", headers=author1_headers)
        self.assertEqual(response.status_code, 200)
        posts = response.json()
        self.assertEqual(len(posts), 2)
        
        # Verify post structure
        post = posts[0]
        self.assertIn("post_id", post)
        self.assertIn("title", post)
        self.assertIn("content", post)
        self.assertIn("author", post)
        self.assertIn("created_at", post)
        
        # Test author1 can update their own post
        update_data = {"title": "Updated by Author1"}
        response = self.client.put(f"/posts/{post1_id}", json=update_data, headers=author1_headers)
        self.assertEqual(response.status_code, 200)
        
        # Test author2 cannot update author1's post
        response = self.client.put(f"/posts/{post1_id}", json=update_data, headers=author2_headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("You can only update your own posts", response.json()["detail"])
        
        # Test author1 can delete their own post
        response = self.client.delete(f"/posts/{post1_id}", headers=author1_headers)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(post1_id, self.posts_db)  # Post should be removed
        
        # Test author2 cannot delete author1's remaining posts
        # (if any were created in other tests)
        response = self.client.delete(f"/posts/{post2_id}", headers=author1_headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("You can only delete your own posts", response.json()["detail"])
        
        # Test 404 for non-existent posts
        response = self.client.get("/posts/999", headers=author1_headers)
        # Note: The current API doesn't have individual post GET endpoint
        # But we can test update/delete on non-existent posts
        response = self.client.put("/posts/999", json={"title": "Test"}, headers=author1_headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Post not found", response.json()["detail"])
        
        response = self.client.delete("/posts/999", headers=author1_headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Post not found", response.json()["detail"])
        
        print("PASS: Multiple authors can create posts")
        print("PASS: Post ownership validation working")
        print("PASS: Authors can only modify their own posts")
        print("PASS: Complete CRUD operations validated")
        print("PASS: 404 handling for non-existent posts")
        print("PASS: Blog post ownership validation completed")

def run_core_tests():
    """Run core tests and provide summary"""
    print("=" * 70)
    print("[*] Core JWT Authentication & Authorization Unit Tests (5 Tests)")
    print("Testing with LOCAL JWT Auth Components")
    print("=" * 70)
    
    print("[INFO] This system uses local JWT auth (no external dependencies)")
    print("[INFO] Tests validate JWT Setup, Registration, Login, Authorization, CRUD")
    print()
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(CoreJWTAuthTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    print("[*] Test Results:")
    print(f"[*] Tests Run: {result.testsRun}")
    print(f"[*] Failures: {len(result.failures)}")
    print(f"[*] Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n[FAILURES]:")
        for test, traceback in result.failures:
            print(f"  - {test}")
            print(f"    {traceback}")
    
    if result.errors:
        print("\n[ERRORS]:")
        for test, traceback in result.errors:
            print(f"  - {test}")
            print(f"    {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n[SUCCESS] All 5 core JWT authentication tests passed!")
        print("[OK] JWT auth components working correctly with local implementation")
        print("[OK] JWT Setup, Registration, Login, Authorization, CRUD validated")
    else:
        print(f"\n[WARNING] {len(result.failures) + len(result.errors)} test(s) failed")
    
    return success

if __name__ == "__main__":
    print("[*] Starting Core JWT Authentication & Authorization Tests")
    print("[*] 5 essential tests with local JWT auth implementation")
    print("[*] Components: JWT Setup, Registration, Login, Authorization, CRUD")
    print()
    
    success = run_core_tests()
    exit(0 if success else 1)