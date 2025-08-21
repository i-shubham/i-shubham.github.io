"""
Scalable Database configuration for millions of concurrent users
Uses async SQLAlchemy with connection pooling and optimized queries
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, DECIMAL, Enum, ForeignKey, BigInteger, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import hashlib
import zlib
import json

# Load environment variables
load_dotenv()

# Database configuration with async support and connection pooling
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+aiomysql://compiler_user:your_secure_password@localhost/online_compiler_db"
)

# Connection pool settings for high concurrency
POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", 20))
MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", 30))
POOL_RECYCLE = int(os.getenv("DATABASE_POOL_RECYCLE", 3600))
POOL_PRE_PING = os.getenv("DATABASE_POOL_PRE_PING", "true").lower() == "true"

# Create async engine with optimized settings
engine = create_async_engine(
    DATABASE_URL,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_recycle=POOL_RECYCLE,
    pool_pre_ping=POOL_PRE_PING,
    echo=False,  # Set to True for debugging
    future=True,
    # Connection pool settings for high concurrency
    connect_args={
        "server_side_cursors": True,
        "charset": "utf8mb4",
    }
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Optimized database models for millions of users
class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    profile_picture = Column(String(500))
    email_verified = Column(Boolean, default=False, index=True)
    email_verification_token = Column(String(255))
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, index=True)
    last_password_change = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, index=True)
    last_activity = Column(DateTime)
    is_active = Column(Boolean, default=True, index=True)
    user_role = Column(Enum('user', 'premium', 'admin'), default='user')
    timezone = Column(String(50), default='UTC')
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    executions = relationship("CodeExecution", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    snippets = relationship("SavedSnippet", back_populates="user", cascade="all, delete-orphan")
    attempts = relationship("QuestionAttempt", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("UserActivityLog", back_populates="user", cascade="all, delete-orphan")

    # Composite indexes for performance
    __table_args__ = (
        Index('idx_composite_login', 'username', 'password_hash', 'is_active'),
        Index('idx_composite_email', 'email', 'email_verified', 'is_active'),
        Index('idx_user_activity', 'is_active', 'last_activity'),
    )

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    refresh_token_hash = Column(String(255))
    device_info = Column(JSON)
    ip_address = Column(String(45), index=True)
    user_agent = Column(Text)
    location_info = Column(JSON)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    last_accessed = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    # Composite indexes
    __table_args__ = (
        Index('idx_composite_session', 'user_id', 'is_active', 'expires_at'),
        Index('idx_session_cleanup', 'expires_at', 'is_active'),
    )

class CodeExecution(Base):
    __tablename__ = "code_executions"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(255), index=True)
    language = Column(String(50), nullable=False, index=True)
    code_hash = Column(String(64), index=True)  # SHA256 hash of code
    code_snippet_compressed = Column(Text)  # Compressed code for storage efficiency
    output_compressed = Column(Text)  # Compressed output
    error_message = Column(Text)
    execution_time = Column(DECIMAL(10, 6))
    memory_used = Column(Integer)  # Memory usage in KB
    cpu_time = Column(DECIMAL(10, 6))  # CPU time used
    status = Column(Enum('success', 'error', 'timeout', 'memory_limit', 'time_limit'), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    ip_address = Column(String(45))
    
    # Relationships
    user = relationship("User", back_populates="executions")
    
    # Composite indexes for analytics and performance
    __table_args__ = (
        Index('idx_composite_user_date', 'user_id', 'created_at'),
        Index('idx_composite_stats', 'user_id', 'language', 'status'),
        Index('idx_execution_analytics', 'language', 'status', 'created_at'),
    )

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True, nullable=False)
    default_language = Column(String(50), default="python")
    theme = Column(String(20), default="dark")
    font_size = Column(Integer, default=14)
    auto_save = Column(Boolean, default=True)
    notifications = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")

class SavedSnippet(Base):
    __tablename__ = "saved_snippets"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    language = Column(String(50), nullable=False, index=True)
    code = Column(Text, nullable=False)
    is_public = Column(Boolean, default=False, index=True)
    tags = Column(String(500))
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="snippets")
    
    # Indexes for searching
    __table_args__ = (
        Index('idx_snippets_public', 'is_public', 'language'),
        Index('idx_snippets_user_updated', 'user_id', 'updated_at'),
    )

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(Enum('easy', 'medium', 'hard'), nullable=False, index=True)
    category = Column(String(100), index=True)
    tags = Column(String(500))
    input_format = Column(Text)
    output_format = Column(Text)
    constraints = Column(Text)
    sample_input = Column(Text)
    sample_output = Column(Text)
    explanation = Column(Text)
    created_by = Column(BigInteger, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    attempts = relationship("QuestionAttempt", back_populates="question")

class QuestionAttempt(Base):
    __tablename__ = "question_attempts"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    language = Column(String(50), nullable=False)
    code = Column(Text, nullable=False)
    status = Column(Enum('attempted', 'solved', 'partially_solved'), nullable=False, index=True)
    execution_time = Column(DECIMAL(10, 6))
    memory_used = Column(Integer)
    test_cases_passed = Column(Integer, default=0)
    total_test_cases = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="attempts")
    question = relationship("Question", back_populates="attempts")

class RateLimit(Base):
    __tablename__ = "rate_limits"
    
    id = Column(BigInteger, primary_key=True, index=True)
    identifier = Column(String(255), nullable=False, index=True)  # IP address or user_id
    identifier_type = Column(Enum('ip', 'user'), nullable=False)
    endpoint = Column(String(255), nullable=False)
    requests_count = Column(Integer, default=0)
    window_start = Column(DateTime, default=func.now(), index=True)
    blocked_until = Column(DateTime, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Unique constraint for rate limiting
    __table_args__ = (
        Index('unique_rate_limit', 'identifier', 'endpoint', unique=True),
    )

class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True)
    activity_type = Column(Enum('login', 'logout', 'failed_login', 'password_change', 'email_change', 'account_locked', 'account_unlocked'), nullable=False, index=True)
    ip_address = Column(String(45), index=True)
    user_agent = Column(Text)
    additional_data = Column(JSON)
    created_at = Column(DateTime, default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")

class SystemStatsCache(Base):
    __tablename__ = "system_stats_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    stat_key = Column(String(255), unique=True, nullable=False, index=True)
    stat_value = Column(BigInteger, nullable=False)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime, index=True)

# Database dependency for async sessions
async def get_async_db():
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Utility functions for code compression (to save storage with millions of executions)
def compress_code(code: str) -> str:
    """Compress code snippet for storage efficiency"""
    if not code:
        return ""
    compressed = zlib.compress(code.encode('utf-8'), level=9)
    return compressed.hex()

def decompress_code(compressed_hex: str) -> str:
    """Decompress code snippet"""
    if not compressed_hex:
        return ""
    try:
        compressed = bytes.fromhex(compressed_hex)
        return zlib.decompress(compressed).decode('utf-8')
    except Exception:
        return ""

def hash_code(code: str) -> str:
    """Generate SHA256 hash of code for deduplication"""
    if not code:
        return ""
    return hashlib.sha256(code.encode('utf-8')).hexdigest()

# Database management functions
async def create_tables():
    """Create all tables in the database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_user_by_username(db: AsyncSession, username: str):
    """Get user by username"""
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.username == username.lower()))
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str):
    """Get user by email"""
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: int):
    """Get user by ID"""
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def update_user_activity(db: AsyncSession, user_id: int):
    """Update user's last activity timestamp"""
    from sqlalchemy import update
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(last_activity=func.now())
    )
    await db.commit()

