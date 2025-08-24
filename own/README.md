# Online Compiler - FastAPI Backend

A simple FastAPI backend for the online compiler with user authentication.

## Setup

1. **Database Setup**:
   - Ensure MySQL is running
   - Create database: `CREATE DATABASE online_compiler_auth;`
   - Update `db_config.py` with your MySQL credentials
   - Test connection: `python db_config.py`

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Run the Server

From the `own` directory:
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Access Points

- **Authentication Page**: http://localhost:8000/auth
- **Compiler Page**: http://localhost:8000/compiler_index.html
- **API Documentation**: http://localhost:8000/docs

## Features

- User registration and login
- JWT token authentication
- Code execution (simulated)
- User statistics tracking
- Simple in-memory storage

## API Endpoints

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/verify` - Verify token
- `POST /auth/logout` - User logout
- `POST /api/run` - Execute code
- `GET /api/user/stats` - Get user statistics

## Notes

- This is a production-ready implementation with MySQL database
- User data is persistently stored in MySQL
- Code execution is simulated for security
- In production, use proper sandboxing for code execution
- Database connection is automatically initialized on startup
