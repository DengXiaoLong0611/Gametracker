#!/usr/bin/env python3
"""
数据迁移脚本：将JSON数据迁移到PostgreSQL数据库
"""

import asyncio
import json
import os
import logging
from datetime import datetime
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入项目模块
from database import db_manager, initialize_settings
from db_models import GameModel, SettingsModel
from models import GameStatus
from sqlalchemy import text

async def migrate_json_to_database():
    """将JSON数据迁移到数据库"""
    
    # 检查JSON文件是否存在
    json_file = Path("games_data.json")
    if not json_file.exists():
        logger.error("games_data.json 文件不存在！")
        return False
    
    try:
        # 读取JSON数据
        logger.info("📖 读取JSON数据...")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        games_data = data.get("games", {})
        next_id = data.get("next_id", 1)
        limit = data.get("limit", 5)
        
        logger.info(f"发现 {len(games_data)} 个游戏，下一个ID: {next_id}，限制: {limit}")
        
        # 初始化数据库连接
        logger.info("🔗 连接到数据库...")
        await db_manager.initialize()
        
        # 创建数据库表
        logger.info("📊 创建数据库表...")
        await db_manager.create_tables()
        
        # 获取数据库会话
        async with db_manager.get_session() as session:
            # 初始化设置表
            logger.info("⚙️ 初始化设置...")
            await initialize_settings(session)
            
            # 更新游戏限制设置
            settings_query = await session.execute(
                text("SELECT id FROM settings WHERE key = 'active_game_limit'")
            )
            settings_result = settings_query.first()
            
            if settings_result:
                await session.execute(
                    text("UPDATE settings SET value = :value WHERE key = 'active_game_limit'"),
                    {"value": str(limit)}
                )
                logger.info(f"✅ 更新游戏限制为: {limit}")
            
            # 清空现有游戏数据（如果有的话）
            await session.execute(text("DELETE FROM games"))
            logger.info("🗑️ 清空现有游戏数据")
            
            # 迁移游戏数据
            logger.info("🎮 开始迁移游戏数据...")
            migrated_count = 0
            
            for game_id_str, game_data in games_data.items():
                try:
                    game_id = int(game_id_str)
                    
                    # 解析时间戳
                    created_at = None
                    if game_data.get('created_at'):
                        created_at = datetime.fromisoformat(game_data['created_at'])
                    
                    ended_at = None
                    if game_data.get('ended_at'):
                        ended_at = datetime.fromisoformat(game_data['ended_at'])
                    
                    # 创建游戏对象
                    game = GameModel(
                        id=game_id,
                        name=game_data['name'],
                        status=GameStatus(game_data['status']),
                        notes=game_data.get('notes', ''),
                        rating=game_data.get('rating'),
                        reason=game_data.get('reason', ''),
                        created_at=created_at or datetime.now(),
                        ended_at=ended_at
                    )
                    
                    session.add(game)
                    migrated_count += 1
                    logger.info(f"✅ 迁移游戏: [{game_id}] {game_data['name']} - {game_data['status']}")
                    
                except Exception as e:
                    logger.error(f"❌ 迁移游戏 {game_id_str} 失败: {e}")
                    continue
            
            # 更新序列的下一个值
            if migrated_count > 0:
                max_id = max(int(gid) for gid in games_data.keys())
                new_next_id = max(max_id + 1, next_id)
                
                # 重置序列
                await session.execute(
                    text(f"SELECT setval('games_id_seq', {new_next_id}, false)")
                )
                logger.info(f"🔢 设置下一个游戏ID为: {new_next_id}")
            
            # 提交事务
            await session.commit()
            logger.info(f"💾 成功迁移 {migrated_count} 个游戏到数据库！")
            
            # 验证数据
            logger.info("🔍 验证迁移结果...")
            result = await session.execute(text("SELECT COUNT(*) FROM games"))
            db_count = result.scalar()
            logger.info(f"数据库中游戏总数: {db_count}")
            
            # 按状态统计
            status_stats = await session.execute(text("""
                SELECT status, COUNT(*) as count 
                FROM games 
                GROUP BY status 
                ORDER BY status
            """))
            
            logger.info("📊 游戏状态分布:")
            for row in status_stats:
                logger.info(f"  {row.status}: {row.count}个")
        
        logger.info("🎉 数据迁移完成！")
        return True
        
    except Exception as e:
        logger.error(f"💥 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 关闭数据库连接
        await db_manager.close()

async def test_database_connection():
    """测试数据库连接"""
    try:
        logger.info("🔍 测试数据库连接...")
        await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✅ 数据库连接成功! PostgreSQL版本: {version}")
            
        await db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return False

async def main():
    """主函数"""
    print("游戏追踪器 - JSON到PostgreSQL数据迁移工具")
    print("=" * 50)
    
    # 检查数据库URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("错误: 未设置 DATABASE_URL 环境变量")
        print("请设置: export DATABASE_URL='your_postgresql_url'")
        return
    
    print(f"数据库URL: {db_url[:50]}...")
    
    # 测试数据库连接
    if not await test_database_connection():
        return
    
    # 询问用户确认
    print("\n警告: 此操作将清空数据库中的现有游戏数据并重新导入JSON数据")
    response = input("确定要继续吗? (y/N): ").lower().strip()
    
    if response not in ['y', 'yes']:
        print("用户取消操作")
        return
    
    # 执行迁移
    print("\n开始数据迁移...")
    success = await migrate_json_to_database()
    
    if success:
        print("\n迁移完成! 您的游戏数据现已存储在PostgreSQL数据库中。")
        print("您现在可以在Render等云平台上使用数据库模式了。")
    else:
        print("\n迁移失败，请检查错误信息并重试。")

if __name__ == "__main__":
    asyncio.run(main())