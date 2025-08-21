"""
Online Compiler FastAPI Application with Google Authentication
"""

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
import subprocess
import tempfile
import os
import signal
import time
import asyncio
from threading import Timer
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import secrets

# Import our auth and database modules
from auth import (
    oauth, create_access_token, get_current_user_optional, get_current_user,
    get_client_ip, create_user_from_google_data, user_to_dict, get_google_user_info,
    create_env_file, SECRET_KEY, ACCESS_TOKEN_EXPIRE_HOURS, GOOGLE_REDIRECT_URI
)
from database import (
    get_db, get_user_by_google_id, get_user_by_email, update_user_login,
    create_session, log_code_execution, create_tables, User
)

# Create environment file if it doesn't exist
create_env_file()

app = FastAPI(
    title="Online Compiler API with Authentication",
    description="A web-based code compiler supporting multiple languages with Google OAuth authentication",
    version="3.0.0"
)

# Add session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables
try:
    create_tables()
    print("✅ Database tables initialized successfully")
except Exception as e:
    print(f"⚠️  Database initialization warning: {e}")

# Pydantic models for request/response
class CodeRequest(BaseModel):
    code: str
    language: str

class CodeResponse(BaseModel):
    output: str = None
    error: str = None
    execution_time: float

class UserStats(BaseModel):
    total_executions: int
    languages_used: list
    recent_activity: list

# Get the directory where this script is located
CURRENT_DIR = Path(__file__).parent

