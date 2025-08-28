# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Game Tracker web application (游戏追踪器) built with FastAPI that helps users manage their gaming progress and control concurrent game limits to avoid "starting too many games" anxiety.

## Key Architecture

- **FastAPI Backend**: Main application in `app.py` with RESTful API endpoints
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

# Run in development mode (JSON storage)
DEBUG=true python app.py

# Run with database (requires DATABASE_URL)
export DATABASE_URL="postgresql://user:pass@localhost:5432/game_tracker"
export USE_DATABASE=true
python app.py
```

## Storage Modes

The application supports two storage modes with automatic detection and **mutually exclusive** operation:

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

## Database Switching Logic

### Priority Detection (`store_adapter.py`)
The storage mode is determined at application startup with the following priority:

```python
def _should_use_database(self) -> bool:
    # 1. Highest priority: DATABASE_URL environment variable
    if os.getenv("DATABASE_URL"):
        return True
    
    # 2. Explicit setting: USE_DATABASE=true
    if os.getenv("USE_DATABASE", "false").lower() in ("true", "1", "yes"):
        return True
    
    # 3. Default: JSON mode for backward compatibility
    return False
```

### Key Behavioral Rules
1. **Runtime Fixed**: Storage mode is determined once at startup and cannot change during runtime
2. **Mutually Exclusive**: Only ONE storage mode is active - never both simultaneously
3. **No Dual Writing**: Data operations only write to the selected storage backend
4. **Automatic Migration**: When switching to database mode, existing JSON data is automatically migrated

### Storage Mode Indicators
- Check current mode via `/health` endpoint: `"database_mode": true/false`
- Database mode logs show: `"Using database storage mode"`
- JSON mode logs show: `"Using JSON file storage mode"`

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

## Core Files

- `app.py` - Main FastAPI application
- `models.py` - Pydantic data models  
- `db_models.py` - SQLAlchemy database models
- `database.py` - Database connection and setup
- `store.py` - JSON file storage implementation
- `store_db.py` - PostgreSQL storage implementation
- `store_adapter.py` - Storage mode selection logic
- `exceptions.py` - Custom exception classes
- `games_data.json` - JSON data file (created automatically)
- `requirements.txt` - Python dependencies
- `templates/index.html` - Web interface
- `static/` - Static assets (CSS, JS)