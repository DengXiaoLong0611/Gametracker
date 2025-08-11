from typing import Dict, List
from datetime import datetime
import threading
import json
import os
from pathlib import Path

from models import Game, GameCreate, GameUpdate, GameStatus
from exceptions import GameNotFoundError, GameLimitExceededError, DuplicateGameError

class GameStore:
    def __init__(self, default_limit: int = 3, data_file: str = "games_data.json"):
        self._games: Dict[int, Game] = {}
        self._next_id = 1
        self._limit = default_limit
        self._lock = threading.Lock()
        self._data_file = Path(data_file)
        self._load_data()
    
    def get_all_games(self) -> dict:
        """Get all games grouped by status"""
        with self._lock:
            active = [game for game in self._games.values() if game.status == GameStatus.ACTIVE]
            finished = [game for game in self._games.values() if game.status == GameStatus.FINISHED]
            dropped = [game for game in self._games.values() if game.status == GameStatus.DROPPED]
            
            return {
                "active": sorted(active, key=lambda g: g.created_at, reverse=True),
                "finished": sorted(finished, key=lambda g: g.ended_at or g.created_at, reverse=True),
                "dropped": sorted(dropped, key=lambda g: g.ended_at or g.created_at, reverse=True)
            }
    
    def get_active_count(self) -> dict:
        """Get current active game count and limit"""
        with self._lock:
            active_count = len([g for g in self._games.values() if g.status == GameStatus.ACTIVE])
            return {"count": active_count, "limit": self._limit}
    
    def add_game(self, game_data: GameCreate) -> Game:
        """Add a new game"""
        with self._lock:
            name = game_data.name.strip()
            
            # Check active game limit only if creating an active game
            if game_data.status == GameStatus.ACTIVE:
                active_games = [g for g in self._games.values() if g.status == GameStatus.ACTIVE]
                if len(active_games) >= self._limit:
                    raise GameLimitExceededError(self._limit)
                
                # Check for duplicate names in active games
                if self._is_duplicate_active_name(name):
                    raise DuplicateGameError(name)
            
            # Set ended_at if creating finished/dropped game
            ended_at = datetime.now() if game_data.status != GameStatus.ACTIVE else None
            
            game = Game(
                id=self._next_id,
                name=name,
                status=game_data.status,
                notes=game_data.notes,
                rating=game_data.rating,
                reason=game_data.reason,
                created_at=datetime.now(),
                ended_at=ended_at
            )
            
            self._games[self._next_id] = game
            self._next_id += 1
            self._save_data()
            return game
    
    def update_game(self, game_id: int, updates: GameUpdate) -> Game:
        """Update an existing game"""
        with self._lock:
            if game_id not in self._games:
                raise GameNotFoundError(game_id)
            
            game = self._games[game_id]
            current_status = game.status
            
            # Handle name updates with duplicate checking
            if updates.name is not None:
                name = updates.name.strip()
                if self._would_create_duplicate_active_name(game_id, name, updates.status or game.status):
                    raise DuplicateGameError(name)
                game.name = name
            
            # Handle status updates with business logic
            if updates.status is not None:
                self._handle_status_change(game, updates, current_status)
            
            # Handle other field updates
            if updates.notes is not None:
                game.notes = updates.notes
            if updates.rating is not None:
                game.rating = updates.rating
            if updates.reason is not None:
                game.reason = updates.reason
            
            self._save_data()
            return game
    
    def delete_game(self, game_id: int) -> bool:
        """Delete a game completely"""
        with self._lock:
            if game_id not in self._games:
                raise GameNotFoundError(game_id)
            
            del self._games[game_id]
            self._save_data()
            return True
    
    def set_limit(self, new_limit: int) -> dict:
        """Update the concurrent game limit"""
        with self._lock:
            self._limit = new_limit
            active_count = len([g for g in self._games.values() if g.status == GameStatus.ACTIVE])
            self._save_data()
            return {"count": active_count, "limit": self._limit}
    
    def _is_duplicate_active_name(self, name: str, exclude_id: int = None) -> bool:
        """Check if name exists in active games"""
        active_games = [g for g in self._games.values() if g.status == GameStatus.ACTIVE]
        if exclude_id is not None:
            active_games = [g for g in active_games if g.id != exclude_id]
        return any(g.name.lower() == name.lower() for g in active_games)
    
    def _would_create_duplicate_active_name(self, game_id: int, name: str, new_status: GameStatus) -> bool:
        """Check if updating would create a duplicate active name"""
        if new_status == GameStatus.ACTIVE:
            return self._is_duplicate_active_name(name, exclude_id=game_id)
        return False
    
    def _handle_status_change(self, game: Game, updates: GameUpdate, current_status: GameStatus) -> None:
        """Handle the business logic for status changes"""
        new_status = updates.status
        
        if new_status == GameStatus.ACTIVE:
            # Reactivating a game
            if current_status != GameStatus.ACTIVE:
                # Check limit when reactivating
                active_games = [g for g in self._games.values() if g.status == GameStatus.ACTIVE]
                if len(active_games) >= self._limit:
                    raise GameLimitExceededError(self._limit)
                
                # Check for duplicate names when reactivating
                check_name = updates.name.strip() if updates.name else game.name
                if self._is_duplicate_active_name(check_name, exclude_id=game.id):
                    raise DuplicateGameError(check_name)
            
            game.ended_at = None
        else:
            # Finishing or dropping a game
            if current_status == GameStatus.ACTIVE:
                game.ended_at = datetime.now()
        
        game.status = new_status
    
    def _save_data(self) -> None:
        """保存数据到JSON文件"""
        try:
            data = {
                "games": {},
                "next_id": self._next_id,
                "limit": self._limit
            }
            
            # 转换Game对象为字典
            for game_id, game in self._games.items():
                game_dict = game.model_dump()
                # 转换datetime对象为字符串
                if game_dict.get('created_at'):
                    game_dict['created_at'] = game_dict['created_at'].isoformat()
                if game_dict.get('ended_at'):
                    game_dict['ended_at'] = game_dict['ended_at'].isoformat()
                data["games"][str(game_id)] = game_dict
            
            with open(self._data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据失败: {e}")
    
    def _load_data(self) -> None:
        """从JSON文件加载数据"""
        if not self._data_file.exists():
            return
        
        try:
            with open(self._data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 恢复设置
            self._next_id = data.get("next_id", 1)
            self._limit = data.get("limit", 3)
            
            # 恢复游戏数据
            games_data = data.get("games", {})
            for game_id_str, game_dict in games_data.items():
                game_id = int(game_id_str)
                
                # 转换字符串时间回datetime对象
                if game_dict.get('created_at'):
                    game_dict['created_at'] = datetime.fromisoformat(game_dict['created_at'])
                if game_dict.get('ended_at'):
                    game_dict['ended_at'] = datetime.fromisoformat(game_dict['ended_at'])
                
                # 创建Game对象
                game = Game(**game_dict)
                self._games[game_id] = game
                
        except Exception as e:
            print(f"加载数据失败: {e}")
            # 如果加载失败，使用默认值
            self._games = {}
            self._next_id = 1
            self._limit = 3
        self._save_data()