# Import all the existing code runners from the original file
async def run_python_code(code: str) -> Dict[str, Any]:
    """Execute Python code safely"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        start_time = time.time()
        
        process = await asyncio.create_subprocess_exec(
            'python3', temp_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
            execution_time = time.time() - start_time
            
            os.unlink(temp_file)
            
            if stderr:
                return {'error': stderr.decode(), 'execution_time': execution_time}
            return {'output': stdout.decode(), 'execution_time': execution_time}
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            os.unlink(temp_file)
            return {'error': 'Code execution timed out', 'execution_time': 5.0}
            
    except Exception as e:
        return {'error': str(e), 'execution_time': 0.0}

# Copy all other runners from the original file
async def run_c_code(code: str) -> Dict[str, Any]:
    """Compile and execute C code"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(code)
            c_file = f.name
        
        exe_file = c_file.replace('.c', '')
        
        # Compile
        compile_process = await asyncio.create_subprocess_exec(
            'gcc', c_file, '-o', exe_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(compile_process.communicate(), timeout=10)
        
        if compile_process.returncode != 0:
            os.unlink(c_file)
            return {'error': f'Compilation Error:\n{stderr.decode()}', 'execution_time': 0.0}
        
        # Execute
        start_time = time.time()
        run_process = await asyncio.create_subprocess_exec(
            exe_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(run_process.communicate(), timeout=5)
        execution_time = time.time() - start_time
        
        # Cleanup
        os.unlink(c_file)
        if os.path.exists(exe_file):
            os.unlink(exe_file)
        
        if stderr:
            return {'error': stderr.decode(), 'execution_time': execution_time}
        return {'output': stdout.decode(), 'execution_time': execution_time}
        
    except asyncio.TimeoutError:
        return {'error': 'Code execution timed out', 'execution_time': 0.0}
    except Exception as e:
        return {'error': str(e), 'execution_time': 0.0}

# Authentication Routes
@app.get("/login", response_class=FileResponse)
async def login_page():
    """Serve the login page"""
    html_path = CURRENT_DIR / "login.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Login page not found")
    return FileResponse(html_path, media_type="text/html")

@app.get("/auth/google")
async def google_login(request: Request):
    """Initiate Google OAuth login"""
    redirect_uri = GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = await get_google_user_info(token['access_token'])
        
        if not user_info:
            return RedirectResponse(url="/login?error=invalid_token")
        
        # Get or create user
        user = get_user_by_google_id(db, user_info['id'])
        if not user:
            # Check if user exists with same email
            existing_user = get_user_by_email(db, user_info['email'])
            if existing_user:
                return RedirectResponse(url="/login?error=email_exists")
            
            # Create new user
            user = create_user_from_google_data(user_info, db)
        
        # Update last login
        update_user_login(db, user.id)
        
        # Create access token
        access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        
        # Create session record
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + access_token_expires
        create_session(
            db=db,
            user_id=user.id,
            session_token=session_token,
            expires_at=expires_at,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent", "")
        )
        
        # Redirect to compiler with token
        response = RedirectResponse(url="/compiler?login=success")
        response.set_cookie(
            key="auth_token",
            value=access_token,
            max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        return response
        
    except Exception as e:
        print(f"OAuth callback error: {e}")
        return RedirectResponse(url="/login?error=server_error")

@app.post("/auth/logout")
async def logout(request: Request, user: User = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    """Logout user"""
    response = {"message": "Logged out successfully"}
    
    if user:
        # Deactivate sessions
        # This would need to be implemented in database.py
        pass
    
    # Clear cookie
    response_obj = RedirectResponse(url="/login", status_code=302)
    response_obj.delete_cookie("auth_token")
    return response_obj

@app.get("/api/verify-token")
async def verify_token(user: User = Depends(get_current_user_optional)):
    """Verify if the current token is valid"""
    if user:
        return {"valid": True, "user": user_to_dict(user)}
    else:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/me")
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current user information"""
    return user_to_dict(user)

# Main application routes
@app.get("/", response_class=RedirectResponse)
async def root():
    """Redirect to login page"""
    return RedirectResponse(url="/login")

@app.get("/compiler", response_class=FileResponse)
async def compiler_page():
    """Serve the compiler interface"""
    html_path = CURRENT_DIR / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Compiler interface not found")
    return FileResponse(html_path, media_type="text/html")

@app.post("/api/run", response_model=CodeResponse)
async def run_code(
    request: CodeRequest, 
    req: Request,
    user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Execute code in the specified language
    
    - **code**: The source code to execute
    - **language**: Programming language (python, c, cpp, java, kotlin, javascript, rust, sql, text)
    """
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="No code provided")
    
    # Security: Basic validation (only for Python)
    if request.language == 'python':
        dangerous_imports = ['os', 'subprocess', 'sys', 'eval', 'exec', '__import__']
        if any(dangerous in request.code for dangerous in dangerous_imports):
            raise HTTPException(status_code=400, detail="Potentially dangerous code detected")
    
    # Route to appropriate runner
    runners = {
        'python': run_python_code,
        'c': run_c_code,
        # Add other runners here (copy from original file)
    }
    
    runner = runners.get(request.language, run_python_code)
    
    # Handle async and sync runners
    if asyncio.iscoroutinefunction(runner):
        result = await runner(request.code)
    else:
        result = runner(request.code)
    
    # Log execution if user is authenticated
    if user:
        try:
            log_code_execution(
                db=db,
                user_id=user.id,
                language=request.language,
                code_snippet=request.code,
                output=result.get('output'),
                error_message=result.get('error'),
                execution_time=result.get('execution_time'),
                status='success' if not result.get('error') else 'error',
                ip_address=get_client_ip(req)
            )
        except Exception as e:
            print(f"Failed to log execution: {e}")
    
    return CodeResponse(**result)

@app.get("/api/languages")
async def get_supported_languages():
    """Get list of supported programming languages"""
    return {
        "languages": [
            {"id": "python", "name": "Python", "extension": ".py"},
            {"id": "c", "name": "C", "extension": ".c"},
            {"id": "cpp", "name": "C++", "extension": ".cpp"},
            {"id": "java", "name": "Java", "extension": ".java"},
            {"id": "kotlin", "name": "Kotlin", "extension": ".kt"},
            {"id": "javascript", "name": "JavaScript", "extension": ".js"},
            {"id": "rust", "name": "Rust", "extension": ".rs"},
            {"id": "sql", "name": "SQL", "extension": ".sql"},
            {"id": "text", "name": "Text", "extension": ".txt"}
        ]
    }

@app.get("/api/user/stats")
async def get_user_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user execution statistics"""
    from sqlalchemy import func
    from database import CodeExecution
    
    # Get total executions
    total_executions = db.query(CodeExecution).filter(CodeExecution.user_id == user.id).count()
    
    # Get languages used
    languages = db.query(CodeExecution.language).filter(
        CodeExecution.user_id == user.id
    ).distinct().all()
    languages_used = [lang[0] for lang in languages]
    
    # Get recent activity (last 10 executions)
    recent_activity = db.query(CodeExecution).filter(
        CodeExecution.user_id == user.id
    ).order_by(CodeExecution.created_at.desc()).limit(10).all()
    
    recent_list = []
    for activity in recent_activity:
        recent_list.append({
            "language": activity.language,
            "status": activity.status,
            "created_at": activity.created_at.isoformat(),
            "execution_time": float(activity.execution_time) if activity.execution_time else 0
        })
    
    return UserStats(
        total_executions=total_executions,
        languages_used=languages_used,
        recent_activity=recent_list
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Online Compiler API with Authentication is running"}

if __name__ == '__main__':
    import uvicorn
    print("🚀 Starting FastAPI Online Compiler with Authentication...")
    print("📋 Required setup:")
    print("   1. MySQL database running")
    print("   2. Google OAuth credentials in .env file")
    print("   3. Required compilers installed")
    print("\n📚 Documentation: http://localhost:8000/docs")
    print("🔐 Login page: http://localhost:8000/login")
    print("💻 Compiler: http://localhost:8000/compiler")
    
    uvicorn.run(
        "fastapi_compiler_auth:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
