"""
Simple test script to demonstrate the Blog API functionality
Run this after starting the FastAPI server (python main.py)
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"

def test_api():
    print("🚀 Testing Simple Blog API with JWT Authentication\n")
    
    # Test 1: Register users
    print("1️⃣ Registering users...")
    
    # Register an author
    author_data = {
        "username": "alice_author",
        "password": "secure123",
        "role": "author"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=author_data)
    print(f"   Author registration: {response.status_code} - {response.json()}")
    
    # Register a reader
    reader_data = {
        "username": "bob_reader",
        "password": "secure456",
        "role": "reader"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=reader_data)
    print(f"   Reader registration: {response.status_code} - {response.json()}")
    
    print()
    
    # Test 2: Login and get tokens
    print("2️⃣ Logging in users...")
    
    # Login author
    login_data = {
        "username": "alice_author",
        "password": "secure123"
    }
    
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    if response.status_code == 200:
        author_token = response.json()["access_token"]
        print(f"   Author login successful! Token: {author_token[:50]}...")
    else:
        print(f"   Author login failed: {response.json()}")
        return
    
    # Login reader
    login_data = {
        "username": "bob_reader",
        "password": "secure456"
    }
    
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    if response.status_code == 200:
        reader_token = response.json()["access_token"]
        print(f"   Reader login successful! Token: {reader_token[:50]}...")
    else:
        print(f"   Reader login failed: {response.json()}")
        return
    
    print()
    
    # Test 3: Create blog posts (author only)
    print("3️⃣ Creating blog posts...")
    
    headers = {"Authorization": f"Bearer {author_token}"}
    
    post_data = {
        "title": "Welcome to My Blog!",
        "content": "This is my first blog post. I'm excited to share my thoughts with you!"
    }
    
    response = requests.post(f"{BASE_URL}/posts", json=post_data, headers=headers)
    print(f"   Author creating post: {response.status_code} - {response.json()}")
    
    # Try reader creating post (should fail)
    reader_headers = {"Authorization": f"Bearer {reader_token}"}
    response = requests.post(f"{BASE_URL}/posts", json=post_data, headers=reader_headers)
    print(f"   Reader trying to create post: {response.status_code} - {response.json()}")
    
    print()
    
    # Test 4: View all posts
    print("4️⃣ Viewing all posts...")
    
    # Author viewing posts
    response = requests.get(f"{BASE_URL}/posts", headers=headers)
    if response.status_code == 200:
        posts = response.json()
        print(f"   Author can see {len(posts)} posts")
        for post in posts:
            print(f"      - Post {post['post_id']}: '{post['title']}' by {post['author']}")
    
    # Reader viewing posts
    response = requests.get(f"{BASE_URL}/posts", headers=reader_headers)
    if response.status_code == 200:
        posts = response.json()
        print(f"   Reader can see {len(posts)} posts")
    
    print()
    
    # Test 5: Update post (author only, own posts only)
    print("5️⃣ Updating blog post...")
    
    if posts:  # If we have posts from previous test
        post_id = posts[0]['post_id']
        
        update_data = {
            "title": "Updated: Welcome to My Blog!",
            "content": "This is my updated first blog post with more content!"
        }
        
        response = requests.put(f"{BASE_URL}/posts/{post_id}", json=update_data, headers=headers)
        print(f"   Author updating own post: {response.status_code} - {response.json()}")
        
        # Try reader updating post (should fail)
        response = requests.put(f"{BASE_URL}/posts/{post_id}", json=update_data, headers=reader_headers)
        print(f"   Reader trying to update post: {response.status_code} - {response.json()}")
    
    print()
    
    # Test 6: Get user info
    print("6️⃣ Getting user information...")
    
    response = requests.get(f"{BASE_URL}/me", headers=headers)
    print(f"   Author info: {response.json()}")
    
    response = requests.get(f"{BASE_URL}/me", headers=reader_headers)
    print(f"   Reader info: {response.json()}")
    
    print()
    
    # Test 7: Rate limiting (login attempts)
    print("7️⃣ Testing rate limiting...")
    
    print("   Making multiple failed login attempts...")
    for i in range(6):  # Try 6 times (limit is 5)
        bad_login = {
            "username": "alice_author",
            "password": "wrong_password"
        }
        response = requests.post(f"{BASE_URL}/login", json=bad_login)
        print(f"   Attempt {i+1}: {response.status_code}")
        
        if response.status_code == 429:
            print("   ✅ Rate limiting working! Too many attempts blocked.")
            break
    
    print()
    
    # Test 8: Authentication required
    print("8️⃣ Testing authentication requirement...")
    
    # Try accessing posts without token
    response = requests.get(f"{BASE_URL}/posts")
    print(f"   Accessing posts without token: {response.status_code}")
    
    # Try with invalid token
    bad_headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{BASE_URL}/posts", headers=bad_headers)
    print(f"   Accessing posts with invalid token: {response.status_code}")
    
    print("\n✅ API testing completed!")

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server.")
        print("   Make sure the FastAPI server is running on http://localhost:8000")
        print("   Run: python main.py")
    except Exception as e:
        print(f"❌ Error during testing: {e}")