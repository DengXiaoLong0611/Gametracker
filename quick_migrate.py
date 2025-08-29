#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速数据迁移脚本 - 为hero19950611用户迁移数据
"""

import asyncio
import json
import os
import logging
from datetime import datetime

# 设置环境变量
os.environ["USE_DATABASE"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./game_tracker.db"

from models import GameCreate, BookCreate, GameStatus, BookStatus, UserCreate
from user_store import MultiUserStore
from auth import get_password_hash
from database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_for_hero():
    """为hero19950611用户迁移数据"""
    
    # 用户信息（您需要修改邮箱和密码）
    USER_EMAIL = "hero19950611@example.com"  # 请修改为您的真实邮箱
    USER_PASSWORD = "your_password_here"      # 请修改为您的密码（至少6位）
    USERNAME = "hero19950611"
    
    print("🎮 开始数据迁移...")
    print(f"👤 用户名: {USERNAME}")
    print(f"📧 邮箱: {USER_EMAIL}")
    print("⚠️  请确保上面的邮箱和密码是您想要的！")
    
    # 初始化数据库
    await db_manager.initialize()
    await db_manager.create_tables()
    
    try:
        user_store = MultiUserStore()
        
        # 创建用户
        user_data = UserCreate(
            username=USERNAME,
            email=USER_EMAIL,
            password=USER_PASSWORD
        )
        password_hash = get_password_hash(USER_PASSWORD)
        
        try:
            user = await user_store.create_user(user_data, password_hash)
            logger.info(f"✅ 用户创建成功: {user.username}")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("用户已存在，获取现有用户...")
                user_model = await user_store.get_user_by_email(USER_EMAIL)
                user = user_store._user_db_to_pydantic(user_model)
            else:
                raise e
        
        # 迁移游戏数据
        games_migrated = 0
        if os.path.exists("games_data.json"):
            with open("games_data.json", 'r', encoding='utf-8') as f:
                games_data = json.load(f)
            
            for status, games_list in games_data.get('games', {}).items():
                for game_data in games_list:
                    try:
                        game_status = getattr(GameStatus, status.upper(), GameStatus.ACTIVE)
                        game_create = GameCreate(
                            name=game_data.get('name', ''),
                            status=game_status,
                            notes=game_data.get('notes', ''),
                            rating=game_data.get('rating'),
                            reason=game_data.get('reason', '')
                        )
                        await user_store.add_game(user.id, game_create)
                        games_migrated += 1
                    except Exception as e:
                        logger.error(f"游戏迁移失败: {game_data.get('name', 'Unknown')} - {str(e)}")
        
        # 迁移书籍数据
        books_migrated = 0
        if os.path.exists("books_data.json"):
            with open("books_data.json", 'r', encoding='utf-8') as f:
                books_data = json.load(f)
            
            for status, books_list in books_data.get('books', {}).items():
                for book_data in books_list:
                    try:
                        book_status = getattr(BookStatus, status.upper(), BookStatus.READING)
                        book_create = BookCreate(
                            title=book_data.get('title', ''),
                            author=book_data.get('author', ''),
                            status=book_status,
                            notes=book_data.get('notes', ''),
                            rating=book_data.get('rating'),
                            reason=book_data.get('reason', ''),
                            progress=book_data.get('progress', '')
                        )
                        await user_store.add_book(user.id, book_create)
                        books_migrated += 1
                    except Exception as e:
                        logger.error(f"书籍迁移失败: {book_data.get('title', 'Unknown')} - {str(e)}")
        
        print("\n" + "=" * 40)
        print("✅ 数据迁移完成！")
        print(f"👤 用户名: {USERNAME}")
        print(f"📧 登录邮箱: {USER_EMAIL}")
        print(f"🔑 登录密码: {USER_PASSWORD}")
        print(f"🎮 迁移游戏: {games_migrated} 个")
        print(f"📚 迁移书籍: {books_migrated} 本")
        print("=" * 40)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        return False
    finally:
        await db_manager.close()

if __name__ == "__main__":
    print("⚠️  请先修改脚本中的 USER_EMAIL 和 USER_PASSWORD！")
    print("位置：第18-19行")
    print("修改完成后请运行此脚本")
    
    # 取消注释下面这行来运行迁移
    # asyncio.run(migrate_for_hero())