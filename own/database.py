"""
Database configuration and models for Online Compiler
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, DECIMAL, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://compiler_user:your_secure_password@localhost/online_compiler_db"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=True  # Set to False in production
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    picture_url = Column(Text)
    given_name = Column(String(255))
    family_name = Column(String(255))
    locale = Column(String(10), default="en")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user")
    executions = relationship("CodeExecution", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    snippets = relationship("SavedSnippet", back_populates="user")
    attempts = relationship("QuestionAttempt", back_populates="user")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    refresh_token = Column(String(255))
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    last_accessed = Column(DateTime, default=func.now(), onupdate=func.now())
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")

class CodeExecution(Base):
    __tablename__ = "code_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    language = Column(String(50), nullable=False)
    code_snippet = Column(Text, nullable=False)
    output = Column(Text)
    error_message = Column(Text)
    execution_time = Column(DECIMAL(10, 6))
    status = Column(Enum('success', 'error', 'timeout'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    ip_address = Column(String(45))
    
    # Relationships
    user = relationship("User", back_populates="executions")

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
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
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    language = Column(String(50), nullable=False)
    code = Column(Text, nullable=False)
    is_public = Column(Boolean, default=False)
    tags = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="snippets")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(Enum('easy', 'medium', 'hard'), nullable=False)
    category = Column(String(100))
    tags = Column(String(500))
    input_format = Column(Text)
    output_format = Column(Text)
    constraints = Column(Text)
    sample_input = Column(Text)
    sample_output = Column(Text)
    explanation = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    attempts = relationship("QuestionAttempt", back_populates="question")

class QuestionAttempt(Base):
    __tablename__ = "question_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    language = Column(String(50), nullable=False)
    code = Column(Text, nullable=False)
    status = Column(Enum('attempted', 'solved', 'partially_solved'), nullable=False)
    execution_time = Column(DECIMAL(10, 6))
    memory_used = Column(Integer)
    test_cases_passed = Column(Integer, default=0)
    total_test_cases = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="attempts")
    question = relationship("Question", back_populates="attempts")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)

def get_user_by_google_id(db: Session, google_id: str):
    """Get user by Google ID"""
    return db.query(User).filter(User.google_id == google_id).first()

def get_user_by_email(db: Session, email: str):
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, google_id: str, email: str, name: str, **kwargs):
    """Create a new user"""
    db_user = User(
        google_id=google_id,
        email=email,
        name=name,
        **kwargs
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create default preferences
    preferences = UserPreference(user_id=db_user.id)
    db.add(preferences)
    db.commit()
    
    return db_user

def update_user_login(db: Session, user_id: int):
    """Update user's last login timestamp"""
    db.query(User).filter(User.id == user_id).update({"last_login": func.now()})
    db.commit()

def create_session(db: Session, user_id: int, session_token: str, expires_at: datetime, **kwargs):
    """Create a new user session"""
    db_session = UserSession(
        user_id=user_id,
        session_token=session_token,
        expires_at=expires_at,
        **kwargs
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_active_session(db: Session, session_token: str):
    """Get active session by token"""
    return db.query(UserSession).filter(
        UserSession.session_token == session_token,
        UserSession.is_active == True,
        UserSession.expires_at > func.now()
    ).first()

def deactivate_session(db: Session, session_token: str):
    """Deactivate a session"""
    db.query(UserSession).filter(UserSession.session_token == session_token).update(
        {"is_active": False}
    )
    db.commit()

def log_code_execution(db: Session, user_id: int, language: str, code_snippet: str, 
                      output: str = None, error_message: str = None, 
                      execution_time: float = None, status: str = "success",
                      ip_address: str = None):
    """Log code execution"""
    execution = CodeExecution(
        user_id=user_id,
        language=language,
        code_snippet=code_snippet,
        output=output,
        error_message=error_message,
        execution_time=execution_time,
        status=status,
        ip_address=ip_address
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution
