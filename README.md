# Simple Blog API with JWT Authentication & Authorization

A simple educational FastAPI application demonstrating authentication, authorization, and security best practices.

## Features

### 🔐 Authentication & Authorization
- **JWT Token Authentication** with 15-minute expiration
- **Role-based Access Control** (Reader vs Author roles)
- **Password Hashing** using bcrypt
- **Rate Limiting** on login attempts (max 5 per minute)

### 📝 Blog Functionality
- **Readers**: Can view all blog posts
- **Authors**: Can create, edit, and delete their own posts
- **Post Management**: Full CRUD operations with ownership validation

### 🛡️ Security Features
- Secure password hashing
- JWT token expiration
- Rate limiting on login attempts
- Role-based endpoint protection
- Input validation with Pydantic

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Amruth22/W1D4S2-Authentication-Authorization-JWT-OAuth2-with-Fastapi.git
cd W1D4S2-Authentication-Authorization-JWT-OAuth2-with-Fastapi
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python main.py
```

The API will be available at: `http://localhost:8000`

### 4. View API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication Endpoints

#### Register User
```http
POST /register
Content-Type: application/json

{
    "username": "john_doe",
    "password": "secure_password123",
    "role": "author"  // or "reader"
}
```

#### Login User
```http
POST /login
Content-Type: application/json

{
    "username": "john_doe",
    "password": "secure_password123"
}
```

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

### Blog Post Endpoints

#### Get All Posts (Authenticated Users)
```http
GET /posts
Authorization: Bearer <your_jwt_token>
```

#### Create Post (Authors Only)
```http
POST /posts
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
    "title": "My First Blog Post",
    "content": "This is the content of my blog post..."
}
```

#### Update Post (Own Posts Only)
```http
PUT /posts/{post_id}
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
    "title": "Updated Title",
    "content": "Updated content..."
}
```

#### Delete Post (Own Posts Only)
```http
DELETE /posts/{post_id}
Authorization: Bearer <your_jwt_token>
```

### User Info Endpoint

#### Get Current User Info
```http
GET /me
Authorization: Bearer <your_jwt_token>
```

## Usage Examples

### 1. Register a New Author
```bash
curl -X POST "http://localhost:8000/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "author1",
       "password": "password123",
       "role": "author"
     }'
```

### 2. Login and Get Token
```bash
curl -X POST "http://localhost:8000/login" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "author1",
       "password": "password123"
     }'
```

### 3. Create a Blog Post
```bash
curl -X POST "http://localhost:8000/posts" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "My First Post",
       "content": "Hello, this is my first blog post!"
     }'
```

### 4. View All Posts
```bash
curl -X GET "http://localhost:8000/posts" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## User Roles & Permissions

| Role | View Posts | Create Posts | Edit Own Posts | Delete Own Posts |
|------|------------|--------------|----------------|------------------|
| **Reader** | ✅ | ❌ | ❌ | ❌ |
| **Author** | ✅ | ✅ | ✅ | ✅ |

## Security Features Explained

### 1. Password Hashing
- Uses bcrypt for secure password hashing
- Passwords are never stored in plain text

### 2. JWT Token Security
- Tokens expire after 15 minutes
- Signed with a secret key
- Contains user information for authorization

### 3. Rate Limiting
- Maximum 5 login attempts per minute per user
- Prevents brute force attacks
- Automatically resets after 1 minute

### 4. Role-Based Access Control
- Different permissions for readers and authors
- Authors can only modify their own posts
- Middleware enforces role requirements

## Project Structure

```
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
└── README.md           # Project documentation
```

## Educational Notes

This project demonstrates several important concepts:

1. **Authentication vs Authorization**
   - Authentication: Verifying who the user is (login)
   - Authorization: Determining what the user can do (roles)

2. **JWT Tokens**
   - Stateless authentication
   - Contains encoded user information
   - Has expiration time for security

3. **Password Security**
   - Never store plain text passwords
   - Use strong hashing algorithms (bcrypt)
   - Salt is automatically handled by bcrypt

4. **Rate Limiting**
   - Prevents abuse and attacks
   - Simple in-memory implementation
   - Production apps should use Redis or similar

5. **Role-Based Access Control (RBAC)**
   - Users have roles with specific permissions
   - Endpoints can require specific roles
   - Ownership validation for resource access

## Production Considerations

For production use, consider:

1. **Database**: Replace in-memory storage with PostgreSQL/MySQL
2. **Secret Management**: Use environment variables for secrets
3. **Rate Limiting**: Use Redis for distributed rate limiting
4. **Logging**: Add comprehensive logging
5. **HTTPS**: Always use HTTPS in production
6. **Token Refresh**: Implement refresh token mechanism
7. **Input Validation**: Add more comprehensive validation
8. **Error Handling**: Improve error messages and handling

## Dependencies

- **FastAPI**: Modern, fast web framework
- **Uvicorn**: ASGI server for running FastAPI
- **python-jose**: JWT token handling
- **passlib**: Password hashing utilities
- **bcrypt**: Secure password hashing algorithm
- **pydantic**: Data validation and serialization

## License

This project is for educational purposes. Feel free to use and modify as needed.

## Contributing

This is an educational project. Feel free to fork and experiment with additional features like:
- User profiles
- Post categories
- Comments system
- Email verification
- Password reset functionality