async def cleanup_expired_sessions(db: AsyncSession):
    """Clean up expired sessions (should be run periodically)"""
    from sqlalchemy import delete
    await db.execute(
        delete(UserSession)
        .where(UserSession.expires_at < func.now())
    )
    await db.commit()

async def log_code_execution_optimized(
    db: AsyncSession, user_id: int, session_id: str, language: str, 
    code: str, output: str = None, error_message: str = None, 
    execution_time: float = None, memory_used: int = None,
    cpu_time: float = None, status: str = "success", ip_address: str = None
):
    """Log code execution with compression and optimization for high volume"""
    
    # Generate hash for deduplication
    code_hash = hash_code(code)
    
    # Compress code and output for storage efficiency
    code_compressed = compress_code(code)
    output_compressed = compress_code(output) if output else None
    
    execution = CodeExecution(
        user_id=user_id,
        session_id=session_id,
        language=language,
        code_hash=code_hash,
        code_snippet_compressed=code_compressed,
        output_compressed=output_compressed,
        error_message=error_message,
        execution_time=execution_time,
        memory_used=memory_used,
        cpu_time=cpu_time,
        status=status,
        ip_address=ip_address
    )
    
    db.add(execution)
    await db.commit()
    return execution

async def get_user_stats_optimized(db: AsyncSession, user_id: int) -> dict:
    """Get user statistics with optimized queries"""
    from sqlalchemy import select, func, distinct
    
    # Get total executions
    total_executions = await db.execute(
        select(func.count(CodeExecution.id))
        .where(CodeExecution.user_id == user_id)
    )
    total_executions = total_executions.scalar() or 0
    
    # Get languages used
    languages = await db.execute(
        select(distinct(CodeExecution.language))
        .where(CodeExecution.user_id == user_id)
    )
    languages_used = [lang[0] for lang in languages.fetchall()]
    
    # Get recent activity (last 10 executions)
    recent_activity = await db.execute(
        select(CodeExecution)
        .where(CodeExecution.user_id == user_id)
        .order_by(CodeExecution.created_at.desc())
        .limit(10)
    )
    
    recent_list = []
    for activity in recent_activity.fetchall():
        recent_list.append({
            "language": activity.language,
            "status": activity.status,
            "created_at": activity.created_at.isoformat(),
            "execution_time": float(activity.execution_time) if activity.execution_time else 0
        })
    
    return {
        "total_executions": total_executions,
        "languages_used": languages_used,
        "recent_activity": recent_list
    }

# Connection health check
async def check_database_health():
    """Check database connection health"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(select(1))
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False
