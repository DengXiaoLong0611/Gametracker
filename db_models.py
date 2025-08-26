from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

from models import GameStatus

Base = declarative_base()

class GameModel(Base):
    """SQLAlchemy游戏数据模型"""
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    status = Column(Enum(GameStatus), nullable=False, default=GameStatus.ACTIVE, index=True)
    notes = Column(Text, default="")
    rating = Column(Integer, nullable=True)
    reason = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # 约束条件
    __table_args__ = (
        CheckConstraint('LENGTH(TRIM(name)) > 0', name='name_not_empty'),
        CheckConstraint('rating IS NULL OR (rating >= 0 AND rating <= 10)', name='rating_range'),
    )

class SettingsModel(Base):
    """设置表模型"""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False, index=True)
    value = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# 创建索引以提高查询性能
from sqlalchemy import Index

# 复合索引：状态 + 创建时间（用于按状态分组并按时间排序）
Index('idx_games_status_created', GameModel.status, GameModel.created_at.desc())

# 结束时间索引（用于已完成/弃坑游戏的排序）
Index('idx_games_ended_at', GameModel.ended_at.desc(), postgresql_where=GameModel.ended_at.isnot(None))