"""
部署脚本 - 自动执行数据迁移和应用启动
运行命令: python deploy.py
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

from migrate_json_to_db import JSONToDBMigrator
from database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def deploy():
    """执行完整的部署流程"""
    logger.info("🚀 开始部署游戏追踪器...")
    
    # 1. 检查环境
    if not os.getenv("DATABASE_URL") and not os.getenv("USE_DATABASE"):
        logger.info("📄 未检测到数据库配置，将使用JSON文件模式")
        return
    
    if not os.getenv("DATABASE_URL"):
        logger.error("❌ 数据库模式需要设置 DATABASE_URL 环境变量")
        sys.exit(1)
    
    logger.info("🗄️ 检测到数据库配置，开始数据库初始化...")
    
    try:
        # 2. 测试数据库连接
        await db_manager.initialize()
        if not await db_manager.health_check():
            logger.error("❌ 数据库连接失败")
            sys.exit(1)
        logger.info("✅ 数据库连接正常")
        
        # 3. 创建表结构
        await db_manager.create_tables()
        logger.info("✅ 数据库表结构创建完成")
        
        # 4. 检查是否需要迁移数据
        json_file = Path("games_data.json")
        if json_file.exists():
            logger.info("📦 发现现有JSON数据，开始迁移...")
            migrator = JSONToDBMigrator()
            await migrator.migrate()
            logger.info("✅ 数据迁移完成")
        else:
            logger.info("📝 未发现现有数据，将使用空数据库")
        
        logger.info("🎉 部署完成！应用已准备就绪")
        
    except Exception as e:
        logger.error(f"❌ 部署失败: {e}")
        sys.exit(1)
    
    finally:
        await db_manager.close()

def main():
    """主函数"""
    asyncio.run(deploy())

if __name__ == "__main__":
    main()