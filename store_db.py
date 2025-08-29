from typing import Dict, List
from datetime import datetime
import logging
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models import Game, GameCreate, GameUpdate, GameStatus, Book, BookCreate, BookUpdate, BookStatus, User, UserCreate
from exceptions import GameNotFoundError, GameLimitExceededError, DuplicateGameError
from db_models import GameModel, SettingsModel, UserModel, BookModel
from database import db_manager

logger = logging.getLogger(__name__)

class DatabaseGameStore:
    """基于数据库的游戏存储实现"""
    
    def __init__(self):
        self._session_cache = {}
    
    async def get_all_games(self, user_id: int) -> dict:
        """Get all games for a specific user grouped by status"""
        async with db_manager.get_session() as session:
            # 获取指定用户的所有游戏
            result = await session.execute(
                select(GameModel)
                .where(GameModel.user_id == user_id)
                .order_by(GameModel.created_at.desc())
            )
            db_games = result.scalars().all()
            
            # 按状态分组
            games_by_status = {
                "active": [],
                "paused": [],
                "casual": [],
                "planned": [],
                "finished": [],
                "dropped": []
            }
            
            # 将数据库模型转换为Pydantic模型
            for db_game in db_games:
                pydantic_game = self._db_model_to_pydantic(db_game)
                status_key = db_game.status.value
                games_by_status[status_key].append(pydantic_game)
            
            # 对已完成和弃坑的游戏按结束时间排序
            games_by_status["finished"].sort(key=lambda g: g.ended_at or g.created_at, reverse=True)
            games_by_status["dropped"].sort(key=lambda g: g.ended_at or g.created_at, reverse=True)
            
            return games_by_status
    
    async def get_active_count(self) -> dict:
        """Get current active game count and limit"""
        async with db_manager.get_session() as session:
            # 统计各状态游戏数量
            count_query = select(
                GameModel.status,
                func.count(GameModel.id).label('count')
            ).group_by(GameModel.status)
            
            result = await session.execute(count_query)
            status_counts = {status.value: count for status, count in result}
            
            # 获取限制设置
            limit_result = await session.execute(
                select(SettingsModel.value).where(SettingsModel.key == 'active_limit')
            )
            limit = limit_result.scalar_one_or_none() or 5
            
            return {
                "count": status_counts.get("active", 0),
                "limit": limit,
                "paused_count": status_counts.get("paused", 0),
                "casual_count": status_counts.get("casual", 0),
                "planned_count": status_counts.get("planned", 0)
            }
    
    async def add_game(self, game_data: GameCreate) -> Game:
        """Add a new game"""
        async with db_manager.get_session() as session:
            name = game_data.name.strip()
            
            # Check active game limit only if creating an active game
            if game_data.status == GameStatus.ACTIVE:
                await self._check_active_game_limit(session)
                
                # Check for duplicate names in active games
                if await self._is_duplicate_active_name(session, name):
                    raise DuplicateGameError(name)
            
            # 创建数据库记录
            db_game = GameModel(
                name=name,
                status=game_data.status,
                notes=game_data.notes,
                rating=game_data.rating,
                reason=game_data.reason,
                created_at=datetime.now()
            )
            
            # Set ended_at if creating finished/dropped game
            if game_data.status in [GameStatus.FINISHED, GameStatus.DROPPED]:
                db_game.ended_at = datetime.now()
            
            session.add(db_game)
            await session.commit()
            await session.refresh(db_game)
            
            return self._db_model_to_pydantic(db_game)
    
    async def update_game(self, game_id: int, updates: GameUpdate) -> Game:
        """Update an existing game"""
        async with db_manager.get_session() as session:
            # 获取现有游戏
            result = await session.execute(
                select(GameModel).where(GameModel.id == game_id)
            )
            db_game = result.scalar_one_or_none()
            
            if not db_game:
                raise GameNotFoundError(game_id)
            
            current_status = db_game.status
            
            # Handle name updates with duplicate checking
            if updates.name is not None:
                name = updates.name.strip()
                new_status = updates.status or db_game.status
                if await self._would_create_duplicate_active_name(session, game_id, name, new_status):
                    raise DuplicateGameError(name)
                db_game.name = name
            
            # Handle status updates with business logic
            if updates.status is not None:
                await self._handle_status_change(session, db_game, updates, current_status)
            
            # Handle other field updates
            if updates.notes is not None:
                db_game.notes = updates.notes
            if updates.rating is not None:
                db_game.rating = updates.rating
            if updates.reason is not None:
                db_game.reason = updates.reason
            
            await session.commit()
            await session.refresh(db_game)
            
            return self._db_model_to_pydantic(db_game)
    
    async def delete_game(self, game_id: int) -> bool:
        """Delete a game completely"""
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(GameModel).where(GameModel.id == game_id)
            )
            db_game = result.scalar_one_or_none()
            
            if not db_game:
                raise GameNotFoundError(game_id)
            
            await session.delete(db_game)
            await session.commit()
            
            return True
    
    async def update_limit(self, new_limit: int) -> None:
        """Update the active game limit"""
        # 强制限制上限不能超过5，保持理性游戏
        if new_limit > 5:
            new_limit = 5
        elif new_limit < 1:
            new_limit = 1
        
        async with db_manager.get_session() as session:
            # 更新或插入设置
            result = await session.execute(
                select(SettingsModel).where(SettingsModel.key == 'active_limit')
            )
            setting = result.scalar_one_or_none()
            
            if setting:
                setting.value = new_limit
            else:
                setting = SettingsModel(key='active_limit', value=new_limit)
                session.add(setting)
            
            await session.commit()
    
    async def _check_active_game_limit(self, session: AsyncSession) -> None:
        """检查活跃游戏数量限制"""
        active_count = await session.scalar(
            select(func.count(GameModel.id)).where(GameModel.status == GameStatus.ACTIVE)
        )
        
        limit_result = await session.execute(
            select(SettingsModel.value).where(SettingsModel.key == 'active_limit')
        )
        limit = limit_result.scalar_one_or_none() or 5
        
        if active_count >= limit:
            raise GameLimitExceededError(limit)
    
    async def _is_duplicate_active_name(self, session: AsyncSession, name: str, exclude_id: int = None) -> bool:
        """Check if name exists in active games"""
        query = select(GameModel.id).where(
            and_(
                GameModel.status == GameStatus.ACTIVE,
                func.lower(GameModel.name) == name.lower()
            )
        )
        
        if exclude_id is not None:
            query = query.where(GameModel.id != exclude_id)
        
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def _would_create_duplicate_active_name(self, session: AsyncSession, game_id: int, name: str, new_status: GameStatus) -> bool:
        """Check if updating would create a duplicate active name"""
        if new_status == GameStatus.ACTIVE:
            return await self._is_duplicate_active_name(session, name, exclude_id=game_id)
        return False
    
    async def _handle_status_change(self, session: AsyncSession, db_game: GameModel, updates: GameUpdate, current_status: GameStatus) -> None:
        """Handle the business logic for status changes"""
        new_status = updates.status
        
        if new_status == GameStatus.ACTIVE:
            # Reactivating a game
            if current_status != GameStatus.ACTIVE:
                await self._check_active_game_limit(session)
                
                # Check for duplicate names when reactivating
                check_name = updates.name.strip() if updates.name else db_game.name
                if await self._is_duplicate_active_name(session, check_name, exclude_id=db_game.id):
                    raise DuplicateGameError(check_name)
            
            db_game.ended_at = None
        elif new_status in [GameStatus.PAUSED, GameStatus.CASUAL, GameStatus.PLANNED]:
            # Pausing, marking as casual, or planning - no limit check needed
            db_game.ended_at = None
        else:
            # Finishing or dropping a game
            if current_status == GameStatus.ACTIVE:
                db_game.ended_at = datetime.now()
        
        db_game.status = new_status
    
    def _db_model_to_pydantic(self, db_game: GameModel) -> Game:
        """Convert SQLAlchemy model to Pydantic model"""
        return Game(
            id=db_game.id,
            name=db_game.name,
            status=db_game.status,
            notes=db_game.notes or "",
            rating=db_game.rating,
            reason=db_game.reason or "",
            created_at=db_game.created_at,
            ended_at=db_game.ended_at
        )