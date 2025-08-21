"""
Scalable Online Compiler FastAPI Application
Designed to handle millions of concurrent users with MySQL and Redis
"""

from fastapi import FastAPI, Request, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
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
import json
import aioredis
from contextlib import asynccontextmanager

# Import our scalable auth and database modules
from scalable_auth import (
    register_user, authenticate_user, create_user_session, get_current_user_optional, 
    get_current_user, logout_user, user_to_dict, get_client_ip, check_rate_limit,
    UserRegister, UserLogin, Token, PasswordChange, create_env_file,
    limiter, get_redis
)
from scalable_database import (
    get_async_db, create_tables, User, log_code_execution_optimized, 
    get_user_stats_optimized, compress_code, decompress_code, hash_code,
    check_database_health, cleanup_expired_sessions
)

# Create environment file if it doesn't exist
create_env_file()

# Lifespan manager for startup/shutdown tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan with startup and shutdown tasks"""
    # Startup tasks
    print("🚀 Starting Online Compiler with Scalable Authentication...")
    
    # Initialize database tables
    try:
        await create_tables()
        print("✅ Database tables initialized successfully")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
    
    # Check database health
    if await check_database_health():
        print("✅ Database connection healthy")
    else:
        print("❌ Database connection issues detected")
    
    # Initialize Redis connection
    try:
        redis = await get_redis()
        await redis.ping()
        print("✅ Redis connection healthy")
    except Exception as e:
        print(f"⚠️  Redis connection warning: {e}")
    
    # Start background tasks
    background_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Shutdown tasks
    print("🛑 Shutting down application...")
    background_task.cancel()
    try:
        await background_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Scalable Online Compiler API",
    description="A high-performance web-based code compiler supporting millions of concurrent users",
    version="4.0.0",
    lifespan=lifespan
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class CodeRequest(BaseModel):
    code: str
    language: str

class CodeResponse(BaseModel):
    output: str = None
    error: str = None
    execution_time: float
    memory_used: Optional[int] = None
    cpu_time: Optional[float] = None

class UserStats(BaseModel):
    total_executions: int
    languages_used: list
    recent_activity: list

# Get the directory where this script is located
CURRENT_DIR = Path(__file__).parent

