import os
import asyncio
from typing import Dict, Union
import logging

from models import Game, GameCreate, GameUpdate
from store import GameStore  # Original JSON-based store
from store_db import DatabaseGameStore  # New database store

logger = logging.getLogger(__name__)

class GameStoreAdapter:
    """游戏存储适配器，自动选择JSON或数据库存储模式"""
    
    def __init__(self):
        self.use_database = self._should_use_database()
        self._store = None
        self._initialize_store()
    
    def _should_use_database(self) -> bool:
        """判断是否应该使用数据库模式"""
        # 如果有DATABASE_URL环境变量，使用数据库
        if os.getenv("DATABASE_URL"):
            return True
        
        # 如果显式设置了USE_DATABASE环境变量
        use_db_env = os.getenv("USE_DATABASE", "false").lower()
        if use_db_env in ("true", "1", "yes"):
            return True
        
        # 默认使用JSON模式（向后兼容）
        return False
    
    def _initialize_store(self):
        """初始化存储实例"""
        if self.use_database:
            self._store = DatabaseGameStore()
            logger.info("Using database storage mode")
        else:
            self._store = GameStore()
            logger.info("Using JSON file storage mode")
    
    def _ensure_async_context(self):
        """确保在异步上下文中运行"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 如果没有运行的事件循环，创建一个
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    
    async def get_all_games(self) -> dict:
        """Get all games grouped by status"""
        if self.use_database:
            return await self._store.get_all_games()
        else:
            return self._store.get_all_games()
    
    async def get_active_count(self) -> dict:
        """Get current active game count and limit"""
        if self.use_database:
            return await self._store.get_active_count()
        else:
            return self._store.get_active_count()
    
    async def add_game(self, game_data: GameCreate) -> Game:
        """Add a new game"""
        if self.use_database:
            return await self._store.add_game(game_data)
        else:
            return self._store.add_game(game_data)
    
    async def update_game(self, game_id: int, updates: GameUpdate) -> Game:
        """Update an existing game"""
        if self.use_database:
            return await self._store.update_game(game_id, updates)
        else:
            return self._store.update_game(game_id, updates)
    
    async def delete_game(self, game_id: int) -> bool:
        """Delete a game completely"""
        if self.use_database:
            return await self._store.delete_game(game_id)
        else:
            return self._store.delete_game(game_id)
    
    async def update_limit(self, new_limit: int) -> None:
        """Update the active game limit"""
        if self.use_database:
            return await self._store.update_limit(new_limit)
        else:
            return self._store.update_limit(new_limit)
    
    # 同步接口（为了保持向后兼容）
    def get_all_games_sync(self) -> dict:
        """同步版本的get_all_games"""
        if self.use_database:
            self._ensure_async_context()
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._store.get_all_games())
        else:
            return self._store.get_all_games()
    
    def get_active_count_sync(self) -> dict:
        """同步版本的get_active_count"""
        if self.use_database:
            self._ensure_async_context()
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._store.get_active_count())
        else:
            return self._store.get_active_count()
    
    def add_game_sync(self, game_data: GameCreate) -> Game:
        """同步版本的add_game"""
        if self.use_database:
            self._ensure_async_context()
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._store.add_game(game_data))
        else:
            return self._store.add_game(game_data)
    
    def update_game_sync(self, game_id: int, updates: GameUpdate) -> Game:
        """同步版本的update_game"""
        if self.use_database:
            self._ensure_async_context()
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._store.update_game(game_id, updates))
        else:
            return self._store.update_game(game_id, updates)
    
    def delete_game_sync(self, game_id: int) -> bool:
        """同步版本的delete_game"""
        if self.use_database:
            self._ensure_async_context()
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._store.delete_game(game_id))
        else:
            return self._store.delete_game(game_id)
    
    def update_limit_sync(self, new_limit: int) -> None:
        """同步版本的update_limit"""
        if self.use_database:
            self._ensure_async_context()
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._store.update_limit(new_limit))
        else:
            return self._store.update_limit(new_limit)