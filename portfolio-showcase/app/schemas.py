from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class WorkType(str, Enum):
    PHOTO = "photo"
    TEXT = "text"
    VIDEO = "video" 
    AUDIO = "audio"
    DOCUMENT = "document"
    OTHER = "other"

class WorkStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    FEATURED = "featured"

# 分类相关Schema
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    color: str = Field("#3498db", regex=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None
    sort_order: int = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    color: Optional[str] = Field(None, regex=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None
    sort_order: Optional[int] = None

class Category(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 标签相关Schema
class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=30)
    color: str = Field("#95a5a6", regex=r"^#[0-9A-Fa-f]{6}$")

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int
    usage_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True

# 作品相关Schema  
class WorkBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = None
    work_type: WorkType
    status: WorkStatus = WorkStatus.DRAFT
    category_id: Optional[int] = None
    is_featured: bool = False
    is_public: bool = True
    sort_order: int = 0

class WorkCreate(WorkBase):
    tag_ids: Optional[List[int]] = []

class WorkUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = None
    work_type: Optional[WorkType] = None
    status: Optional[WorkStatus] = None
    category_id: Optional[int] = None
    is_featured: Optional[bool] = None
    is_public: Optional[bool] = None
    sort_order: Optional[int] = None
    tag_ids: Optional[List[int]] = None

class WorkSummary(BaseModel):
    """作品摘要信息(列表页用)"""
    id: int
    title: str
    description: Optional[str]
    work_type: WorkType
    status: WorkStatus
    category: Optional[Category] = None
    tags: List[Tag] = []
    thumbnail_path: Optional[str] = None
    is_featured: bool
    is_public: bool
    view_count: int
    like_count: int
    created_at: datetime
    published_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Work(WorkBase):
    """完整作品信息"""
    id: int
    category: Optional[Category] = None
    tags: List[Tag] = []
    
    # 文件信息
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    thumbnail_path: Optional[str] = None
    
    # 媒体信息
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    
    # 统计信息
    view_count: int = 0
    like_count: int = 0
    download_count: int = 0
    
    # 时间戳
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    
    # 额外元数据
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# 文件上传Schema
class FileUploadResponse(BaseModel):
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    thumbnail_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None

# 系统设置Schema
class SettingBase(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    value: Optional[str] = None
    description: Optional[str] = None
    data_type: str = "string"

class SettingCreate(SettingBase):
    pass

class SettingUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None

class Setting(SettingBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# API响应Schema
class WorkListResponse(BaseModel):
    works: List[WorkSummary]
    total: int
    page: int
    per_page: int
    total_pages: int

class StatsResponse(BaseModel):
    total_works: int
    published_works: int
    draft_works: int
    total_views: int
    total_likes: int
    categories_count: int
    tags_count: int