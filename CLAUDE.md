# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **multi-user** dual-purpose tracking application (游戏追踪器) built with FastAPI that manages both gaming progress and reading progress. It helps users control concurrent limits to avoid "starting too many games/books" anxiety.

### Multi-User Architecture
- **User Authentication**: Complete JWT-based login/registration system
- **Data Isolation**: Each user has independent game/book data
- **Game Tracker**: Primary feature for managing gaming progress with concurrent game limiting
- **Reading Tracker**: Secondary feature for managing reading progress with concurrent book limiting
- **Data Export**: Users can export their data in JSON/CSV/Excel formats

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

#### Authentication (🆕 New)
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login (returns JWT token)
- `GET /api/auth/me` - Get current user information

#### Game Management (🔒 Now requires authentication)
- `GET /api/games` - Returns user's games grouped by status
- `POST /api/games` - Create new game (validates user limits)
- `PATCH /api/games/{id}` - Update user's game (handles status transitions)
- `DELETE /api/games/{id}` - Remove user's game completely
- `GET /api/active-count` - Get current user's counts and limits
- `POST /api/settings/limit` - Update user's concurrent game limit

#### Book Management (🔒 Now requires authentication)
- `GET /api/books` - Returns user's books grouped by status
- `POST /api/books` - Create new book (validates user limits)
- `PATCH /api/books/{id}` - Update user's book (handles status transitions)
- `DELETE /api/books/{id}` - Remove user's book completely
- `GET /api/reading-count` - Get current user's reading counts and limits
- `POST /api/books/settings/limit` - Update user's concurrent reading limit

#### Data Export (🆕 New)
- `POST /api/export` - Export user data (supports JSON/CSV/Excel formats)

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
- `app.py` - Main FastAPI application with all endpoints (🔒 now includes auth)
- `run.py` - Simplified development server launcher
- `models.py` - Pydantic data models (🆕 includes user models)
- `exceptions.py` - Custom exception classes

### Authentication & User Management (🆕 New)
- `auth.py` - JWT authentication, password hashing, user dependencies
- `user_store.py` - Multi-user storage layer with data isolation

### Game Storage Layer
- `store.py` - JSON file storage implementation (legacy, single-user)
- `store_db.py` - PostgreSQL storage implementation  
- `store_adapter.py` - Automatic storage mode selection
- `db_models.py` - SQLAlchemy database models (🆕 includes user models)
- `database.py` - Database connection and setup

### Book Storage Layer
- `book_store.py` - JSON-only storage for books (legacy, single-user)

### Data Migration Tools (🆕 New)
- `migrate_existing_data.py` - General migration script
- `quick_migrate.py` - Pre-configured migration for hero19950611

### Data Files
- `games_data.json` - Game data file (legacy, pre-user system)
- `books_data.json` - Book data file (legacy, pre-user system)
- `requirements.txt` - Python dependencies (🆕 includes auth libraries)

### Web Interface
- `templates/index.html` - Game tracker web interface (🔒 now requires login)
- `templates/login.html` - User login/registration page (🆕 New)
- `templates/reading.html` - Reading tracker web interface (🔒 now requires login)
- `static/` - Static assets (CSS, JS)

### Marketing & Documentation (🆕 New)
- `market/` - Marketing strategy and discussion documents

## Post-Deployment Data Migration

### User Account: hero19950611
- **Email**: 382592406@qq.com  
- **Password**: HEROsf4454
- **Username**: hero19950611

### Migration Process (After Render Deployment)
1. **Verify Deployment**: Ensure the web application is running with PostgreSQL
2. **Run Migration Script**: Execute `quick_migrate.py` to migrate existing JSON data to user account
3. **Verify Migration**: Login and confirm all games/books are properly migrated
4. **Archive Legacy Files**: Keep `games_data.json` and `books_data.json` as backup

### Migration Command
```bash
# On deployed server (if shell access available) or locally with DATABASE_URL
python quick_migrate.py
```

**Note**: The migration script is pre-configured with hero19950611's credentials and will automatically create the user account and migrate all existing data.