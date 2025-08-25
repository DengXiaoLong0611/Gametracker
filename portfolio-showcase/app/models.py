from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
import enum

Base = declarative_base()

class WorkType(str, PyEnum):
    """作品类型枚举"""
    PHOTO = "photo"
    TEXT = "text" 
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    OTHER = "other"

class WorkStatus(str, PyEnum):
    """作品状态枚举"""
    DRAFT = "draft"          # 草稿
    PUBLISHED = "published"   # 已发布
    ARCHIVED = "archived"     # 已归档
    FEATURED = "featured"     # 精选作品

class Category(Base):
    """作品分类表"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, comment="分类名称")
    description = Column(Text, comment="分类描述") 
    color = Column(String(7), default="#3498db", comment="分类颜色(hex)")
    icon = Column(String(50), comment="分类图标")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Tag(Base):
    """标签表"""
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), unique=True, nullable=False, comment="标签名称")
    color = Column(String(7), default="#95a5a6", comment="标签颜色")
    usage_count = Column(Integer, default=0, comment="使用次数")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Work(Base):
    """作品主表"""
    __tablename__ = "works"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="作品标题")
    description = Column(Text, comment="作品描述")
    content = Column(Text, comment="作品内容/正文")
    
    # 作品属性
    work_type = Column(Enum(WorkType), nullable=False, default=WorkType.OTHER, comment="作品类型")
    status = Column(Enum(WorkStatus), default=WorkStatus.DRAFT, comment="作品状态")
    category_id = Column(Integer, nullable=True, comment="分类ID") 
    
    # 文件信息
    file_path = Column(String(500), comment="文件路径")
    file_name = Column(String(200), comment="原始文件名")
    file_size = Column(Integer, comment="文件大小(bytes)")
    mime_type = Column(String(100), comment="文件MIME类型")
    thumbnail_path = Column(String(500), comment="缩略图路径")
    
    # 媒体信息(图片/视频)
    width = Column(Integer, comment="宽度(像素)")
    height = Column(Integer, comment="高度(像素)")
    duration = Column(Float, comment="时长(秒)")
    
    # 展示设置
    is_featured = Column(Boolean, default=False, comment="是否精选")
    is_public = Column(Boolean, default=True, comment="是否公开")
    view_count = Column(Integer, default=0, comment="浏览次数")
    like_count = Column(Integer, default=0, comment="点赞次数")
    download_count = Column(Integer, default=0, comment="下载次数")
    
    # 排序和元数据
    sort_order = Column(Integer, default=0, comment="排序顺序")
    metadata = Column(Text, comment="额外元数据(JSON)")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    published_at = Column(DateTime(timezone=True), comment="发布时间")

class WorkTag(Base):
    """作品-标签关联表"""
    __tablename__ = "work_tags"
    
    id = Column(Integer, primary_key=True)
    work_id = Column(Integer, nullable=False, comment="作品ID")
    tag_id = Column(Integer, nullable=False, comment="标签ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Settings(Base):
    """系统设置表"""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, comment="设置键")
    value = Column(Text, comment="设置值") 
    description = Column(String(200), comment="设置描述")
    data_type = Column(String(20), default="string", comment="数据类型")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())