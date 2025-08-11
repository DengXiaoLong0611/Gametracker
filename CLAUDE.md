# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a game tracking web application built with FastAPI that helps users manage concurrent gaming by enforcing a configurable limit on active games (default: 3). The app prevents "starting too many games at once" anxiety by providing strict controls and validation.

**Key Features:**
- Configurable concurrent game limit 
- Duplicate active game prevention (case-insensitive)
- Three game states: active/finished/dropped with state transitions
- Notes, ratings (0-10), and reasons for each game
- In-memory storage with thread-safe operations

## Development Commands

### Environment Setup
```powershell
# Create virtual environment
python -m venv .venv

# Install dependencies
.\.venv\Scripts\pip install -r requirements.txt
```

### Running the Application
```powershell
# Start server (non-reload mode to preserve memory state)
.\.venv\Scripts\python app.py

# Access at: http://127.0.0.1:8001/
```

### Testing
No automated tests are currently configured. Manual testing through the web interface.

## Architecture

### Core Data Models (`store.py`)
- **Game**: Dataclass with id, name, status, timestamps, notes, rating, reason
- **GameStore**: Thread-safe singleton managing all game operations with Lock
- **GameStatus**: Literal type with "active"|"finished"|"dropped" states

### Key Business Logic
- **Concurrent Limit Enforcement**: Both frontend and backend validation
- **Duplicate Prevention**: Case-insensitive name matching for active games only  
- **State Transitions**: Automatic timestamp management when changing status
- **Thread Safety**: All store operations use threading.Lock for concurrent access

### API Structure (`app.py`)
- `GET /api/games` - Returns games grouped by status (active/finished/dropped)
- `POST /api/games` - Create new active game with validation
- `PATCH /api/games/{id}` - Update any game field with business rule validation
- `DELETE /api/games/{id}` - Remove game completely
- `POST /api/settings/limit` - Update concurrent game limit
- `GET /api/active-count` - Current active count and limit

### Frontend (`static/app.js`, `templates/index.html`)
- Vanilla JavaScript with fetch API for backend communication
- Real-time UI updates with proper error handling
- Three separate lists rendering games by status
- Inline editing for notes, ratings, and reasons

## Critical Implementation Details

### Memory Storage Considerations
- Data persists only during server runtime - restarts clear all games
- Server runs with `reload=False` to maintain memory state stability
- Thread-safe operations prevent race conditions in concurrent requests

### Validation Rules
- Active games must have unique names (case-insensitive, whitespace-trimmed)
- Cannot exceed configured concurrent limit when adding or reactivating games
- Rating validation: 0-10 integer range
- Game names: 1-100 characters, non-empty after trimming

### State Management
- Active → Finished/Dropped: Sets ended_at timestamp
- Finished/Dropped → Active: Clears ended_at, validates limit and duplicates
- Name changes on active games validate against other active games

## Dependencies
- **FastAPI**: Web framework with automatic API documentation
- **Uvicorn**: ASGI server for FastAPI
- **Jinja2**: Template rendering for HTML responses
- **Pydantic**: Request/response validation and parsing