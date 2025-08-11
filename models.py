from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

class GameStatus(str, Enum):
    ACTIVE = "active"
    FINISHED = "finished"
    DROPPED = "dropped"

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
    active: list[Game]
    finished: list[Game]
    dropped: list[Game]

class ActiveCountResponse(BaseModel):
    count: int
    limit: int