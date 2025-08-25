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