# Background tasks
async def periodic_cleanup():
    """Periodic cleanup of expired sessions and cache"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            
            # Cleanup expired sessions
            async for db in get_async_db():
                await cleanup_expired_sessions(db)
                break
                
            print("🧹 Periodic cleanup completed")
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"❌ Cleanup error: {e}")

# Code execution functions (optimized for high concurrency)
async def run_python_code(code: str) -> Dict[str, Any]:
    """Execute Python code safely with resource monitoring"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        start_time = time.time()
        start_cpu = time.process_time()
        
        process = await asyncio.create_subprocess_exec(
            'python3', temp_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
            execution_time = time.time() - start_time
            cpu_time = time.process_time() - start_cpu
            
            os.unlink(temp_file)
            
            if stderr:
                return {
                    'error': stderr.decode(), 
                    'execution_time': execution_time,
                    'cpu_time': cpu_time
                }
            return {
                'output': stdout.decode(), 
                'execution_time': execution_time,
                'cpu_time': cpu_time
            }
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            os.unlink(temp_file)
            return {
                'error': 'Code execution timed out (5s limit)', 
                'execution_time': 5.0,
                'cpu_time': 5.0
            }
            
    except Exception as e:
        return {'error': str(e), 'execution_time': 0.0, 'cpu_time': 0.0}

async def run_cpp_code(code: str) -> Dict[str, Any]:
    """Compile and execute C++ code with resource monitoring"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(code)
            cpp_file = f.name
        
        exe_file = cpp_file.replace('.cpp', '')
        
        # Compile
        compile_process = await asyncio.create_subprocess_exec(
            'g++', cpp_file, '-o', exe_file, '-O2', '-std=c++17',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(compile_process.communicate(), timeout=10)
        
        if compile_process.returncode != 0:
            os.unlink(cpp_file)
            return {'error': f'Compilation Error:\n{stderr.decode()}', 'execution_time': 0.0}
        
        # Execute with resource monitoring
        start_time = time.time()
        start_cpu = time.process_time()
        
        run_process = await asyncio.create_subprocess_exec(
            exe_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(run_process.communicate(), timeout=5)
        execution_time = time.time() - start_time
        cpu_time = time.process_time() - start_cpu
        
        # Cleanup
        os.unlink(cpp_file)
        if os.path.exists(exe_file):
            os.unlink(exe_file)
        
        if stderr:
            return {
                'error': stderr.decode(), 
                'execution_time': execution_time,
                'cpu_time': cpu_time
            }
        return {
            'output': stdout.decode(), 
            'execution_time': execution_time,
            'cpu_time': cpu_time
        }
        
    except asyncio.TimeoutError:
        return {'error': 'Code execution timed out', 'execution_time': 0.0}
    except Exception as e:
        return {'error': str(e), 'execution_time': 0.0}

# Authentication Routes
@app.get("/auth", response_class=FileResponse)
async def auth_page():
    """Serve the authentication page"""
    html_path = CURRENT_DIR / "auth.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Authentication page not found")
    return FileResponse(html_path, media_type="text/html")

@app.get("/login", response_class=FileResponse)
async def login_redirect():
    """Redirect to auth page"""
    html_path = CURRENT_DIR / "auth.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Authentication page not found")
    return FileResponse(html_path, media_type="text/html")

@app.post("/auth/register", response_model=Token)
@limiter.limit("3/minute")
async def register_endpoint(
    request: Request,
    user_data: UserRegister,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    """Register a new user"""
    try:
        user = await register_user(user_data, request, db)
        access_token, refresh_token, expires_in = await create_user_session(
            user, request, False, db
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                first_name=user.first_name,
                last_name=user.last_name,
                profile_picture=user.profile_picture,
                email_verified=user.email_verified,
                user_role=user.user_role,
                created_at=user.created_at,
                last_login=user.last_login
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/auth/login", response_model=Token)
@limiter.limit("5/minute")
async def login_endpoint(
    request: Request,
    login_data: UserLogin,
    db: AsyncSession = Depends(get_async_db)
):
    """Authenticate user and return tokens"""
    try:
        user = await authenticate_user(login_data, request, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        access_token, refresh_token, expires_in = await create_user_session(
            user, request, login_data.remember_me, db
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                first_name=user.first_name,
                last_name=user.last_name,
                profile_picture=user.profile_picture,
                email_verified=user.email_verified,
                user_role=user.user_role,
                created_at=user.created_at,
                last_login=user.last_login
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@app.post("/auth/logout")
async def logout_endpoint(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Logout user"""
    try:
        # Get session ID from token
        from scalable_auth import verify_token
        
        auth_header = request.headers.get("authorization")
        if auth_header:
            token = auth_header.split(" ")[1]
            payload = verify_token(token)
            if payload:
                session_id = payload.get("session_id")
                if session_id:
                    await logout_user(session_id, db)
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@app.get("/auth/verify")
async def verify_token_endpoint(user: User = Depends(get_current_user)):
    """Verify if the current token is valid"""
    return {"valid": True, "user": user_to_dict(user)}

@app.get("/api/me")
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current user information"""
    return user_to_dict(user)

# Main application routes
@app.get("/", response_class=FileResponse)
async def root():
    """Redirect to authentication page"""
    html_path = CURRENT_DIR / "auth.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Authentication page not found")
    return FileResponse(html_path, media_type="text/html")

@app.get("/compiler", response_class=FileResponse)
async def compiler_page():
    """Serve the compiler interface"""
    html_path = CURRENT_DIR / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Compiler interface not found")
    return FileResponse(html_path, media_type="text/html")

@app.post("/api/run", response_model=CodeResponse)
@limiter.limit("30/minute")
async def run_code_endpoint(
    request: Request,
    code_request: CodeRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Execute code with rate limiting and logging"""
    
    if not code_request.code.strip():
        raise HTTPException(status_code=400, detail="No code provided")
    
    # Get client info
    ip_address = get_client_ip(request)
    
    # Additional rate limiting for anonymous users
    if not user:
        redis = await get_redis()
        key = f"anon_executions:{ip_address}"
        count = await redis.get(key)
        if count and int(count) >= 10:  # 10 executions per hour for anonymous users
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded for anonymous users. Please sign in for higher limits."
            )
        await redis.incr(key)
        await redis.expire(key, 3600)
    
    # Security: Basic validation
    if code_request.language == 'python':
        dangerous_patterns = ['os.', 'subprocess', 'sys.', 'eval(', 'exec(', '__import__']
        if any(pattern in code_request.code for pattern in dangerous_patterns):
            raise HTTPException(status_code=400, detail="Potentially dangerous code detected")
    
    # Route to appropriate runner
    runners = {
        'python': run_python_code,
        'cpp': run_cpp_code,
        # Add more runners as needed
    }
    
    runner = runners.get(code_request.language, run_python_code)
    
    # Execute code
    try:
        result = await runner(code_request.code)
    except Exception as e:
        result = {'error': str(e), 'execution_time': 0.0}
    
    # Log execution if user is authenticated
    if user:
        background_tasks.add_task(
            log_execution_async,
            db,
            user.id,
            code_request.language,
            code_request.code,
            result,
            ip_address
        )
    
    return CodeResponse(
        output=result.get('output'),
        error=result.get('error'),
        execution_time=result.get('execution_time', 0.0),
        memory_used=result.get('memory_used'),
        cpu_time=result.get('cpu_time')
    )

