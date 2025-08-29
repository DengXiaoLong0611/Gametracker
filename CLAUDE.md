# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a dual-purpose tracking application (游戏追踪器) built with FastAPI that manages both gaming progress and reading progress. It helps users control concurrent limits to avoid "starting too many games/books" anxiety.

### Dual Tracker Architecture
- **Game Tracker**: Primary feature for managing gaming progress with concurrent game limiting
- **Reading Tracker**: Secondary feature for managing reading progress with concurrent book limiting
- Both trackers share similar status systems and limiting mechanisms but operate independently

## Key Architecture

- **FastAPI Backend**: Main application in `app.py` with RESTful API endpoints
- **Data Models**: Pydantic models in `models.py` and SQLAlchemy models in `db_models.py`
- **Dual Storage Architecture**: 
  - **Games**: Dual-mode storage with automatic switching between JSON and PostgreSQL
    - `store.py`: Original JSON file storage (thread-safe)
    - `store_db.py`: PostgreSQL storage with async SQLAlchemy
    - `store_adapter.py`: Automatic mode selection based on environment variables
  - **Books**: JSON-only storage via `book_store.py` (independent of game storage mode)
- **Database Layer**: Async PostgreSQL with connection pooling and health checks (`database.py`)
- **Status Systems**: 
  - **Games**: Six states - ACTIVE, PAUSED, CASUAL, PLANNED, FINISHED, DROPPED
  - **Books**: Four states - READING, PLANNED, FINISHED, DROPPED
- **Concurrent Limiting**: Both games and books enforce concurrent limits (games: max 5 active, books: max 3 reading)

## Development Commands

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Simple local development (uses run.py for convenience)
python run.py

# Main application (JSON storage)
python app.py

# Development mode with auto-reload
DEBUG=true python app.py
```

### Database Development
```bash
# Run with database (requires DATABASE_URL)
export DATABASE_URL="postgresql://user:pass@localhost:5432/game_tracker"
export USE_DATABASE=true
python app.py

# Migrate existing JSON data to database
python migrate_to_db.py
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

#### Game Management
- `GET /api/games` - Returns games grouped by status
- `POST /api/games` - Create new game (validates limits)
- `PATCH /api/games/{id}` - Update game (handles status transitions)
- `DELETE /api/games/{id}` - Remove game completely
- `GET /api/active-count` - Get current counts and limits
- `POST /api/settings/limit` - Update concurrent game limit

#### Book Management  
- `GET /api/books` - Returns books grouped by status
- `POST /api/books` - Create new book (validates limits)
- `PATCH /api/books/{id}` - Update book (handles status transitions)
- `DELETE /api/books/{id}` - Remove book completely
- `GET /api/reading-count` - Get current reading counts and limits
- `POST /api/books/settings/limit` - Update concurrent reading limit

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

### Application Core
- `app.py` - Main FastAPI application with all endpoints
- `run.py` - Simplified development server launcher
- `models.py` - Pydantic data models for games and books
- `exceptions.py` - Custom exception classes

### Game Storage Layer
- `store.py` - JSON file storage implementation (thread-safe)
- `store_db.py` - PostgreSQL storage implementation  
- `store_adapter.py` - Automatic storage mode selection
- `db_models.py` - SQLAlchemy database models
- `database.py` - Database connection and setup
- `migrate_to_db.py` - JSON to PostgreSQL migration script

### Book Storage Layer
- `book_store.py` - JSON-only storage for books (independent system)

### Data Files
- `games_data.json` - Game data file (created automatically)
- `books_data.json` - Book data file (created automatically)
- `requirements.txt` - Python dependencies

### Web Interface
- `templates/index.html` - Game tracker web interface
- `templates/reading.html` - Reading tracker web interface
- `static/` - Static assets (CSS, JS)