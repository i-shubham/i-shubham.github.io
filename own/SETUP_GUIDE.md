# Online Compiler with Google Authentication - Setup Guide

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **MySQL 8.0+** running
3. **Google Cloud Console** account for OAuth setup
4. **Required compilers** (gcc, g++, java, node, etc.)

## 🗄️ Database Setup

### 1. Install and Start MySQL

```bash
# On macOS with Homebrew
brew install mysql
brew services start mysql

# On Ubuntu/Debian
sudo apt install mysql-server
sudo systemctl start mysql

# On Windows
# Download and install MySQL from official website
```

### 2. Create Database and User

```bash
# Login to MySQL as root
mysql -u root -p

# Create database and user
CREATE DATABASE online_compiler_db;
CREATE USER 'compiler_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON online_compiler_db.* TO 'compiler_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Run Database Schema

```bash
mysql -u compiler_user -p online_compiler_db < database_schema.sql
```

## 🔑 Google OAuth Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API

### 2. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth 2.0 Client IDs**
3. Choose **Web application**
4. Add authorized redirect URIs:
   - `http://localhost:8000/auth/callback`
   - `http://127.0.0.1:8000/auth/callback`
5. Save your **Client ID** and **Client Secret**

## ⚙️ Application Setup

### 1. Install Dependencies

```bash
# Navigate to the project directory
cd own/

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Create Environment File

Create a `.env` file with your configuration:

```env
# Database Configuration
DATABASE_URL=mysql+pymysql://compiler_user:your_secure_password@localhost/online_compiler_db

# JWT Configuration - Generate using: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-generated-secret-key-here

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Optional: Redis for session storage
REDIS_URL=redis://localhost:6379/0
```

### 3. Generate Secret Key

```bash
# Generate a secure secret key
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
```

## 🚀 Running the Application

### 1. Start the FastAPI Server

```bash
# Using the new authentication-enabled server
python fastapi_compiler_auth.py

# Or using uvicorn directly
uvicorn fastapi_compiler_auth:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Access the Application

- **Login Page**: http://localhost:8000/login
- **Compiler**: http://localhost:8000/compiler
- **API Docs**: http://localhost:8000/docs

## 📝 Features

### ✅ Authentication Features
- Google OAuth 2.0 login
- User profile management
- Session handling
- Guest mode (limited functionality)

### ✅ Compiler Features
- Multi-language support (Python, C/C++, Java, JavaScript, Rust, SQL)
- Code execution with output display
- Execution time tracking
- Error handling and security

### ✅ User Features
- Code execution history
- User statistics and analytics
- Personalized dashboard
- Activity tracking

## 🛠️ Required Compilers

Make sure you have these compilers installed:

```bash
# Python
python3 --version

# C/C++
gcc --version
g++ --version

# Java
javac -version
java -version

# JavaScript (Node.js)
node --version

# Rust (optional)
cargo --version

# Kotlin (optional)
kotlinc -version
```

## 🔧 Troubleshooting

### Database Connection Issues
- Check MySQL service is running
- Verify database credentials in `.env`
- Ensure database and user exist

### Google OAuth Issues
- Verify Google Client ID/Secret in `.env`
- Check redirect URI matches Google Console
- Ensure Google+ API is enabled

### Compiler Issues
- Install missing compilers
- Check PATH environment variable
- Verify permissions for code execution

## 📚 API Endpoints

### Authentication
- `GET /login` - Login page
- `GET /auth/google` - Initiate Google OAuth
- `GET /auth/callback` - OAuth callback
- `POST /auth/logout` - Logout
- `GET /api/verify-token` - Verify token
- `GET /api/me` - Current user info

### Compiler
- `POST /api/run` - Execute code
- `GET /api/languages` - Supported languages
- `GET /api/user/stats` - User statistics

## 🔐 Security Features

- JWT token authentication
- SQL injection prevention
- Code execution sandboxing
- Input validation
- Session management
- HTTPS ready (configure reverse proxy)

## 📊 Database Tables

- `users` - User profiles from Google OAuth
- `user_sessions` - Active user sessions
- `code_executions` - Code execution history
- `user_preferences` - User settings
- `saved_snippets` - Saved code snippets
- `questions` - Coding problems
- `question_attempts` - User problem attempts

## 🚀 Production Deployment

### 1. Security Settings
```env
SECRET_KEY=your-super-secure-32-byte-key
DATABASE_URL=mysql+pymysql://user:password@production-db:3306/database
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/callback
```

### 2. Use Production WSGI Server
```bash
pip install gunicorn
gunicorn fastapi_compiler_auth:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 3. Configure Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📞 Support

If you encounter any issues:

1. Check the console for error messages
2. Verify all prerequisites are installed
3. Ensure `.env` file is configured correctly
4. Check database connectivity
5. Verify Google OAuth setup

Happy Coding! 🎉
