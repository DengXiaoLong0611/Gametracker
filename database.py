import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
import asyncio
import logging

from db_models import Base

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """数据库配置管理"""
    
    def __init__(self):
        # 从环境变量读取数据库配置
        self.database_url = self._get_database_url()
        self.echo = os.getenv("DB_ECHO", "false").lower() == "true"
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        
    def _get_database_url(self) -> str:
        """构建数据库连接URL"""
        # Render PostgreSQL URL (优先)
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            # Render提供的URL通常是postgres://，需要转换为asyncpg格式
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return database_url
        
        # 手动构建URL（本地开发）
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "password")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        database = os.getenv("DB_NAME", "game_tracker")
        
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.engine = None
        self.async_session_factory = None
        self._initialized = False
        
    async def initialize(self):
        """初始化数据库连接"""
        if self._initialized:
            return
            
        try:
            # 创建异步引擎
            self.engine = create_async_engine(
                self.config.database_url,
                echo=self.config.echo,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_pre_ping=True,  # 连接健康检查
                pool_recycle=3600,   # 1小时后回收连接
            )
            
            # 创建会话工厂
            self.async_session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            
            self._initialized = True
            logger.info(f"Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def create_tables(self):
        """创建数据库表"""
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话上下文管理器"""
        if not self._initialized:
            await self.initialize()
            
        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """数据库健康检查"""
        try:
            from sqlalchemy import text
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# 全局数据库管理器实例
db_manager = DatabaseManager()

# 便捷的会话获取函数
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（用于FastAPI依赖注入）"""
    async with db_manager.get_session() as session:
        yield session

# 初始化设置的函数
async def initialize_settings(session: AsyncSession):
    """初始化默认设置 - 现在设置是按用户管理的，所以这里不做全局初始化"""
    # 新的多用户系统中，设置是在用户创建时初始化的
    # 这个函数暂时保留为空，保持向后兼容
    logger.info("Settings initialization skipped - using per-user settings")