from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, CheckConstraint, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from models import GameStatus, BookStatus

Base = declarative_base()

class UserModel(Base):
    """用户数据模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    games = relationship("GameModel", back_populates="owner", cascade="all, delete-orphan")
    books = relationship("BookModel", back_populates="owner", cascade="all, delete-orphan")
    
    # 约束条件
    __table_args__ = (
        CheckConstraint('LENGTH(TRIM(username)) >= 2', name='username_min_length'),
        CheckConstraint('LENGTH(TRIM(email)) > 0', name='email_not_empty'),
    )

class GameModel(Base):
    """SQLAlchemy游戏数据模型"""
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    status = Column(Enum(GameStatus), nullable=False, default=GameStatus.ACTIVE, index=True)
    notes = Column(Text, default="")
    rating = Column(Integer, nullable=True)
    reason = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    owner = relationship("UserModel", back_populates="games")
    
    # 约束条件
    __table_args__ = (
        CheckConstraint('LENGTH(TRIM(name)) > 0', name='name_not_empty'),
        CheckConstraint('rating IS NULL OR (rating >= 0 AND rating <= 10)', name='rating_range'),
    )

class BookModel(Base):
    """书籍数据模型"""
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String(200), nullable=False, index=True)
    author = Column(String(100), default="")
    status = Column(Enum(BookStatus), nullable=False, default=BookStatus.READING, index=True)
    notes = Column(Text, default="")
    rating = Column(Integer, nullable=True)
    reason = Column(Text, default="")
    progress = Column(String(100), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    owner = relationship("UserModel", back_populates="books")
    
    # 约束条件
    __table_args__ = (
        CheckConstraint('LENGTH(TRIM(title)) > 0', name='title_not_empty'),
        CheckConstraint('rating IS NULL OR (rating >= 0 AND rating <= 10)', name='book_rating_range'),
    )

class SettingsModel(Base):
    """设置表模型"""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    key = Column(String(50), nullable=False, index=True)
    value = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    owner = relationship("UserModel")
    
    # 约束条件：每个用户的每个设置键唯一
    __table_args__ = (
        CheckConstraint('LENGTH(TRIM(key)) > 0', name='settings_key_not_empty'),
    )

# 创建索引以提高查询性能
from sqlalchemy import Index

# 用户相关索引
Index('idx_users_email', UserModel.email)
Index('idx_users_active', UserModel.is_active)

# 游戏相关索引
Index('idx_games_user_status', GameModel.user_id, GameModel.status)
Index('idx_games_user_created', GameModel.user_id, GameModel.created_at.desc())
Index('idx_games_user_ended', GameModel.user_id, GameModel.ended_at.desc(), 
      postgresql_where=GameModel.ended_at.isnot(None))

# 书籍相关索引
Index('idx_books_user_status', BookModel.user_id, BookModel.status)
Index('idx_books_user_created', BookModel.user_id, BookModel.created_at.desc())
Index('idx_books_user_ended', BookModel.user_id, BookModel.ended_at.desc(), 
      postgresql_where=BookModel.ended_at.isnot(None))

# 设置相关索引
Index('idx_settings_user_key', SettingsModel.user_id, SettingsModel.key, unique=True)