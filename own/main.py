from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import bcrypt
import jwt
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List
import mysql.connector
from mysql.connector import Error

# Initialize FastAPI app
app = FastAPI(title="Online Compiler API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Import database configuration
from db_config import DB_CONFIG

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    first_name: str
    last_name: str

class UserLogin(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class CodeExecution(BaseModel):
    code: str
    language: str

class User(BaseModel):
    username: str
    email: str
    full_name: str
    first_name: str
    last_name: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# Database connection functions
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_database():
    """Initialize database tables if they don't exist"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Create users table if it doesn't exist
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL,
            INDEX idx_username (username),
            INDEX idx_email (email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        cursor.execute(create_users_table)
        
        # Check if questions tables already exist
        cursor.execute("SHOW TABLES LIKE 'main_categories'")
        questions_tables_exist = cursor.fetchone() is not None
        
        if not questions_tables_exist:
            print("📚 Questions tables not found. Please run the schema.sql file first.")
            print("💡 You can run: mysql -u your_username -p online_compiler_auth < schema.sql")
        else:
            print("✅ Questions tables already exist")
        
        connection.commit()
        print("✅ Database initialized successfully")
        return True
        
    except Error as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Utility functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def hash_password(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password: str, hashed_password: str):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# Database user functions
def create_user_in_db(user_data: dict):
    """Create a new user in the database"""
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        
        insert_query = """
        INSERT INTO users (username, email, password_hash, full_name, first_name, last_name)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            user_data["username"],
            user_data["email"],
            user_data["password_hash"],
            user_data["full_name"],
            user_data["first_name"],
            user_data["last_name"]
        ))
        
        connection.commit()
        return True
        
    except Error as e:
        if "Duplicate entry" in str(e):
            if "username" in str(e):
                raise HTTPException(status_code=400, detail="Username already registered")
            elif "email" in str(e):
                raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_user_by_username_or_email(username_or_email: str):
    """Get user by username or email from database"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        select_query = """
        SELECT id, username, email, password_hash, full_name, first_name, last_name, is_active
        FROM users 
        WHERE username = %s OR email = %s
        """
        
        cursor.execute(select_query, (username_or_email, username_or_email))
        user = cursor.fetchone()
        
        return user
        
    except Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_last_login(user_id: int):
    """Update user's last login timestamp"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        update_query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s"
        cursor.execute(update_query, (user_id,))
        connection.commit()
        return True
        
    except Error as e:
        print(f"Error updating last login: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/auth")

@app.get("/auth", response_class=HTMLResponse)
async def auth_page():
    with open("auth.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/compiler_index.html", response_class=HTMLResponse)
async def compiler_page():
    print("\n\ncompiler_page\n\n")
    with open("compilar_index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/auth/register", response_model=Token)
async def register(user: UserCreate):
    # Check if username already exists
    existing_user = get_user_by_username_or_email(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    existing_user = get_user_by_username_or_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(user.password)
    
    # Prepare user data
    user_data = {
        "username": user.username,
        "email": user.email,
        "password_hash": hashed_password.decode('utf-8'),
        "full_name": user.full_name,
        "first_name": user.first_name,
        "last_name": user.last_name
    }
    
    # Create user in database
    try:
        create_user_in_db(user_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create user")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            first_name=user.first_name,
            last_name=user.last_name
        )
    )

@app.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    # Get user from database
    user = get_user_by_username_or_email(user_credentials.username)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Check if user is active
    if not user["is_active"]:
        raise HTTPException(status_code=401, detail="Account is deactivated")
    
    # Verify password
    if not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Update last login
    update_last_login(user["id"])
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=User(
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            first_name=user["first_name"],
            last_name=user["last_name"]
        )
    )

