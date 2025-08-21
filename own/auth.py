"""
Authentication system with Google OAuth for Online Compiler
"""

from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from authlib.common.security import generate_token
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import httpx
from typing import Optional

from database import get_db, get_user_by_google_id, create_user, update_user_login, create_session, get_active_session, User

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")

# OAuth setup
oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Security
security = HTTPBearer(auto_error=False)

# Pydantic models
from pydantic import BaseModel

class UserCreate(BaseModel):
    google_id: str
    email: str
    name: str
    picture_url: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    picture_url: Optional[str]
    given_name: Optional[str]
    family_name: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

# Utility functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

async def verify_google_token(token: str):
    """Verify Google OAuth token"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?access_token={token}"
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception:
        return None

async def get_google_user_info(access_token: str):
    """Get user info from Google using access token"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception:
        return None

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from token (optional - returns None if not authenticated)"""
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # First try to get from session token
    session = get_active_session(db, token)
    if session:
        return session.user
    
    # Then try JWT token
    payload = verify_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    return user

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from token (required - raises exception if not authenticated)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_current_user_optional(credentials, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

def create_user_from_google_data(google_user_data: dict, db: Session) -> User:
    """Create user from Google user data"""
    return create_user(
        db=db,
        google_id=google_user_data["id"],
        email=google_user_data["email"],
        name=google_user_data["name"],
        picture_url=google_user_data.get("picture"),
        given_name=google_user_data.get("given_name"),
        family_name=google_user_data.get("family_name"),
        locale=google_user_data.get("locale", "en")
    )

def user_to_dict(user: User) -> dict:
    """Convert User model to dictionary"""
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture_url": user.picture_url,
        "given_name": user.given_name,
        "family_name": user.family_name,
        "created_at": user.created_at,
        "last_login": user.last_login
    }

# Authentication middleware
class AuthenticationMiddleware:
    """Middleware to handle authentication for routes"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Add user info to scope if authenticated
            request = Request(scope, receive)
            
            # Check for authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                
                # Try to get user from token
                try:
                    db = next(get_db())
                    
                    # Try session token first
                    session = get_active_session(db, token)
                    if session:
                        scope["user"] = session.user
                    else:
                        # Try JWT token
                        payload = verify_token(token)
                        if payload:
                            user_id = payload.get("sub")
                            if user_id:
                                user = db.query(User).filter(User.id == int(user_id)).first()
                                if user:
                                    scope["user"] = user
                    
                    db.close()
                except Exception:
                    pass
        
        await self.app(scope, receive, send)

# Environment file template
ENV_TEMPLATE = """
# Database Configuration
DATABASE_URL=mysql+pymysql://compiler_user:your_secure_password@localhost/online_compiler_db

# JWT Configuration
SECRET_KEY=your-super-secret-key-here-change-in-production-use-openssl-rand-hex-32

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Optional: Redis for session storage (if using Redis)
REDIS_URL=redis://localhost:6379/0
"""

def create_env_file():
    """Create .env file with template if it doesn't exist"""
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(ENV_TEMPLATE)
        print("Created .env file with template. Please update with your actual values.")
        return True
    return False
