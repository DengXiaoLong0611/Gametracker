"""
用户认证和授权模块
包含密码加密、JWT令牌生成/验证、用户依赖注入等功能
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from database import db_manager
from models import User, TokenData
from db_models import UserModel
from store_adapter import GameStoreAdapter

# 密码加密配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

# HTTP Bearer认证
security = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """加密密码"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[TokenData]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        token_data = TokenData(user_id=user_id)
        return token_data
    except JWTError:
        return None

async def get_user_by_id(user_id: int) -> Optional[User]:
    """根据用户ID获取用户"""
    # 检查是否使用数据库模式
    store_adapter = GameStoreAdapter()
    if store_adapter.use_database:
        async with db_manager.get_session() as session:
            result = await session.get(UserModel, user_id)
            if result:
                return User(
                    id=result.id,
                    username=result.username,
                    email=result.email,
                    is_active=result.is_active,
                    created_at=result.created_at
                )
            return None
    else:
        # JSON模式：使用默认用户
        if user_id == 1:
            return User(
                id=1,
                username="hero19950611",
                email="382592406@qq.com",
                is_active=True,
                created_at=datetime.utcnow()
            )
        return None

async def get_user_by_email(email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    store_adapter = GameStoreAdapter()
    if store_adapter.use_database:
        from sqlalchemy import select
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            user_model = result.scalar_one_or_none()
            if user_model:
                return User(
                    id=user_model.id,
                    username=user_model.username,
                    email=user_model.email,
                    is_active=user_model.is_active,
                    created_at=user_model.created_at
                )
            return None
    else:
        # JSON模式：硬编码默认用户
        if email == "382592406@qq.com":
            return User(
                id=1,
                username="hero19950611",
                email="382592406@qq.com",
                is_active=True,
                created_at=datetime.utcnow()
            )
        return None

async def authenticate_user(email: str, password: str) -> Optional[User]:
    """验证用户登录凭证"""
    store_adapter = GameStoreAdapter()
    if store_adapter.use_database:
        user_by_email = await get_user_by_email(email)
        if not user_by_email:
            return None
        # 需要获取数据库中的密码哈希进行验证
        async with db_manager.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            user_model = result.scalar_one_or_none()
            if not user_model:
                return None
            if not verify_password(password, user_model.password_hash):
                return None
            if not user_model.is_active:
                return None
            return user_by_email
    else:
        # JSON模式：硬编码认证
        if email == "382592406@qq.com" and password == "HEROsf4454":
            return User(
                id=1,
                username="hero19950611",
                email="382592406@qq.com",
                is_active=True,
                created_at=datetime.utcnow()
            )
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """获取当前登录用户的依赖注入函数"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    token_data = verify_token(credentials.credentials)
    if token_data is None or token_data.user_id is None:
        raise credentials_exception
    
    user = await get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception
    
    # 转换为Pydantic模型
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at
    )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )
    return current_user