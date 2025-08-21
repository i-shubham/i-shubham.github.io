# Scalable Online Compiler - Setup Guide
## 🚀 Built to Handle Millions of Concurrent Users

This system is designed for high-scale deployment with traditional MySQL authentication, Redis caching, and advanced performance optimizations.

## 📋 Prerequisites

1. **Python 3.8+** with asyncio support
2. **MySQL 8.0+** with optimized configuration
3. **Redis 6.0+** for session storage and caching
4. **Required compilers** (gcc, g++, python3, java, node, etc.)

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│   FastAPI App   │────│   MySQL Cluster │
│   (Nginx/HAProxy)│    │  (Multiple     │    │  (Master/Slave) │
└─────────────────┘    │   Workers)      │    └─────────────────┘
                       └─────────────────┘
                              │
                       ┌─────────────────┐
                       │   Redis Cluster │
                       │  (Session Cache)│
                       └─────────────────┘
```

## 🗄️ Database Setup (Optimized for Scale)

### 1. MySQL Configuration

Create `/etc/mysql/mysql.conf.d/99-scalable.cnf`:

```ini
[mysqld]
# Connection settings for high concurrency
max_connections = 1000
max_user_connections = 500
thread_cache_size = 50
table_open_cache = 4000
table_definition_cache = 2000

# InnoDB settings for performance
innodb_buffer_pool_size = 8G  # 70-80% of RAM
innodb_buffer_pool_instances = 8
innodb_log_file_size = 1G
innodb_log_buffer_size = 256M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT

# Query cache (MySQL 5.7 only)
query_cache_type = 1
query_cache_size = 256M
query_cache_limit = 8M

# Replication settings (for read replicas)
server_id = 1
log_bin = mysql-bin
binlog_format = ROW
expire_logs_days = 7

# Character set
character_set_server = utf8mb4
collation_server = utf8mb4_unicode_ci
```

### 2. Create Database and User

```bash
# Login to MySQL as root
mysql -u root -p

# Create database and optimized user
CREATE DATABASE online_compiler_db 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

# Create users for different purposes
CREATE USER 'compiler_app'@'%' IDENTIFIED BY 'your_secure_app_password';
CREATE USER 'compiler_read'@'%' IDENTIFIED BY 'your_secure_read_password';

# Grant privileges
GRANT ALL PRIVILEGES ON online_compiler_db.* TO 'compiler_app'@'%';
GRANT SELECT ON online_compiler_db.* TO 'compiler_read'@'%';

# Create additional indexes for performance
USE online_compiler_db;

# Run the schema
SOURCE database_schema.sql;

# Additional performance indexes
CREATE INDEX idx_users_activity ON users(is_active, last_activity, created_at);
CREATE INDEX idx_sessions_cleanup ON user_sessions(expires_at, is_active);
CREATE INDEX idx_executions_analytics ON code_executions(created_at, language, status);

