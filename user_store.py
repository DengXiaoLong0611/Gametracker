"""
多用户数据存储层
支持用户管理、游戏管理、书籍管理的数据库操作
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from models import (
    User, UserCreate, UserResponse, 
    Game, GameCreate, GameUpdate, GameStatus,
    Book, BookCreate, BookUpdate, BookStatus
)
from exceptions import GameNotFoundError, GameLimitExceededError, DuplicateGameError
from db_models import UserModel, GameModel, BookModel, SettingsModel
from database import db_manager

logger = logging.getLogger(__name__)

class UserNotFoundError(Exception):
    """用户未找到异常"""
    def __init__(self, user_id: int):
        super().__init__(f"User with ID {user_id} not found")

class EmailAlreadyExistsError(Exception):
    """邮箱已存在异常"""
    def __init__(self, email: str):
        super().__init__(f"Email {email} already exists")

class MultiUserStore:
    """多用户数据存储类"""
    
    def __init__(self):
        pass
    
    # ====================== 用户管理 ======================
    
    async def create_user(self, user_data: UserCreate, password_hash: str) -> User:
        """创建新用户"""
        async with db_manager.get_session() as session:
            # 检查邮箱是否已存在
            existing_user = await session.execute(
                select(UserModel).where(UserModel.email == user_data.email)
            )
            if existing_user.scalar_one_or_none():
                raise EmailAlreadyExistsError(user_data.email)
            
            # 创建新用户
            db_user = UserModel(
                username=user_data.username,
                email=user_data.email,
                password_hash=password_hash,
                is_active=True
            )
            
            try:
                session.add(db_user)
                await session.commit()
                await session.refresh(db_user)
                
                # 创建默认设置
                await self._create_default_settings(session, db_user.id)
                
                return self._user_db_to_pydantic(db_user)
                
            except IntegrityError:
                await session.rollback()
                raise EmailAlreadyExistsError(user_data.email)
    
    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """根据邮箱获取用户"""
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: int) -> Optional[UserModel]:
        """根据ID获取用户"""
        async with db_manager.get_session() as session:
            return await session.get(UserModel, user_id)
    
    async def _create_default_settings(self, session: AsyncSession, user_id: int):
        """为新用户创建默认设置"""
        default_settings = [
            SettingsModel(user_id=user_id, key="game_limit", value=3),
            SettingsModel(user_id=user_id, key="book_limit", value=3)
        ]
        
        for setting in default_settings:
            session.add(setting)
        await session.commit()
    
    # ====================== 游戏管理 ======================
    
    async def get_all_games(self, user_id: int) -> dict:
        """获取用户的所有游戏，按状态分组"""
        async with db_manager.get_session() as session:
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
            
            for db_game in db_games:
                pydantic_game = self._game_db_to_pydantic(db_game)
                status_key = db_game.status.value
                games_by_status[status_key].append(pydantic_game)
            
            # 对已完成和弃坑的游戏按结束时间排序
            games_by_status["finished"].sort(key=lambda g: g.ended_at or g.created_at, reverse=True)
            games_by_status["dropped"].sort(key=lambda g: g.ended_at or g.created_at, reverse=True)
            
            return games_by_status
    
    async def get_active_count(self, user_id: int) -> dict:
        """获取用户的活跃游戏计数"""
        async with db_manager.get_session() as session:
            # 获取各状态游戏数量
            active_count = await self._get_game_count_by_status(session, user_id, GameStatus.ACTIVE)
            paused_count = await self._get_game_count_by_status(session, user_id, GameStatus.PAUSED)
            casual_count = await self._get_game_count_by_status(session, user_id, GameStatus.CASUAL)
            planned_count = await self._get_game_count_by_status(session, user_id, GameStatus.PLANNED)
            
            # 获取游戏限制
            limit = await self._get_user_setting(session, user_id, "game_limit", 3)
            
            return {
                "count": active_count,
                "limit": limit,
                "paused_count": paused_count,
                "casual_count": casual_count,
                "planned_count": planned_count
            }
    
    async def add_game(self, user_id: int, game_data: GameCreate) -> Game:
        """添加新游戏"""
        async with db_manager.get_session() as session:
            # 检查活跃游戏数量限制
            if game_data.status == GameStatus.ACTIVE:
                active_count = await self._get_game_count_by_status(session, user_id, GameStatus.ACTIVE)
                limit = await self._get_user_setting(session, user_id, "game_limit", 3)
                
                if active_count >= limit:
                    raise GameLimitExceededError(limit)
                
                # 检查重复游戏名
                await self._check_duplicate_game_name(session, user_id, game_data.name)
            
            # 创建游戏记录
            db_game = GameModel(
                user_id=user_id,
                name=game_data.name,
                status=game_data.status,
                notes=game_data.notes,
                rating=game_data.rating,
                reason=game_data.reason
            )
            
            session.add(db_game)
            await session.commit()
            await session.refresh(db_game)
            
            return self._game_db_to_pydantic(db_game)
    
    async def update_game(self, user_id: int, game_id: int, updates: GameUpdate) -> Game:
        """更新游戏"""
        async with db_manager.get_session() as session:
            db_game = await session.get(GameModel, game_id)
            if not db_game or db_game.user_id != user_id:
                raise GameNotFoundError(game_id)
            
            # 检查状态变更的限制
            if updates.status and updates.status != db_game.status:
                if updates.status == GameStatus.ACTIVE:
                    active_count = await self._get_game_count_by_status(session, user_id, GameStatus.ACTIVE)
                    limit = await self._get_user_setting(session, user_id, "game_limit", 3)
                    
                    if active_count >= limit:
                        raise GameLimitExceededError(limit)
                    
                    # 检查重复游戏名
                    game_name = updates.name or db_game.name
                    await self._check_duplicate_game_name(session, user_id, game_name, exclude_id=game_id)
                
                # 设置结束时间
                if updates.status in [GameStatus.FINISHED, GameStatus.DROPPED]:
                    db_game.ended_at = datetime.now()
                elif db_game.status in [GameStatus.FINISHED, GameStatus.DROPPED]:
                    # 从完成/弃坑状态变为其他状态，清除结束时间
                    db_game.ended_at = None
            
            # 更新字段
            for field, value in updates.dict(exclude_unset=True).items():
                setattr(db_game, field, value)
            
            await session.commit()
            await session.refresh(db_game)
            
            return self._game_db_to_pydantic(db_game)
    
    async def delete_game(self, user_id: int, game_id: int) -> bool:
        """删除游戏"""
        async with db_manager.get_session() as session:
            db_game = await session.get(GameModel, game_id)
            if not db_game or db_game.user_id != user_id:
                raise GameNotFoundError(game_id)
            
            await session.delete(db_game)
            await session.commit()
            return True
    
    # ====================== 书籍管理 ======================
    
    async def get_all_books(self, user_id: int) -> dict:
        """获取用户的所有书籍，按状态分组"""
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(BookModel)
                .where(BookModel.user_id == user_id)
                .order_by(BookModel.created_at.desc())
            )
            db_books = result.scalars().all()
            
            # 按状态分组
            books_by_status = {
                "reading": [],
                "paused": [],
                "reference": [],
                "planned": [],
                "finished": [],
                "dropped": []
            }
            
            for db_book in db_books:
                pydantic_book = self._book_db_to_pydantic(db_book)
                status_key = db_book.status.value
                books_by_status[status_key].append(pydantic_book)
            
            # 对已完成和弃坑的书籍按结束时间排序
            books_by_status["finished"].sort(key=lambda b: b.ended_at or b.created_at, reverse=True)
            books_by_status["dropped"].sort(key=lambda b: b.ended_at or b.created_at, reverse=True)
            
            return books_by_status
    
    async def get_reading_count(self, user_id: int) -> dict:
        """获取用户的阅读计数"""
        async with db_manager.get_session() as session:
            # 获取各状态书籍数量
            reading_count = await self._get_book_count_by_status(session, user_id, BookStatus.READING)
            paused_count = await self._get_book_count_by_status(session, user_id, BookStatus.PAUSED)
            reference_count = await self._get_book_count_by_status(session, user_id, BookStatus.REFERENCE)
            planned_count = await self._get_book_count_by_status(session, user_id, BookStatus.PLANNED)
            
            # 获取阅读限制
            limit = await self._get_user_setting(session, user_id, "book_limit", 3)
            
            return {
                "count": reading_count,
                "limit": limit,
                "paused_count": paused_count,
                "reference_count": reference_count,
                "planned_count": planned_count
            }
    
    async def add_book(self, user_id: int, book_data: BookCreate) -> Book:
        """添加新书籍"""
        async with db_manager.get_session() as session:
            # 检查阅读书籍数量限制
            if book_data.status == BookStatus.READING:
                reading_count = await self._get_book_count_by_status(session, user_id, BookStatus.READING)
                limit = await self._get_user_setting(session, user_id, "book_limit", 3)
                
                if reading_count >= limit:
                    from exceptions import GameTrackerException
                    raise GameTrackerException(f"Cannot exceed reading limit of {limit} books")
            
            # 创建书籍记录
            db_book = BookModel(
                user_id=user_id,
                title=book_data.title,
                author=book_data.author,
                status=book_data.status,
                notes=book_data.notes,
                rating=book_data.rating,
                reason=book_data.reason,
                progress=book_data.progress
            )
            
            session.add(db_book)
            await session.commit()
            await session.refresh(db_book)
            
            return self._book_db_to_pydantic(db_book)
    
    async def update_book(self, user_id: int, book_id: int, updates: BookUpdate) -> Book:
        """更新书籍"""
        async with db_manager.get_session() as session:
            db_book = await session.get(BookModel, book_id)
            if not db_book or db_book.user_id != user_id:
                from exceptions import GameTrackerException
                raise GameTrackerException(f"Book with ID {book_id} not found")
            
            # 检查状态变更的限制
            if updates.status and updates.status != db_book.status:
                if updates.status == BookStatus.READING:
                    reading_count = await self._get_book_count_by_status(session, user_id, BookStatus.READING)
                    limit = await self._get_user_setting(session, user_id, "book_limit", 3)
                    
                    if reading_count >= limit:
                        from exceptions import GameTrackerException
                        raise GameTrackerException(f"Cannot exceed reading limit of {limit} books")
                
                # 设置结束时间
                if updates.status in [BookStatus.FINISHED, BookStatus.DROPPED]:
                    db_book.ended_at = datetime.now()
                elif db_book.status in [BookStatus.FINISHED, BookStatus.DROPPED]:
                    # 从完成/弃读状态变为其他状态，清除结束时间
                    db_book.ended_at = None
            
            # 更新字段
            for field, value in updates.dict(exclude_unset=True).items():
                setattr(db_book, field, value)
            
            await session.commit()
            await session.refresh(db_book)
            
            return self._book_db_to_pydantic(db_book)
    
    async def delete_book(self, user_id: int, book_id: int) -> bool:
        """删除书籍"""
        async with db_manager.get_session() as session:
            db_book = await session.get(BookModel, book_id)
            if not db_book or db_book.user_id != user_id:
                from exceptions import GameTrackerException
                raise GameTrackerException(f"Book with ID {book_id} not found")
            
            await session.delete(db_book)
            await session.commit()
            return True
    
    # ====================== 设置管理 ======================
    
    async def update_game_limit(self, user_id: int, new_limit: int) -> None:
        """更新用户的游戏限制"""
        await self._update_user_setting(user_id, "game_limit", new_limit)
    
    async def update_book_limit(self, user_id: int, new_limit: int) -> None:
        """更新用户的书籍限制"""
        await self._update_user_setting(user_id, "book_limit", new_limit)
    
    async def _update_user_setting(self, user_id: int, key: str, value: int):
        """更新用户设置"""
        async with db_manager.get_session() as session:
            # 查找现有设置
            result = await session.execute(
                select(SettingsModel)
                .where(and_(SettingsModel.user_id == user_id, SettingsModel.key == key))
            )
            setting = result.scalar_one_or_none()
            
            if setting:
                setting.value = value
            else:
                setting = SettingsModel(user_id=user_id, key=key, value=value)
                session.add(setting)
            
            await session.commit()
    
    # ====================== 辅助方法 ======================
    
    async def _get_game_count_by_status(self, session: AsyncSession, user_id: int, status: GameStatus) -> int:
        """获取指定状态的游戏数量"""
        result = await session.execute(
            select(func.count(GameModel.id))
            .where(and_(GameModel.user_id == user_id, GameModel.status == status))
        )
        return result.scalar()
    
    async def _get_book_count_by_status(self, session: AsyncSession, user_id: int, status: BookStatus) -> int:
        """获取指定状态的书籍数量"""
        result = await session.execute(
            select(func.count(BookModel.id))
            .where(and_(BookModel.user_id == user_id, BookModel.status == status))
        )
        return result.scalar()
    
    async def _get_user_setting(self, session: AsyncSession, user_id: int, key: str, default: int) -> int:
        """获取用户设置值"""
        result = await session.execute(
            select(SettingsModel.value)
            .where(and_(SettingsModel.user_id == user_id, SettingsModel.key == key))
        )
        setting = result.scalar_one_or_none()
        return setting if setting is not None else default
    
    async def _check_duplicate_game_name(self, session: AsyncSession, user_id: int, name: str, exclude_id: Optional[int] = None):
        """检查游戏名是否重复"""
        query = select(GameModel).where(
            and_(
                GameModel.user_id == user_id,
                GameModel.name == name,
                GameModel.status == GameStatus.ACTIVE
            )
        )
        
        if exclude_id:
            query = query.where(GameModel.id != exclude_id)
        
        result = await session.execute(query)
        if result.scalar_one_or_none():
            raise DuplicateGameError(name)
    
    def _user_db_to_pydantic(self, db_user: UserModel) -> User:
        """数据库用户模型转换为Pydantic模型"""
        return User(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            is_active=db_user.is_active,
            created_at=db_user.created_at
        )
    
    def _game_db_to_pydantic(self, db_game: GameModel) -> Game:
        """数据库游戏模型转换为Pydantic模型"""
        return Game(
            id=db_game.id,
            user_id=db_game.user_id,
            name=db_game.name,
            status=db_game.status,
            notes=db_game.notes,
            rating=db_game.rating,
            reason=db_game.reason,
            created_at=db_game.created_at,
            ended_at=db_game.ended_at
        )
    
    def _book_db_to_pydantic(self, db_book: BookModel) -> Book:
        """数据库书籍模型转换为Pydantic模型"""
        return Book(
            id=db_book.id,
            user_id=db_book.user_id,
            title=db_book.title,
            author=db_book.author,
            status=db_book.status,
            notes=db_book.notes,
            rating=db_book.rating,
            reason=db_book.reason,
            progress=db_book.progress,
            created_at=db_book.created_at,
            ended_at=db_book.ended_at
        )