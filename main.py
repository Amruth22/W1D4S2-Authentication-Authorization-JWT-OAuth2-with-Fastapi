from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import time
from typing import Optional, List

app = FastAPI(title="Simple Blog API", description="Blog API with JWT Authentication and Role-based Authorization")

# Security configuration
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# In-memory storage (for educational purposes)
users_db = {}  # {username: {password_hash, role, user_id}}
posts_db = {}  # {post_id: {title, content, author_id, created_at}}
login_attempts = {}  # {username: {attempts, last_attempt_time}}
user_counter = 1
post_counter = 1

# Pydantic models
class UserRegister(BaseModel):
    username: str
    password: str
    role: str  # "reader" or "author"

class UserLogin(BaseModel):
    username: str
    password: str

class BlogPost(BaseModel):
    title: str
    content: str

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    user_id: int
    username: str
    role: str

# Utility functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def check_rate_limit(username: str) -> bool:
    """Check if user has exceeded login rate limit (5 attempts per minute)"""
    current_time = time.time()
    
    if username not in login_attempts:
        login_attempts[username] = {"attempts": 0, "last_attempt_time": current_time}
        return True
    
    user_attempts = login_attempts[username]
    
    # Reset attempts if more than 1 minute has passed
    if current_time - user_attempts["last_attempt_time"] > 60:
        user_attempts["attempts"] = 0
        user_attempts["last_attempt_time"] = current_time
        return True
    
    # Check if under rate limit
    if user_attempts["attempts"] < 5:
        return True
    
    return False

def increment_login_attempts(username: str):
    """Increment login attempts for rate limiting"""
    current_time = time.time()
    if username not in login_attempts:
        login_attempts[username] = {"attempts": 1, "last_attempt_time": current_time}
    else:
        login_attempts[username]["attempts"] += 1
        login_attempts[username]["last_attempt_time"] = current_time

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = users_db.get(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return User(
        user_id=user["user_id"],
        username=username,
        role=user["role"]
    )

def require_author_role(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require author role"""
    if current_user.role != "author":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only authors can perform this action"
        )
    return current_user

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Welcome to Simple Blog API with JWT Authentication!"}

@app.post("/register", response_model=dict)
async def register_user(user: UserRegister):
    """Register a new user"""
    global user_counter
    
    # Validate role
    if user.role not in ["reader", "author"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be either 'reader' or 'author'"
        )
    
    # Check if user already exists
    if user.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Hash password and store user
    hashed_password = hash_password(user.password)
    users_db[user.username] = {
        "password_hash": hashed_password,
        "role": user.role,
        "user_id": user_counter
    }
    user_counter += 1
    
    return {"message": f"User {user.username} registered successfully as {user.role}"}

@app.post("/login", response_model=Token)
async def login_user(user: UserLogin):
    """Login user and return JWT token"""
    
    # Check rate limiting
    if not check_rate_limit(user.username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    # Increment login attempts
    increment_login_attempts(user.username)
    
    # Check if user exists
    stored_user = users_db.get(user.username)
    if not stored_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password
    if not verify_password(user.password, stored_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/posts", response_model=List[dict])
async def get_all_posts(current_user: User = Depends(get_current_user)):
    """Get all blog posts (accessible to both readers and authors)"""
    posts = []
    for post_id, post_data in posts_db.items():
        # Get author username
        author_username = None
        for username, user_data in users_db.items():
            if user_data["user_id"] == post_data["author_id"]:
                author_username = username
                break
        
        posts.append({
            "post_id": post_id,
            "title": post_data["title"],
            "content": post_data["content"],
            "author": author_username,
            "created_at": post_data["created_at"]
        })
    
    return posts

@app.post("/posts", response_model=dict)
async def create_post(post: BlogPost, current_user: User = Depends(require_author_role)):
    """Create a new blog post (authors only)"""
    global post_counter
    
    posts_db[post_counter] = {
        "title": post.title,
        "content": post.content,
        "author_id": current_user.user_id,
        "created_at": datetime.utcnow().isoformat()
    }
    
    post_id = post_counter
    post_counter += 1
    
    return {
        "message": "Post created successfully",
        "post_id": post_id,
        "title": post.title
    }

@app.put("/posts/{post_id}", response_model=dict)
async def update_post(post_id: int, post_update: BlogPostUpdate, current_user: User = Depends(require_author_role)):
    """Update a blog post (authors can only update their own posts)"""
    
    # Check if post exists
    if post_id not in posts_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Check if current user is the author of the post
    if posts_db[post_id]["author_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own posts"
        )
    
    # Update post fields
    if post_update.title is not None:
        posts_db[post_id]["title"] = post_update.title
    if post_update.content is not None:
        posts_db[post_id]["content"] = post_update.content
    
    return {"message": "Post updated successfully", "post_id": post_id}

@app.delete("/posts/{post_id}", response_model=dict)
async def delete_post(post_id: int, current_user: User = Depends(require_author_role)):
    """Delete a blog post (authors can only delete their own posts)"""
    
    # Check if post exists
    if post_id not in posts_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Check if current user is the author of the post
    if posts_db[post_id]["author_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own posts"
        )
    
    # Delete post
    deleted_post = posts_db.pop(post_id)
    
    return {
        "message": "Post deleted successfully",
        "post_id": post_id,
        "title": deleted_post["title"]
    }

@app.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)