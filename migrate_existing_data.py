#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
现有数据迁移脚本
将JSON文件中的游戏和书籍数据迁移到指定用户账户下
"""

import asyncio
import json
import os
import logging
from datetime import datetime
from typing import Optional

from models import GameCreate, BookCreate, GameStatus, BookStatus
from user_store import MultiUserStore
from auth import get_password_hash
from database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataMigrator:
    """数据迁移器"""
    
    def __init__(self):
        self.user_store = MultiUserStore()
    
    async def migrate_data_to_user(
        self, 
        user_email: str, 
        user_password: str, 
        username: str = "游戏追踪器原主人"
    ):
        """将现有JSON数据迁移到指定用户"""
        
        logger.info("开始数据迁移流程...")
        
        # 初始化数据库
        await db_manager.initialize()
        await db_manager.create_tables()
        
        try:
            # 1. 创建或获取用户
            user = await self._get_or_create_user(user_email, user_password, username)
            logger.info(f"用户准备完毕: {user.username} ({user.email})")
            
            # 2. 迁移游戏数据
            games_migrated = await self._migrate_games(user.id)
            logger.info(f"游戏数据迁移完成: {games_migrated} 个游戏")
            
            # 3. 迁移书籍数据
            books_migrated = await self._migrate_books(user.id)
            logger.info(f"书籍数据迁移完成: {books_migrated} 本书籍")
            
            logger.info("✅ 数据迁移成功完成！")
            logger.info(f"📧 登录邮箱: {user_email}")
            logger.info(f"🔑 登录密码: {user_password}")
            logger.info(f"🎮 已迁移游戏: {games_migrated} 个")
            logger.info(f"📚 已迁移书籍: {books_migrated} 本")
            
            return {
                "user_id": user.id,
                "email": user_email,
                "games_migrated": games_migrated,
                "books_migrated": books_migrated
            }
            
        except Exception as e:
            logger.error(f"迁移过程中出现错误: {str(e)}")
            raise
        finally:
            await db_manager.close()
    
    async def _get_or_create_user(self, email: str, password: str, username: str):
        """获取或创建用户"""
        # 检查用户是否已存在
        existing_user = await self.user_store.get_user_by_email(email)
        if existing_user:
            logger.info(f"用户已存在: {email}")
            return self.user_store._user_db_to_pydantic(existing_user)
        
        # 创建新用户
        from models import UserCreate
        user_data = UserCreate(
            username=username,
            email=email,
            password=password
        )
        password_hash = get_password_hash(password)
        user = await self.user_store.create_user(user_data, password_hash)
        logger.info(f"新用户创建成功: {email}")
        return user
    
    async def _migrate_games(self, user_id: int) -> int:
        """迁移游戏数据"""
        games_file = "games_data.json"
        if not os.path.exists(games_file):
            logger.warning(f"游戏数据文件 {games_file} 不存在，跳过游戏迁移")
            return 0
        
        try:
            with open(games_file, 'r', encoding='utf-8') as f:
                games_data = json.load(f)
            
            migrated_count = 0
            
            # 遍历所有状态的游戏
            for status, games_list in games_data.get('games', {}).items():
                for game_data in games_list:
                    try:
                        # 转换状态枚举
                        game_status = self._convert_game_status(status)
                        
                        # 创建游戏对象
                        game_create = GameCreate(
                            name=game_data.get('name', ''),
                            status=game_status,
                            notes=game_data.get('notes', ''),
                            rating=game_data.get('rating'),
                            reason=game_data.get('reason', '')
                        )
                        
                        # 添加到用户账户
                        await self.user_store.add_game(user_id, game_create)
                        migrated_count += 1
                        logger.debug(f"迁移游戏: {game_data.get('name')}")
                        
                    except Exception as e:
                        logger.error(f"迁移游戏失败 {game_data.get('name', 'Unknown')}: {str(e)}")
                        continue
            
            return migrated_count
            
        except Exception as e:
            logger.error(f"读取游戏数据文件失败: {str(e)}")
            return 0
    
    async def _migrate_books(self, user_id: int) -> int:
        """迁移书籍数据"""
        books_file = "books_data.json"
        if not os.path.exists(books_file):
            logger.warning(f"书籍数据文件 {books_file} 不存在，跳过书籍迁移")
            return 0
        
        try:
            with open(books_file, 'r', encoding='utf-8') as f:
                books_data = json.load(f)
            
            migrated_count = 0
            
            # 遍历所有状态的书籍
            for status, books_list in books_data.get('books', {}).items():
                for book_data in books_list:
                    try:
                        # 转换状态枚举
                        book_status = self._convert_book_status(status)
                        
                        # 创建书籍对象
                        book_create = BookCreate(
                            title=book_data.get('title', ''),
                            author=book_data.get('author', ''),
                            status=book_status,
                            notes=book_data.get('notes', ''),
                            rating=book_data.get('rating'),
                            reason=book_data.get('reason', ''),
                            progress=book_data.get('progress', '')
                        )
                        
                        # 添加到用户账户
                        await self.user_store.add_book(user_id, book_create)
                        migrated_count += 1
                        logger.debug(f"迁移书籍: {book_data.get('title')}")
                        
                    except Exception as e:
                        logger.error(f"迁移书籍失败 {book_data.get('title', 'Unknown')}: {str(e)}")
                        continue
            
            return migrated_count
            
        except Exception as e:
            logger.error(f"读取书籍数据文件失败: {str(e)}")
            return 0
    
    def _convert_game_status(self, status_str: str) -> GameStatus:
        """转换游戏状态字符串为枚举"""
        status_mapping = {
            'active': GameStatus.ACTIVE,
            'paused': GameStatus.PAUSED,
            'casual': GameStatus.CASUAL,
            'planned': GameStatus.PLANNED,
            'finished': GameStatus.FINISHED,
            'dropped': GameStatus.DROPPED
        }
        return status_mapping.get(status_str, GameStatus.ACTIVE)
    
    def _convert_book_status(self, status_str: str) -> BookStatus:
        """转换书籍状态字符串为枚举"""
        status_mapping = {
            'reading': BookStatus.READING,
            'paused': BookStatus.PAUSED,
            'reference': BookStatus.REFERENCE,
            'planned': BookStatus.PLANNED,
            'finished': BookStatus.FINISHED,
            'dropped': BookStatus.DROPPED
        }
        return status_mapping.get(status_str, BookStatus.READING)

async def main():
    """主迁移函数"""
    print("🎮 游戏追踪器数据迁移工具")
    print("=" * 40)
    print("⚠️  重要说明：")
    print("   - 数据只会迁移到您指定的邮箱账户")
    print("   - 其他用户不会看到您的数据")
    print("   - 如果该邮箱账户不存在，会自动创建")
    print("=" * 40)
    
    # 获取用户输入
    email = input("请输入您的邮箱（用于登录）: ").strip()
    password = input("请输入您的登录密码（至少6位）: ").strip()
    username = input("请输入用户名（推荐：hero19950611）: ").strip()
    
    if not email or not password:
        print("❌ 邮箱和密码不能为空！")
        return
    
    if len(password) < 6:
        print("❌ 密码长度至少6位！")
        return
    
    if not username:
        username = "hero19950611"  # 默认使用您建议的用户名
    
    # 设置数据库模式
    os.environ["USE_DATABASE"] = "true"
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite:///./game_tracker.db"  # 默认使用SQLite
    
    print(f"\n📧 邮箱: {email}")
    print(f"👤 用户名: {username}")
    print(f"💾 数据库: {os.getenv('DATABASE_URL')}")
    
    confirm = input("\n确认开始迁移吗？(y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ 迁移已取消")
        return
    
    # 开始迁移
    migrator = DataMigrator()
    try:
        result = await migrator.migrate_data_to_user(email, password, username)
        
        print("\n" + "=" * 40)
        print("✅ 迁移完成！")
        print(f"📧 登录邮箱: {result['email']}")
        print(f"🎮 迁移游戏: {result['games_migrated']} 个")
        print(f"📚 迁移书籍: {result['books_migrated']} 本")
        print("\n现在您可以使用上述邮箱和密码登录系统了！")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())