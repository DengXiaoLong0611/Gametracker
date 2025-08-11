from fastapi import HTTPException

class GameTrackerException(Exception):
    """Base exception for game tracker operations"""
    pass

class GameNotFoundError(GameTrackerException):
    """Raised when a game is not found"""
    def __init__(self, game_id: int):
        self.game_id = game_id
        super().__init__(f"Game with ID {game_id} not found")
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=404, detail=str(self))

class GameLimitExceededError(GameTrackerException):
    """Raised when trying to exceed the active game limit"""
    def __init__(self, limit: int):
        self.limit = limit
        super().__init__(f"Cannot exceed limit of {limit} active games")
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=400, detail=str(self))

class DuplicateGameError(GameTrackerException):
    """Raised when trying to create a duplicate active game"""
    def __init__(self, game_name: str):
        self.game_name = game_name
        super().__init__(f"Game '{game_name}' already exists in active games")
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=400, detail=str(self))

import functools

def handle_game_tracker_exception(func):
    """Decorator to convert GameTrackerException to HTTPException"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except GameTrackerException as e:
            if hasattr(e, 'to_http_exception'):
                raise e.to_http_exception()
            else:
                raise HTTPException(status_code=500, detail=str(e))
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except GameTrackerException as e:
            if hasattr(e, 'to_http_exception'):
                raise e.to_http_exception()
            else:
                raise HTTPException(status_code=500, detail=str(e))
    
    # Return async wrapper for async functions
    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper