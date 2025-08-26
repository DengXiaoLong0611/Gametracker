"""
数据迁移脚本：将JSON数据迁移到PostgreSQL数据库
运行命令：python migrate_json_to_db.py
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

from database import db_manager, initialize_settings
from db_models import GameModel, SettingsModel
from models import GameStatus
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONToDBMigrator:
    """JSON到数据库的数据迁移器"""
    
    def __init__(self, json_file: str = "games_data.json"):
        self.json_file = Path(json_file)
    
    async def migrate(self):
        """执行完整的迁移流程"""
        logger.info("开始数据迁移...")
        
        # 1. 检查JSON文件
        if not self.json_file.exists():
            logger.warning(f"JSON文件 {self.json_file} 不存在，将创建空数据库")
            await self._create_empty_database()
            return
        
        # 2. 读取JSON数据
        json_data = await self._load_json_data()
        if not json_data:
            logger.warning("JSON文件为空或无效，将创建空数据库")
            await self._create_empty_database()
            return
        
        # 3. 初始化数据库
        await db_manager.initialize()
        await db_manager.create_tables()
        
        # 4. 迁移数据
        await self._migrate_games(json_data)
        await self._migrate_settings(json_data)
        
        # 5. 验证迁移结果
        await self._verify_migration(json_data)
        
        logger.info("数据迁移完成！")
    
    async def _load_json_data(self) -> dict:
        """读取JSON数据"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"成功读取JSON文件，包含 {len(data.get('games', {}))} 个游戏")
            return data
        except Exception as e:
            logger.error(f"读取JSON文件失败: {e}")
            return {}
    
    async def _create_empty_database(self):
        """创建空数据库结构"""
        await db_manager.initialize()
        await db_manager.create_tables()
        
        async with db_manager.get_session() as session:
            await initialize_settings(session)
        
        logger.info("创建了空数据库结构")
    
    async def _migrate_games(self, json_data: dict):
        """迁移游戏数据"""
        games_data = json_data.get("games", {})
        if not games_data:
            logger.info("没有游戏数据需要迁移")
            return
        
        async with db_manager.get_session() as session:
            migrated_count = 0
            
            for game_id_str, game_dict in games_data.items():
                try:
                    # 转换datetime字符串
                    created_at = datetime.fromisoformat(game_dict['created_at']) if game_dict.get('created_at') else datetime.now()
                    ended_at = None
                    if game_dict.get('ended_at'):
                        ended_at = datetime.fromisoformat(game_dict['ended_at'])
                    
                    # 创建数据库记录
                    db_game = GameModel(
                        id=int(game_id_str),
                        name=game_dict['name'],
                        status=GameStatus(game_dict['status']),
                        notes=game_dict.get('notes', ''),
                        rating=game_dict.get('rating'),
                        reason=game_dict.get('reason', ''),
                        created_at=created_at,
                        ended_at=ended_at
                    )
                    
                    session.add(db_game)
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(f"迁移游戏 {game_id_str} 失败: {e}")
                    continue
            
            await session.commit()
            logger.info(f"成功迁移了 {migrated_count} 个游戏")
    
    async def _migrate_settings(self, json_data: dict):
        """迁移设置数据"""
        async with db_manager.get_session() as session:
            # 初始化默认设置
            await initialize_settings(session)
            
            # 迁移活跃游戏限制
            limit = json_data.get("limit", 5)
            result = await session.execute(
                select(SettingsModel).where(SettingsModel.key == 'active_limit')
            )
            setting = result.scalar_one_or_none()
            
            if setting:
                setting.value = limit
            else:
                setting = SettingsModel(key='active_limit', value=limit)
                session.add(setting)
            
            await session.commit()
            logger.info(f"迁移设置: 活跃游戏限制 = {limit}")
    
    async def _verify_migration(self, json_data: dict):
        """验证迁移结果"""
        async with db_manager.get_session() as session:
            # 验证游戏数量
            from sqlalchemy import func
            game_count = await session.scalar(select(func.count(GameModel.id)))
            expected_count = len(json_data.get("games", {}))
            
            logger.info(f"数据库中的游戏数量: {game_count}")
            logger.info(f"JSON中的游戏数量: {expected_count}")
            
            if game_count == expected_count:
                logger.info("✅ 游戏数量验证通过")
            else:
                logger.warning("⚠️ 游戏数量不匹配，可能有部分数据迁移失败")
            
            # 验证设置
            result = await session.execute(
                select(SettingsModel.value).where(SettingsModel.key == 'active_limit')
            )
            db_limit = result.scalar_one_or_none()
            json_limit = json_data.get("limit", 5)
            
            if db_limit == json_limit:
                logger.info("✅ 设置迁移验证通过")
            else:
                logger.warning(f"⚠️ 设置不匹配: DB={db_limit}, JSON={json_limit}")
    
    async def backup_json(self):
        """备份原始JSON文件"""
        if self.json_file.exists():
            backup_file = self.json_file.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            self.json_file.rename(backup_file)
            logger.info(f"已备份原始JSON文件到: {backup_file}")

async def main():
    """主函数"""
    # 检查环境变量
    if not os.getenv("DATABASE_URL"):
        logger.error("请设置DATABASE_URL环境变量")
        logger.info("示例: export DATABASE_URL='postgresql://user:pass@localhost:5432/dbname'")
        sys.exit(1)
    
    migrator = JSONToDBMigrator()
    
    # 执行迁移
    try:
        await migrator.migrate()
        
        # 询问是否备份JSON文件
        if migrator.json_file.exists():
            response = input("\n迁移成功！是否要备份原始JSON文件？(y/N): ").strip().lower()
            if response in ('y', 'yes'):
                await migrator.backup_json()
                logger.info("建议在确认数据库工作正常后删除JSON备份文件")
    
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        sys.exit(1)
    
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())