from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime
from enum import Enum

class GameStatus(str, Enum):
    ACTIVE = "active"      # 正在游玩
    PAUSED = "paused"      # 暂时放下（玩累了歇一下，不算弃坑）
    CASUAL = "casual"      # 休闲游戏（可以随时拿起来玩，不涉及剧情通关）
    PLANNED = "planned"    # 未来要玩的游戏（即将进行通关的游戏）
    FINISHED = "finished"  # 已通关
    DROPPED = "dropped"    # 已弃坑

class Game(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=100)
    status: GameStatus
    notes: str = ""
    rating: Optional[int] = Field(None, ge=0, le=10)
    reason: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None

class GameCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    notes: str = ""
    status: GameStatus = GameStatus.ACTIVE
    rating: Optional[int] = Field(None, ge=0, le=10)
    reason: str = ""

class GameUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[GameStatus] = None
    notes: Optional[str] = None
    rating: Optional[int] = Field(None, ge=0, le=10)
    reason: Optional[str] = None

class LimitUpdate(BaseModel):
    limit: int = Field(..., ge=1, le=20)

class GameResponse(BaseModel):
    active: List[Game]     # 正在游玩的游戏
    paused: List[Game]     # 暂时放下的游戏
    casual: List[Game]     # 休闲游戏
    planned: List[Game]    # 未来要玩的游戏
    finished: List[Game]   # 已通关的游戏
    dropped: List[Game]    # 已弃坑的游戏

class ActiveCountResponse(BaseModel):
    count: int             # 正在游玩的游戏数量
    limit: int             # 同时游玩限制
    paused_count: int      # 暂时放下的游戏数量
    casual_count: int      # 休闲游戏数量
    planned_count: int     # 未来要玩的游戏数量

# ================== 书籍阅读追踪器模型 ==================

class BookStatus(str, Enum):
    READING = "reading"       # 正在阅读
    PAUSED = "paused"        # 暂时搁置（暂时没时间读，但计划继续）
    REFERENCE = "reference"   # 工具书（可以随时翻阅，不涉及完整阅读）
    PLANNED = "planned"      # 计划阅读（即将开始阅读的书籍）
    FINISHED = "finished"    # 已读完
    DROPPED = "dropped"      # 已弃读

class Book(BaseModel):
    id: int
    title: str = Field(..., min_length=1, max_length=200)  # 书名长度可以更长
    author: str = Field("", max_length=100)  # 作者
    status: BookStatus
    notes: str = ""
    rating: Optional[int] = Field(None, ge=0, le=10)
    reason: str = ""
    progress: Optional[str] = ""  # 阅读进度，如 "第3章" 或 "120/350页"
    created_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None

class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field("", max_length=100)
    notes: str = ""
    status: BookStatus = BookStatus.READING
    rating: Optional[int] = Field(None, ge=0, le=10)
    reason: str = ""
    progress: Optional[str] = ""

class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, max_length=100)
    status: Optional[BookStatus] = None
    notes: Optional[str] = None
    rating: Optional[int] = Field(None, ge=0, le=10)
    reason: Optional[str] = None
    progress: Optional[str] = None

class BookResponse(BaseModel):
    reading: List[Book]      # 正在阅读的书籍
    paused: List[Book]       # 暂时搁置的书籍
    reference: List[Book]    # 工具书
    planned: List[Book]      # 计划阅读的书籍
    finished: List[Book]     # 已读完的书籍
    dropped: List[Book]      # 已弃读的书籍

class ReadingCountResponse(BaseModel):
    count: int               # 正在阅读的书籍数量
    limit: int               # 同时阅读限制
    paused_count: int        # 暂时搁置的书籍数量
    reference_count: int     # 工具书数量
    planned_count: int       # 计划阅读的书籍数量