@app.post("/auth/verify")
async def verify_token_endpoint(username: str = Depends(verify_token)):
    user = get_user_by_username_or_email(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user["is_active"]:
        raise HTTPException(status_code=401, detail="Account is deactivated")
    
    return {
        "user": User(
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            first_name=user["first_name"],
            last_name=user["last_name"]
        )
    }

@app.post("/auth/logout")
async def logout(username: str = Depends(verify_token)):
    # In a real application, you might want to blacklist the token
    return {"message": "Successfully logged out"}

@app.post("/api/run")
async def run_code(code_execution: CodeExecution, username: Optional[str] = Depends(verify_token)):
    code = code_execution.code
    language = code_execution.language
    
    # Simple code execution simulation
    try:
        if language == "python":
            # Very basic Python execution (in production, use proper sandboxing)
            if "import os" in code or "import sys" in code or "import subprocess" in code:
                return {"error": "Security: Restricted imports not allowed"}
            
            # Execute Python code
            local_vars = {}
            exec(code, {"__builtins__": {}}, local_vars)
            
            # Capture output (this is simplified)
            output = "Code executed successfully"
            if "print" in code:
                output = "Code executed with print statements"
            
        elif language == "javascript":
            output = "JavaScript execution simulated"
        elif language == "cpp":
            output = "C++ compilation simulated"
        elif language == "java":
            output = "Java compilation simulated"
        else:
            output = f"{language.capitalize()} execution simulated"
        
        return {
            "output": output,
            "execution_time": 0.1,
            "language": language
        }
        
    except Exception as e:
        error_msg = str(e)
        return {"error": error_msg, "execution_time": 0.05}

@app.get("/api/user/stats")
async def get_user_stats(username: str = Depends(verify_token)):
    # For now, return basic stats (you can extend this with database queries)
    return {
        "total_executions": 0,
        "languages_used": [],
        "recent_activity": []
    }

# Question-related endpoints
@app.get("/api/questions/subcategories")
async def get_subcategories(main_category: str):
    """Get subcategories for a main category"""
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        
        # Get subcategories for the main category
        query = """
        SELECT sc.name 
        FROM subcategories sc
        JOIN main_categories mc ON sc.main_category_id = mc.id
        WHERE mc.name = %s
        ORDER BY sc.name
        """
        
        cursor.execute(query, (main_category,))
        subcategories = [row[0] for row in cursor.fetchall()]
        
        return subcategories
        
    except Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.get("/api/questions")
async def get_questions(main_category: str, sub_category: str):
    """Get questions for a specific category and subcategory"""
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get questions for the category and subcategory
        query = """
        SELECT q.id, q.title, q.description, q.difficulty, q.tags
        FROM questions q
        JOIN main_categories mc ON q.main_category_id = mc.id
        JOIN subcategories sc ON q.subcategory_id = sc.id
        WHERE mc.name = %s AND sc.name = %s
        ORDER BY q.difficulty, q.title
        """
        
        cursor.execute(query, (main_category, sub_category))
        questions = cursor.fetchall()
        
        return questions
        
    except Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.get("/api/questions/{question_id}")
async def get_question(question_id: int):
    """Get a specific question by ID"""
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get question by ID
        query = """
        SELECT q.id, q.title, q.description, q.content, q.difficulty, q.tags,
               mc.name as main_category, sc.name as subcategory
        FROM questions q
        JOIN main_categories mc ON q.main_category_id = mc.id
        JOIN subcategories sc ON q.subcategory_id = sc.id
        WHERE q.id = %s
        """
        
        cursor.execute(query, (question_id,))
        question = cursor.fetchone()
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        return question
        
    except Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.get("/docs", response_class=HTMLResponse)
async def api_docs():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }
            h2 { color: #555; margin-top: 30px; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
            .method { background: #007bff; color: white; padding: 4px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }
            .url { font-family: monospace; background: #e9ecef; padding: 8px; border-radius: 3px; margin: 10px 0; }
            code { background: #e9ecef; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Online Compiler API Documentation</h1>
            
            <h2>Authentication Endpoints</h2>
            
            <div class="endpoint">
                <span class="method">POST</span>
                <div class="url">/auth/register</div>
                <p>Register a new user account</p>
                <strong>Body:</strong> username, email, password, full_name, first_name, last_name
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span>
                <div class="url">/auth/login</div>
                <p>Login with username/email and password</p>
                <strong>Body:</strong> username, password, remember_me (optional)
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span>
                <div class="url">/auth/verify</div>
                <p>Verify authentication token</p>
                <strong>Headers:</strong> Authorization: Bearer {token}
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span>
                <div class="url">/auth/logout</div>
                <p>Logout user</p>
                <strong>Headers:</strong> Authorization: Bearer {token}
            </div>
            
            <h2>Code Execution Endpoints</h2>
            
            <div class="endpoint">
                <span class="method">POST</span>
                <div class="url">/api/run</div>
                <p>Execute code in specified language</p>
                <strong>Body:</strong> code, language
                <strong>Headers:</strong> Authorization: Bearer {token} (optional)
            </div>
            
            <h2>User Statistics Endpoints</h2>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <div class="url">/api/user/stats</div>
                <p>Get user's coding statistics</p>
                <strong>Headers:</strong> Authorization: Bearer {token}
            </div>
            
            <h2>Page Endpoints</h2>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <div class="url">/auth</div>
                <p>Authentication page</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <div class="url">/compiler_index.html</div>
                <p>Online compiler interface</p>
            </div>
            
            <h2>Supported Languages</h2>
            <p>The compiler supports: <code>python</code>, <code>javascript</code>, <code>cpp</code>, <code>c</code>, <code>java</code>, <code>kotlin</code>, <code>rust</code>, <code>sql</code>, <code>text</code></p>
            
            <h2>Usage Examples</h2>
            <p><strong>Login:</strong> POST to <code>/auth/login</code> with username and password</p>
            <p><strong>Run Code:</strong> POST to <code>/api/run</code> with code and language</p>
            <p><strong>Get Stats:</strong> GET <code>/api/user/stats</code> with Bearer token</p>
        </div>
    </body>
    </html>
    """

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting Online Compiler API...")
    print("🗄️ Initializing database connection...")
    
    if init_database():
        print("✅ Database initialized successfully")
    else:
        print("❌ Failed to initialize database")
        print("⚠️ Please check your MySQL connection settings")

if __name__ == "__main__":
    import uvicorn
    print("🔑 Register/Login to access full features")
    uvicorn.run(app, host="0.0.0.0", port=8000)
