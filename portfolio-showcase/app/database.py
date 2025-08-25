from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from typing import Generator

# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./database/portfolio.db"  # 默认使用SQLite
)

# 支持多种数据库
if DATABASE_URL.startswith("sqlite"):
    # SQLite配置
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )
else:
    # PostgreSQL/MySQL配置
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """创建所有数据库表"""
    from .models import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

def init_database():
    """初始化数据库数据"""
    from sqlalchemy.orm import Session
    from .models import Category, Tag, Settings
    
    db = SessionLocal()
    try:
        # 检查是否已初始化
        if db.query(Settings).filter(Settings.key == "initialized").first():
            print("📊 Database already initialized")
            return
            
        # 创建默认分类
        default_categories = [
            {"name": "摄影作品", "description": "照片和摄影相关作品", "color": "#e74c3c", "icon": "📸"},
            {"name": "文字创作", "description": "文章、诗歌、小说等文字作品", "color": "#3498db", "icon": "📝"},
            {"name": "视频作品", "description": "视频、动画等影像作品", "color": "#9b59b6", "icon": "🎬"},
            {"name": "音频作品", "description": "音乐、播客等音频作品", "color": "#1abc9c", "icon": "🎵"},
            {"name": "设计作品", "description": "平面设计、UI设计等", "color": "#f39c12", "icon": "🎨"},
        ]
        
        for i, cat_data in enumerate(default_categories):
            category = Category(
                name=cat_data["name"],
                description=cat_data["description"], 
                color=cat_data["color"],
                icon=cat_data["icon"],
                sort_order=i
            )
            db.add(category)
            
        # 创建默认标签
        default_tags = [
            {"name": "原创", "color": "#e74c3c"},
            {"name": "精选", "color": "#f39c12"},
            {"name": "摄影", "color": "#3498db"},
            {"name": "生活", "color": "#2ecc71"},
            {"name": "旅行", "color": "#9b59b6"},
            {"name": "艺术", "color": "#e67e22"},
            {"name": "技术", "color": "#34495e"},
            {"name": "随笔", "color": "#95a5a6"},
        ]
        
        for tag_data in default_tags:
            tag = Tag(
                name=tag_data["name"],
                color=tag_data["color"]
            )
            db.add(tag)
            
        # 创建默认设置
        default_settings = [
            {"key": "site_title", "value": "我的作品集", "description": "网站标题"},
            {"key": "site_description", "value": "展示我的创作作品", "description": "网站描述"},
            {"key": "items_per_page", "value": "12", "description": "每页显示作品数量", "data_type": "integer"},
            {"key": "allow_public_view", "value": "true", "description": "允许公开访问", "data_type": "boolean"},
            {"key": "show_view_count", "value": "true", "description": "显示浏览次数", "data_type": "boolean"},
            {"key": "initialized", "value": "true", "description": "数据库初始化标记", "data_type": "boolean"},
        ]
        
        for setting_data in default_settings:
            setting = Settings(
                key=setting_data["key"],
                value=setting_data["value"],
                description=setting_data["description"],
                data_type=setting_data.get("data_type", "string")
            )
            db.add(setting)
            
        db.commit()
        print("🎯 Database initialized with default data")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Failed to initialize database: {e}")
        raise
    finally:
        db.close()