async def log_execution_async(db: AsyncSession, user_id: int, language: str, 
                            code: str, result: dict, ip_address: str):
    """Background task to log code execution"""
    try:
        # Get session ID from current context if available
        session_id = "unknown"  # This would come from the request context in a real implementation
        
        status = 'success' if not result.get('error') else 'error'
        if 'timed out' in str(result.get('error', '')):
            status = 'timeout'
        
        await log_code_execution_optimized(
            db=db,
            user_id=user_id,
            session_id=session_id,
            language=language,
            code=code,
            output=result.get('output'),
            error_message=result.get('error'),
            execution_time=result.get('execution_time'),
            memory_used=result.get('memory_used'),
            cpu_time=result.get('cpu_time'),
            status=status,
            ip_address=ip_address
        )
    except Exception as e:
        print(f"Failed to log execution: {e}")

@app.get("/api/languages")
async def get_supported_languages():
    """Get list of supported programming languages"""
    return {
        "languages": [
            {"id": "python", "name": "Python", "extension": ".py"},
            {"id": "cpp", "name": "C++", "extension": ".cpp"},
            {"id": "c", "name": "C", "extension": ".c"},
            {"id": "java", "name": "Java", "extension": ".java"},
            {"id": "javascript", "name": "JavaScript", "extension": ".js"},
            {"id": "rust", "name": "Rust", "extension": ".rs"},
            {"id": "go", "name": "Go", "extension": ".go"},
        ]
    }

@app.get("/api/user/stats")
async def get_user_stats_endpoint(
    user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_async_db)
):
    """Get user execution statistics"""
    try:
        stats = await get_user_stats_optimized(db, user.id)
        return UserStats(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user stats: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Check database
        db_healthy = await check_database_health()
        
        # Check Redis
        redis_healthy = False
        try:
            redis = await get_redis()
            await redis.ping()
            redis_healthy = True
        except Exception:
            pass
        
        return {
            "status": "healthy" if db_healthy and redis_healthy else "degraded",
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
            "version": "4.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/metrics")
async def get_metrics():
    """Basic metrics endpoint for monitoring"""
    try:
        redis = await get_redis()
        
        # Get cached stats
        total_users = await redis.get("stats:total_users") or "0"
        active_users = await redis.get("stats:active_users_today") or "0"
        total_executions = await redis.get("stats:total_executions") or "0"
        
        return {
            "total_users": int(total_users),
            "active_users_today": int(active_users),
            "total_executions": int(total_executions),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

# Import UserResponse for type hints
from scalable_auth import UserResponse

if __name__ == '__main__':
    import uvicorn
    print("🚀 Starting Scalable Online Compiler...")
    print("📋 System Requirements:")
    print("   ✅ MySQL 8.0+ with optimized configuration")
    print("   ✅ Redis for session storage and caching")
    print("   ✅ Connection pooling configured")
    print("   ✅ Rate limiting enabled")
    print("\n🔧 Endpoints:")
    print("   🔐 Authentication: http://localhost:8000/auth")
    print("   💻 Compiler: http://localhost:8000/compiler")
    print("   📚 API Docs: http://localhost:8000/docs")
    print("   📊 Health: http://localhost:8000/health")
    print("   📈 Metrics: http://localhost:8000/metrics")
    
    uvicorn.run(
        "scalable_compiler_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        workers=1  # Use multiple workers in production
    )
