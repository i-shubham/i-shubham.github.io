"""
Scalable Authentication System for Millions of Concurrent Users
Handles traditional username/password authentication with MySQL and Redis
"""

from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from passlib.context import CryptContext
from passlib.hash import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import secrets
import hashlib
import json
import asyncio
import aioredis
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, validator
import re
from email_validator import validate_email, EmailNotValidError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from database import get_async_db, User, UserSession, UserActivityLog, RateLimit

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 30
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30

# Redis configuration for session storage and caching
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer(auto_error=False)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Redis connection pool
redis_pool = None

async def get_redis():
    """Get Redis connection"""
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.from_url(REDIS_URL, decode_responses=True)
    return redis_pool

# Pydantic models for request/response
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Username must be between 3 and 50 characters')
        if not re.match('^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower()

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserLogin(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    first_name: Optional[str]
    last_name: Optional[str]
    profile_picture: Optional[str]
    email_verified: bool
    user_role: str
    created_at: datetime
    last_login: Optional[datetime]

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

# Utility functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def generate_session_id() -> str:
    """Generate secure session ID"""
    return secrets.token_urlsafe(32)

def generate_refresh_token() -> str:
    """Generate refresh token"""
    return secrets.token_urlsafe(64)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None

def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

async def check_rate_limit(identifier: str, identifier_type: str, endpoint: str, 
                          max_requests: int, window_minutes: int, db: AsyncSession) -> bool:
    """Check if request is within rate limits"""
    redis = await get_redis()
    
    # Use Redis for fast rate limiting
    key = f"rate_limit:{identifier_type}:{identifier}:{endpoint}"
    current_time = datetime.utcnow()
    window_start = current_time - timedelta(minutes=window_minutes)
    
    # Get current count from Redis
    current_count = await redis.get(key)
    if current_count is None:
        current_count = 0
    else:
        current_count = int(current_count)
    
    if current_count >= max_requests:
        return False
    
    # Increment counter
    await redis.incr(key)
    await redis.expire(key, window_minutes * 60)
    
    return True

async def log_user_activity(db: AsyncSession, user_id: Optional[int], activity_type: str, 
                           ip_address: str, user_agent: str, additional_data: Optional[dict] = None):
    """Log user activity for security monitoring"""
    activity_log = UserActivityLog(
        user_id=user_id,
        activity_type=activity_type,
        ip_address=ip_address,
        user_agent=user_agent,
        additional_data=additional_data
    )
    db.add(activity_log)
    await db.commit()

async def store_session_in_redis(session_id: str, user_data: dict, expires_in_seconds: int):
    """Store session data in Redis for fast access"""
    redis = await get_redis()
    await redis.setex(f"session:{session_id}", expires_in_seconds, json.dumps(user_data))

async def get_session_from_redis(session_id: str) -> Optional[dict]:
    """Get session data from Redis"""
    redis = await get_redis()
    session_data = await redis.get(f"session:{session_id}")
    if session_data:
        return json.loads(session_data)
    return None

async def delete_session_from_redis(session_id: str):
    """Delete session from Redis"""
    redis = await get_redis()
    await redis.delete(f"session:{session_id}")

async def register_user(user_data: UserRegister, request: Request, db: AsyncSession) -> User:
    """Register a new user"""
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    
    # Check rate limiting for registration
    if not await check_rate_limit(ip_address, "ip", "register", 5, 60, db):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later."
        )
    
    # Check if username or email already exists
    existing_user = await db.execute(
        select(User).where(
            (User.username == user_data.username) | (User.email == user_data.email)
        )
    )
    if existing_user.scalar_one_or_none():
        await log_user_activity(db, None, "failed_login", ip_address, user_agent, 
                               {"reason": "username_or_email_exists", "username": user_data.username})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email_verification_token=secrets.token_urlsafe(32)
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Log successful registration
    await log_user_activity(db, new_user.id, "login", ip_address, user_agent, 
                           {"type": "registration"})
    
    return new_user

async def authenticate_user(login_data: UserLogin, request: Request, db: AsyncSession) -> Optional[User]:
    """Authenticate user with username/password"""
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    
    # Check rate limiting for login attempts
    if not await check_rate_limit(ip_address, "ip", "login", 10, 15, db):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    # Get user by username or email
    user = await db.execute(
        select(User).where(
            (User.username == login_data.username.lower()) | (User.email == login_data.username)
        )
    )
    user = user.scalar_one_or_none()
    
    if not user:
        await log_user_activity(db, None, "failed_login", ip_address, user_agent, 
                               {"reason": "user_not_found", "username": login_data.username})
        return None
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        await log_user_activity(db, user.id, "failed_login", ip_address, user_agent, 
                               {"reason": "account_locked"})
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account is locked until {user.locked_until}"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        # Increment failed attempts
        user.failed_login_attempts += 1
        
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            await log_user_activity(db, user.id, "account_locked", ip_address, user_agent, 
                                   {"failed_attempts": user.failed_login_attempts})
        
        await db.commit()
        await log_user_activity(db, user.id, "failed_login", ip_address, user_agent, 
                               {"reason": "wrong_password", "failed_attempts": user.failed_login_attempts})
        return None
    
    # Reset failed attempts on successful login
    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        user.locked_until = None
    
    user.last_login = datetime.utcnow()
    user.last_activity = datetime.utcnow()
    await db.commit()
    
    # Log successful login
    await log_user_activity(db, user.id, "login", ip_address, user_agent, {"type": "password_login"})
    
    return user

async def create_user_session(user: User, request: Request, remember_me: bool, db: AsyncSession) -> tuple:
    """Create user session and return tokens"""
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    
    # Generate tokens
    session_id = generate_session_id()
    refresh_token = generate_refresh_token()
    
    # Create access token
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "session_id": session_id},
        expires_delta=access_token_expires
    )
    
    # Set expiration times
    if remember_me:
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        expires_at = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    # Create session record in database
    session = UserSession(
        user_id=user.id,
        session_id=session_id,
        refresh_token_hash=hash_password(refresh_token),
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=expires_at,
        device_info={
            "browser": request.headers.get("user-agent", ""),
            "accept_language": request.headers.get("accept-language", ""),
        }
    )
    
    db.add(session)
    await db.commit()
    
    # Store session in Redis for fast access
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "user_role": user.user_role,
        "session_id": session_id
    }
    
    expires_in_seconds = int((expires_at - datetime.utcnow()).total_seconds())
    await store_session_in_redis(session_id, user_data, expires_in_seconds)
    
    return access_token, refresh_token, expires_in_seconds

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_async_db)
) -> Optional[User]:
    """Get current user from token (optional - returns None if not authenticated)"""
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # Verify JWT token
    payload = verify_token(token)
    if not payload:
        return None
    
    session_id = payload.get("session_id")
    user_id = payload.get("sub")
    
    if not session_id or not user_id:
        return None
    
    # Check session in Redis first (fast)
    session_data = await get_session_from_redis(session_id)
    if session_data:
        # Update last activity
        user = await db.execute(select(User).where(User.id == int(user_id)))
        user = user.scalar_one_or_none()
        if user and user.is_active:
            user.last_activity = datetime.utcnow()
            await db.commit()
            return user
    
    # Fallback to database
    session = await db.execute(
        select(UserSession).where(
            and_(
                UserSession.session_id == session_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
    )
    session = session.scalar_one_or_none()
    
    if session:
        user = await db.execute(select(User).where(User.id == session.user_id))
        user = user.scalar_one_or_none()
        if user and user.is_active:
            # Update last activity
            user.last_activity = datetime.utcnow()
            session.last_accessed = datetime.utcnow()
            await db.commit()
            return user
    
    return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """Get current user from token (required - raises exception if not authenticated)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await get_current_user_optional(credentials, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def logout_user(session_id: str, db: AsyncSession):
    """Logout user by deactivating session"""
    # Remove from Redis
    await delete_session_from_redis(session_id)
    
    # Deactivate in database
    await db.execute(
        update(UserSession)
        .where(UserSession.session_id == session_id)
        .values(is_active=False)
    )
    await db.commit()

def user_to_dict(user: User) -> dict:
    """Convert User model to dictionary"""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "profile_picture": user.profile_picture,
        "email_verified": user.email_verified,
        "user_role": user.user_role,
        "created_at": user.created_at,
        "last_login": user.last_login
    }

# Environment file template for scalable deployment
ENV_TEMPLATE = """
# Database Configuration (MySQL with connection pooling)
DATABASE_URL=mysql+aiomysql://compiler_user:your_secure_password@localhost/online_compiler_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# JWT Configuration
SECRET_KEY=your-super-secret-key-here-change-in-production-use-openssl-rand-hex-32

# Redis Configuration for sessions and caching
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=10

# Rate Limiting Configuration
MAX_REQUESTS_PER_MINUTE=100
MAX_LOGIN_ATTEMPTS=10
LOCKOUT_DURATION_MINUTES=30

# Session Configuration
ACCESS_TOKEN_EXPIRE_HOURS=24
REFRESH_TOKEN_EXPIRE_DAYS=30

# Email Configuration (for email verification)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
"""

def create_env_file():
    """Create .env file with template if it doesn't exist"""
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(ENV_TEMPLATE)
        print("Created .env file with template. Please update with your actual values.")
        return True
    return False
