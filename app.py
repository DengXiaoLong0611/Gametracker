from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from pathlib import Path

from models import Game, GameCreate, GameUpdate, LimitUpdate
from store_adapter import GameStoreAdapter
from database import db_manager, initialize_settings
from exceptions import GameTrackerException


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    if store.use_database:
        await db_manager.initialize()
        await db_manager.create_tables()
        async with db_manager.get_session() as session:
            await initialize_settings(session)
    yield
    # 关闭时清理
    if store.use_database:
        await db_manager.close()

# 全局store实例
store = GameStoreAdapter()

# 同步创建app
def create_app_sync() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="游戏追踪器",
        description="管理您的游戏进度",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境中应该设置具体的域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Configure static files and templates
    static_dir = Path("static")
    templates_dir = Path("templates")
    
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory="static"), name="static")
    
    app.templates = Jinja2Templates(directory="templates") if templates_dir.exists() else None
    app.templates_dir_exists = templates_dir.exists()
    
    # 添加安全头
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
    
    return app

app = create_app_sync()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    if app.templates_dir_exists:
        return app.templates.TemplateResponse("index.html", {"request": request})
    else:
        return HTMLResponse("""
        <html><body>
        <h1>Game Tracker API</h1>
        <p>API is running. Visit <a href="/docs">/docs</a> for API documentation.</p>
        </body></html>
        """)

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "message": "游戏追踪器运行正常",
        "active_games": (await store.get_active_count()).get("count", 0),
        "database_mode": store.use_database
    }

@app.get("/api/games")
async def get_games():
    try:
        return await store.get_all_games()
    except GameTrackerException as e:
        raise e.to_http_exception() if hasattr(e, 'to_http_exception') else HTTPException(status_code=500, detail=str(e))

@app.get("/api/active-count")
async def get_active_count():
    try:
        return await store.get_active_count()
    except GameTrackerException as e:
        raise e.to_http_exception() if hasattr(e, 'to_http_exception') else HTTPException(status_code=500, detail=str(e))

@app.post("/api/games", response_model=Game)
async def create_game(game: GameCreate):
    try:
        return await store.add_game(game)
    except GameTrackerException as e:
        raise e.to_http_exception() if hasattr(e, 'to_http_exception') else HTTPException(status_code=500, detail=str(e))

@app.patch("/api/games/{game_id}", response_model=Game)
async def update_game(game_id: int, updates: GameUpdate):
    try:
        return await store.update_game(game_id, updates)
    except GameTrackerException as e:
        raise e.to_http_exception() if hasattr(e, 'to_http_exception') else HTTPException(status_code=500, detail=str(e))

@app.delete("/api/games/{game_id}")
async def delete_game(game_id: int):
    try:
        await store.delete_game(game_id)
        return {"success": True}
    except GameTrackerException as e:
        raise e.to_http_exception() if hasattr(e, 'to_http_exception') else HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings/limit")
async def update_limit(limit_data: LimitUpdate):
    try:
        await store.update_limit(limit_data.limit)
        return await store.get_active_count()
    except GameTrackerException as e:
        raise e.to_http_exception() if hasattr(e, 'to_http_exception') else HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 环境检测和配置
    deployment_env = os.getenv("DEPLOYMENT_ENV", "local")
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    # 端口配置根据部署环境
    if deployment_env == "tencent-container":
        # 腾讯云容器环境
        port = int(os.getenv("PORT", "9000"))
    elif deployment_env == "tencent-scf":
        # 腾讯云云函数环境
        port = int(os.getenv("PORT", "9000"))
    else:
        # 本地开发环境
        port = int(os.getenv("PORT", "8001"))
    
    print(f"🚀 Starting Game Tracker")
    print(f"🌍 Environment: {deployment_env}")
    print(f"📡 Server: {host}:{port}")
    print(f"📁 Static files: {Path('static').exists()}")
    print(f"📄 Templates: {Path('templates').exists()}")
    print(f"🔧 Debug mode: {debug}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=debug,
        access_log=True,
        log_level="info" if not debug else "debug"
    )