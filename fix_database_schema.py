#!/usr/bin/env python3
"""
修复数据库schema - 创建用户表和更新游戏表结构
适用于生产环境的schema升级
"""

import asyncio
import logging
import os
from sqlalchemy import text
from database import db_manager
from db_models import Base, UserModel
from auth import get_password_hash

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def fix_database_schema():
    """修复数据库schema问题"""
    try:
        logger.info("开始修复数据库schema...")
        
        await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            # 1. 检查当前表结构
            logger.info("检查现有表...")
            result = await session.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            existing_tables = [row[0] for row in result]
            logger.info(f"现有表: {existing_tables}")
            
            # 2. 创建所有表（如果不存在）
            logger.info("创建/更新表结构...")
            async with db_manager.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("表结构创建/更新完成")
            
            # 3. 检查并创建默认用户
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            
            if user_count == 0:
                logger.info("创建默认用户账户...")
                password_hash = get_password_hash("HEROsf4454")
                
                await session.execute(text("""
                    INSERT INTO users (username, email, password_hash, is_active, created_at)
                    VALUES (:username, :email, :password_hash, :is_active, NOW())
                """), {
                    "username": "hero19950611",
                    "email": "382592406@qq.com", 
                    "password_hash": password_hash,
                    "is_active": True
                })
                await session.commit()
                logger.info("默认用户创建成功")
            else:
                logger.info(f"用户表已有 {user_count} 个用户")
            
            # 4. 检查games表是否需要添加user_id字段
            try:
                await session.execute(text("SELECT user_id FROM games LIMIT 1"))
                logger.info("games表已有user_id字段")
            except Exception:
                logger.info("为games表添加user_id字段...")
                await session.execute(text("ALTER TABLE games ADD COLUMN user_id INTEGER"))
                # 将现有游戏关联到默认用户
                await session.execute(text("UPDATE games SET user_id = 1 WHERE user_id IS NULL"))
                await session.execute(text("ALTER TABLE games ALTER COLUMN user_id SET NOT NULL"))
                await session.commit()
                logger.info("games表user_id字段添加完成")
            
            # 5. 检查books表是否需要添加user_id字段
            if 'books' in existing_tables:
                try:
                    await session.execute(text("SELECT user_id FROM books LIMIT 1"))
                    logger.info("books表已有user_id字段")
                except Exception:
                    logger.info("为books表添加user_id字段...")
                    await session.execute(text("ALTER TABLE books ADD COLUMN user_id INTEGER"))
                    await session.execute(text("UPDATE books SET user_id = 1 WHERE user_id IS NULL"))
                    await session.execute(text("ALTER TABLE books ALTER COLUMN user_id SET NOT NULL"))
                    await session.commit()
                    logger.info("books表user_id字段添加完成")
            
            # 6. 创建默认设置
            try:
                result = await session.execute(text("SELECT COUNT(*) FROM settings WHERE user_id = 1"))
                settings_count = result.scalar()
                if settings_count == 0:
                    logger.info("创建默认用户设置...")
                    await session.execute(text("""
                        INSERT INTO settings (user_id, concurrent_game_limit, concurrent_reading_limit, created_at, updated_at)
                        VALUES (1, 5, 3, NOW(), NOW())
                    """))
                    await session.commit()
                    logger.info("默认设置创建成功")
            except Exception as e:
                logger.warning(f"创建设置时出现问题（可能是正常的）: {e}")
            
            logger.info("数据库schema修复完成！")
            
    except Exception as e:
        logger.error(f"修复数据库schema时出错: {e}")
        raise
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(fix_database_schema())