# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Game Tracker web application (游戏追踪器) built with FastAPI that helps users manage their gaming progress and control concurrent game limits to avoid "starting too many games" anxiety. The application supports multiple deployment environments including local development, Tencent Cloud containers, and cloud functions.

## Key Architecture

- **FastAPI Backend**: Main application in `app.py` with RESTful API endpoints and lifespan events
- **Data Models**: Pydantic models in `models.py` and SQLAlchemy models in `db_models.py`
- **Storage Layer**: Dual-mode storage with automatic switching between JSON and PostgreSQL
  - `store.py`: Original JSON file storage (thread-safe)
  - `store_db.py`: PostgreSQL storage with async SQLAlchemy
  - `store_adapter.py`: Automatic mode selection based on environment variables
- **Database Layer**: Async PostgreSQL with connection pooling and health checks (`database.py`)
- **Game Status System**: Six states - ACTIVE, PAUSED, CASUAL, PLANNED, FINISHED, DROPPED
- **Concurrent Game Limiting**: Database constraints and business logic enforce max 5 active games

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (copy .env.example to .env)
cp .env.example .env

# Run in development mode (JSON storage)
DEBUG=true python app.py

# Run with database (requires DATABASE_URL)
export DATABASE_URL="postgresql://user:pass@localhost:5432/game_tracker"
export USE_DATABASE=true
python app.py
```

### Database Migration
```bash
# Migrate existing JSON data to database
export DATABASE_URL="postgresql://user:pass@localhost:5432/game_tracker"
python migrate_json_to_db.py

# Or use the automated deploy script
python deploy.py
```

### Docker Deployment
```bash
# For Render (uses Dockerfile)
docker build -t game-tracker .
docker run -p 10000:10000 -e DATABASE_URL="..." game-tracker

# For Tencent Cloud (uses Dockerfile.tencent)
docker build -f Dockerfile.tencent -t game-tracker .
docker run -p 9000:9000 game-tracker

# Check health
curl http://localhost:8000/health
```

## Storage Modes

The application supports two storage modes with automatic detection:

### JSON Mode (Default)
- File-based storage in `games_data.json`
- Thread-safe with file locking
- Suitable for single-instance deployments
- Activated when no `DATABASE_URL` environment variable

### Database Mode
- PostgreSQL with SQLAlchemy ORM
- Async operations with connection pooling
- Suitable for production/cloud deployments
- Activated when `DATABASE_URL` is present

## Environment Configuration

The application detects deployment environments automatically:
- `DEPLOYMENT_ENV=local`: Uses port 8001 (default)
- `DEPLOYMENT_ENV=tencent-container`: Uses port 9000
- `DEPLOYMENT_ENV=tencent-scf`: Uses port 9000 for cloud functions
- `DEBUG=true`: Enables reload and debug logging
- `HOST`: Server binding address (default: 0.0.0.0)
- `PORT`: Override default port

## Core Business Logic

### Game Status Transitions
- Only ACTIVE games count toward the concurrent limit (max 5, enforced in code)
- PAUSED, CASUAL, PLANNED games don't count toward limit
- Duplicate names only checked for ACTIVE games
- FINISHED/DROPPED games automatically set `ended_at` timestamp

### API Endpoints
- `GET /api/games` - Returns games grouped by status
- `POST /api/games` - Create new game (validates limits)
- `PATCH /api/games/{id}` - Update game (handles status transitions)
- `DELETE /api/games/{id}` - Remove game completely
- `GET /api/active-count` - Get current counts and limits
- `POST /api/settings/limit` - Update concurrent game limit

## Data Persistence

- Uses JSON file storage (`games_data.json`) with automatic backup
- Thread-safe operations with proper locking
- Datetime serialization handled automatically
- Graceful error handling for file operations

## Security Features

- CORS middleware configured (currently allows all origins)
- Security headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
- Input validation through Pydantic models
- Health check endpoint at `/health`

## Testing & Validation

The application includes built-in validation through Pydantic models and business logic enforcement. No specific test framework is configured - when adding tests, check for existing test patterns in the codebase first.

## Render部署指南

### 从JSON模式升级到PostgreSQL数据库

**步骤1：添加PostgreSQL数据库**
```
Render Dashboard → 你的现有服务旁边 → New → PostgreSQL
选择免费套餐，创建数据库实例
```

**步骤2：连接数据库到现有服务**
```
你的Web Service → Environment → Add Environment Variable
键: DATABASE_URL
值: [PostgreSQL连接字符串，Render会自动提供]
```

**步骤3：Git推送触发重新部署**
```bash
git add .
git commit -m "🗄️ 添加PostgreSQL数据库支持"
git push origin main
```

**步骤4：验证部署**
```bash
# 检查健康状态
curl https://your-app.onrender.com/health

# 应该看到：
{
  "status": "healthy",
  "database_mode": true,
  "active_games": 0
}
```

**故障排除**
- 如果启动失败，检查Render日志中的数据库连接错误
- 如果数据迁移失败，可以手动运行 `python migrate_json_to_db.py`
- 健康检查endpoint会显示当前使用的存储模式