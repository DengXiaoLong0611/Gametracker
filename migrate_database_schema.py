#!/usr/bin/env python3
"""
数据库模式迁移脚本 - 添加user_id列和用户表
用于将旧的数据库模式升级到支持多用户的新模式
"""

import asyncio
import os
import logging
from database import db_manager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_database_schema():
    """迁移数据库模式"""
    
    try:
        await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            # 检查用户表是否存在
            users_table_check = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                );
            """))
            users_table_exists = users_table_check.scalar()
            
            if not users_table_exists:
                logger.info("创建用户表...")
                await session.execute(text("""
                    CREATE TABLE users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        is_active BOOLEAN DEFAULT true NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        CONSTRAINT username_min_length CHECK (LENGTH(TRIM(username)) >= 2),
                        CONSTRAINT email_not_empty CHECK (LENGTH(TRIM(email)) > 0)
                    );
                """))
                
                # 创建索引
                await session.execute(text("CREATE INDEX ix_users_id ON users (id);"))
                await session.execute(text("CREATE INDEX ix_users_email ON users (email);"))
                logger.info("✅ 用户表创建成功")
            else:
                logger.info("✅ 用户表已存在")
            
            # 检查games表的user_id列是否存在
            games_user_id_check = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'games' AND column_name = 'user_id'
                );
            """))
            games_user_id_exists = games_user_id_check.scalar()
            
            if not games_user_id_exists:
                logger.info("为games表添加user_id列...")
                
                # 创建默认用户（如果需要）
                default_user_check = await session.execute(text("""
                    SELECT id FROM users WHERE email = 'default@gametracker.com' LIMIT 1;
                """))
                default_user_id = default_user_check.scalar()
                
                if not default_user_id:
                    logger.info("创建默认用户...")
                    result = await session.execute(text("""
                        INSERT INTO users (username, email, password_hash) 
                        VALUES ('default_user', 'default@gametracker.com', '$2b$12$defaulthash') 
                        RETURNING id;
                    """))
                    default_user_id = result.scalar()
                    logger.info(f"✅ 默认用户创建成功，ID: {default_user_id}")
                
                # 添加user_id列
                await session.execute(text(f"""
                    ALTER TABLE games ADD COLUMN user_id INTEGER NOT NULL DEFAULT {default_user_id};
                """))
                
                # 添加外键约束
                await session.execute(text("""
                    ALTER TABLE games ADD CONSTRAINT fk_games_user_id 
                    FOREIGN KEY (user_id) REFERENCES users(id);
                """))
                
                # 创建索引
                await session.execute(text("CREATE INDEX ix_games_user_id ON games (user_id);"))
                logger.info("✅ games表user_id列添加成功")
            else:
                logger.info("✅ games表已有user_id列")
            
            # 检查books表是否存在以及user_id列
            books_table_check = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'books'
                );
            """))
            books_table_exists = books_table_check.scalar()
            
            if not books_table_exists:
                logger.info("创建books表...")
                await session.execute(text("""
                    CREATE TYPE bookstatus AS ENUM ('reading', 'paused', 'reference', 'planned', 'finished', 'dropped');
                """))
                
                await session.execute(text("""
                    CREATE TABLE books (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        title VARCHAR(200) NOT NULL,
                        author VARCHAR(100) DEFAULT '',
                        status bookstatus DEFAULT 'reading' NOT NULL,
                        notes TEXT DEFAULT '',
                        rating INTEGER,
                        reason TEXT DEFAULT '',
                        progress VARCHAR(100) DEFAULT '',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        ended_at TIMESTAMP WITH TIME ZONE,
                        CONSTRAINT books_rating_range CHECK (rating >= 0 AND rating <= 10)
                    );
                """))
                
                # 创建索引
                await session.execute(text("CREATE INDEX ix_books_id ON books (id);"))
                await session.execute(text("CREATE INDEX ix_books_user_id ON books (user_id);"))
                await session.execute(text("CREATE INDEX ix_books_title ON books (title);"))
                await session.execute(text("CREATE INDEX ix_books_status ON books (status);"))
                logger.info("✅ books表创建成功")
            else:
                # 检查books表的user_id列
                books_user_id_check = await session.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'books' AND column_name = 'user_id'
                    );
                """))
                books_user_id_exists = books_user_id_check.scalar()
                
                if not books_user_id_exists:
                    logger.info("为books表添加user_id列...")
                    await session.execute(text(f"""
                        ALTER TABLE books ADD COLUMN user_id INTEGER NOT NULL DEFAULT {default_user_id};
                    """))
                    await session.execute(text("""
                        ALTER TABLE books ADD CONSTRAINT fk_books_user_id 
                        FOREIGN KEY (user_id) REFERENCES users(id);
                    """))
                    await session.execute(text("CREATE INDEX ix_books_user_id ON books (user_id);"))
                    logger.info("✅ books表user_id列添加成功")
                else:
                    logger.info("✅ books表已有user_id列")
            
            # 检查settings表
            settings_table_check = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'settings'
                );
            """))
            settings_table_exists = settings_table_check.scalar()
            
            if not settings_table_exists:
                logger.info("创建settings表...")
                await session.execute(text("""
                    CREATE TABLE settings (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        key VARCHAR(50) NOT NULL,
                        value INTEGER NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        UNIQUE(user_id, key)
                    );
                """))
                
                await session.execute(text("CREATE INDEX ix_settings_id ON settings (id);"))
                await session.execute(text("CREATE INDEX ix_settings_user_id ON settings (user_id);"))
                logger.info("✅ settings表创建成功")
            else:
                logger.info("✅ settings表已存在")
            
            await session.commit()
            logger.info("🎉 数据库模式迁移完成!")
            
    except Exception as e:
        logger.error(f"❌ 数据库迁移失败: {str(e)}")
        return False
    finally:
        await db_manager.close()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(migrate_database_schema())
    if success:
        print("✅ 数据库迁移成功完成!")
    else:
        print("❌ 数据库迁移失败!")
        exit(1)