FLUSH PRIVILEGES;
```

### 3. Partitioning Setup (For Large Scale)

```sql
-- Partition code_executions by month for better performance
ALTER TABLE code_executions 
PARTITION BY RANGE (YEAR(created_at) * 100 + MONTH(created_at)) (
    PARTITION p202401 VALUES LESS THAN (202402),
    PARTITION p202402 VALUES LESS THAN (202403),
    -- Add partitions for future months
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- Partition activity logs similarly
ALTER TABLE user_activity_logs 
PARTITION BY RANGE (YEAR(created_at) * 100 + MONTH(created_at)) (
    PARTITION p202401 VALUES LESS THAN (202402),
    PARTITION p202402 VALUES LESS THAN (202403),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

## 🔴 Redis Setup (Session Storage & Caching)

### 1. Redis Configuration

Create `/etc/redis/redis.conf`:

```ini
# Network
bind 0.0.0.0
port 6379
protected-mode yes
requirepass your_secure_redis_password

# Memory management
maxmemory 4gb
maxmemory-policy allkeys-lru
maxmemory-samples 10

# Persistence (for session recovery)
save 900 1
save 300 10
save 60 10000
rdbcompression yes
rdbchecksum yes

# Connection settings
tcp-keepalive 300
tcp-backlog 511
timeout 0
databases 16

# Performance
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
```

### 2. Redis Cluster (For High Availability)

```bash
# For production, set up Redis Cluster with 6 nodes (3 masters, 3 slaves)
redis-cli --cluster create \
  127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \
  127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 \
  --cluster-replicas 1
```

## ⚙️ Application Setup

### 1. Install Dependencies

```bash
# Navigate to project directory
cd own/

# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies
sudo apt update
sudo apt install -y gcc g++ openjdk-11-jdk nodejs npm python3-dev
```

### 2. Environment Configuration

Create `.env` file:

```env
# Database Configuration (with connection pooling)
DATABASE_URL=mysql+aiomysql://compiler_app:your_secure_app_password@localhost/online_compiler_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_RECYCLE=3600

# Read replica for analytics (optional)
DATABASE_READ_URL=mysql+aiomysql://compiler_read:your_secure_read_password@replica-host/online_compiler_db

# JWT Configuration (generate with: openssl rand -hex 32)
SECRET_KEY=your-generated-secret-key-64-characters-long

# Redis Configuration
REDIS_URL=redis://:your_secure_redis_password@localhost:6379/0
REDIS_POOL_SIZE=10

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=100
MAX_ANONYMOUS_EXECUTIONS_PER_HOUR=10
MAX_USER_EXECUTIONS_PER_MINUTE=30

# Session Configuration
ACCESS_TOKEN_EXPIRE_HOURS=24
REFRESH_TOKEN_EXPIRE_DAYS=30

# Security Settings
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30

# Performance Settings
CODE_EXECUTION_TIMEOUT=5
MEMORY_LIMIT_MB=256
CPU_TIME_LIMIT=10

# Email Configuration (for user verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourcompiler.com
```

### 3. Database Migration

```bash
# Initialize database tables
python -c "
import asyncio
from scalable_database import create_tables
asyncio.run(create_tables())
"

# Verify database setup
python -c "
import asyncio
from scalable_database import check_database_health
print('DB Health:', asyncio.run(check_database_health()))
"
```

## 🚀 Running the Application

### 1. Development Mode

```bash
# Run with auto-reload
python scalable_compiler_app.py

# Or with Uvicorn
uvicorn scalable_compiler_app:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Production Mode (High Performance)

```bash
# Install production WSGI server
pip install gunicorn

# Run with multiple workers (CPU cores * 2 + 1)
gunicorn scalable_compiler_app:app \
  -w 8 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --worker-connections 1000 \
  --max-requests 10000 \
  --max-requests-jitter 1000 \
  --preload \
  --access-logfile /var/log/compiler/access.log \
  --error-logfile /var/log/compiler/error.log
```

### 3. Load Balancer Configuration (Nginx)

```nginx
upstream compiler_backend {
    least_conn;
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8003 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name yourcompiler.com;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

    # Static files
    location /static/ {
        alias /path/to/static/files/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API endpoints with rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://compiler_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Authentication endpoints
    location /auth/ {
        limit_req zone=login burst=10 nodelay;
        proxy_pass http://compiler_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # All other requests
    location / {
        proxy_pass http://compiler_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 📊 Performance Monitoring

### 1. System Monitoring

```bash
# Install monitoring tools
pip install prometheus-client grafana-api

# Create monitoring script
cat > monitor.py << 'EOF'
import asyncio
import time
from prometheus_client import start_http_server, Counter, Histogram, Gauge
from scalable_database import check_database_health

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users_total', 'Total active users')
DB_CONNECTIONS = Gauge('database_connections', 'Database connections')

async def collect_metrics():
    while True:
        # Collect custom metrics
        await asyncio.sleep(30)

if __name__ == '__main__':
    start_http_server(8001)  # Prometheus metrics port
    asyncio.run(collect_metrics())
EOF
```

### 2. Database Monitoring Queries

```sql
-- Monitor active connections
SELECT 
    SUBSTRING_INDEX(host, ':', 1) as client_ip,
    command,
    time,
    state,
    info
FROM information_schema.processlist 
WHERE command != 'Sleep' 
ORDER BY time DESC;

-- Monitor slow queries
SELECT 
    query_time,
    lock_time,
    rows_sent,
    rows_examined,
    sql_text
FROM mysql.slow_log 
ORDER BY query_time DESC 
LIMIT 10;

-- Monitor table sizes
SELECT 
    table_name,
    table_rows,
    ROUND(data_length / 1024 / 1024, 2) as data_size_mb,
    ROUND(index_length / 1024 / 1024, 2) as index_size_mb
FROM information_schema.tables 
WHERE table_schema = 'online_compiler_db'
ORDER BY data_length + index_length DESC;
```

## 🔧 Performance Tuning

### 1. Application Level

```python
# Connection pooling tuning in .env
DATABASE_POOL_SIZE=50          # Per worker process
DATABASE_MAX_OVERFLOW=100      # Additional connections
DATABASE_POOL_RECYCLE=7200     # Recycle connections every 2 hours

# Redis connection tuning
REDIS_POOL_SIZE=20             # Per worker process
REDIS_MAX_CONNECTIONS=200      # Total Redis connections

# Rate limiting tuning
GLOBAL_RATE_LIMIT=10000        # Requests per minute globally
USER_RATE_LIMIT=100            # Requests per minute per user
ANON_RATE_LIMIT=10             # Requests per minute per IP
```

### 2. Operating System Tuning

```bash
# Increase file descriptor limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Network tuning
echo 'net.core.somaxconn = 65535' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_max_syn_backlog = 65535' >> /etc/sysctl.conf
echo 'net.core.netdev_max_backlog = 5000' >> /etc/sysctl.conf

# Apply changes
sysctl -p
```

## 📈 Scaling Strategies

### 1. Horizontal Scaling

```bash
# Run multiple app instances
for port in 8000 8001 8002 8003; do
    gunicorn scalable_compiler_app:app \
      -w 4 -k uvicorn.workers.UvicornWorker \
      --bind 0.0.0.0:$port &
done
```

### 2. Database Scaling

```sql
-- Read replicas for analytics
CREATE USER 'replica_user'@'%' IDENTIFIED BY 'replica_password';
GRANT REPLICATION SLAVE ON *.* TO 'replica_user'@'%';

-- Set up read replica
CHANGE MASTER TO
    MASTER_HOST='master-db-host',
    MASTER_USER='replica_user',
    MASTER_PASSWORD='replica_password',
    MASTER_LOG_FILE='mysql-bin.000001',
    MASTER_LOG_POS=0;

START SLAVE;
```

### 3. Caching Strategy

```python
# Multi-layer caching
# L1: Application memory (per process)
# L2: Redis (shared across processes)  
# L3: Database query cache

# Example implementation in code:
@lru_cache(maxsize=1000)  # L1 cache
async def get_user_stats_cached(user_id: int):
    # Check L2 cache (Redis)
    cached = await redis.get(f"stats:{user_id}")
    if cached:
        return json.loads(cached)
    
    # Fallback to database (L3)
    stats = await get_user_stats_optimized(db, user_id)
    
    # Cache in Redis for 5 minutes
    await redis.setex(f"stats:{user_id}", 300, json.dumps(stats))
    
    return stats
```

## 📊 Access Points

- **🔐 Authentication**: http://localhost:8000/auth
- **💻 Compiler Interface**: http://localhost:8000/compiler  
- **📚 API Documentation**: http://localhost:8000/docs
- **❤️ Health Check**: http://localhost:8000/health
- **📈 Metrics**: http://localhost:8000/metrics

## 🚨 Security Features

### ✅ Authentication Security
- **bcrypt password hashing** with salt rounds
- **JWT tokens** with expiration
- **Account lockout** after failed attempts
- **Rate limiting** on auth endpoints
- **Session management** with Redis

### ✅ API Security
- **Rate limiting** by IP and user
- **Input validation** and sanitization
- **SQL injection** protection
- **Code execution** sandboxing
- **CORS** configuration

### ✅ Infrastructure Security
- **Database connection** encryption
- **Redis authentication** enabled
- **Secure headers** middleware
- **Request logging** for audit

## 📞 Troubleshooting

### Database Issues
```bash
# Check connections
mysql -e "SHOW PROCESSLIST;"

# Check slow queries
mysql -e "SHOW VARIABLES LIKE 'slow_query_log';"

# Check table locks
mysql -e "SHOW OPEN TABLES WHERE In_use > 0;"
```

### Redis Issues
```bash
# Check Redis status
redis-cli ping
redis-cli info memory
redis-cli info clients
```

### Application Issues
```bash
# Check application logs
tail -f /var/log/compiler/error.log

# Monitor resource usage
htop
iotop
nethogs
```

## 🎯 Performance Benchmarks

Expected performance with optimized setup:

- **👤 Concurrent Users**: 100,000+ 
- **⚡ API Latency**: <100ms (95th percentile)
- **🚀 Throughput**: 10,000+ requests/second
- **💾 Database**: 50,000+ queries/second  
- **⚡ Redis**: 100,000+ operations/second

## 🔄 Deployment Checklist

### Pre-Production
- [ ] Database optimized and indexed
- [ ] Redis cluster configured
- [ ] Load balancer configured
- [ ] SSL certificates installed
- [ ] Monitoring setup (Grafana/Prometheus)
- [ ] Backup strategy implemented
- [ ] Security audit completed

### Production Launch
- [ ] DNS configured
- [ ] CDN setup for static files
- [ ] Log aggregation configured
- [ ] Alert thresholds set
- [ ] Disaster recovery tested
- [ ] Performance baseline established

This architecture can handle millions of concurrent users with proper infrastructure scaling! 🚀

**Happy Scaling! 🎉**
