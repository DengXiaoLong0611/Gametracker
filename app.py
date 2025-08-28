from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from pathlib import Path

from models import Game, GameCreate, GameUpdate, LimitUpdate, Book, BookCreate, BookUpdate, BookResponse, ReadingCountResponse
from store_adapter import GameStoreAdapter
from book_store import BookStore
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
book_store = BookStore()

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

@app.get("/reading", response_class=HTMLResponse)
async def reading_tracker(request: Request):
    if app.templates_dir_exists:
        return app.templates.TemplateResponse("reading.html", {"request": request})
    else:
        return HTMLResponse("""
        <html><body>
        <h1>Reading Tracker API</h1>
        <p>Reading tracker is running. Visit <a href="/docs">/docs</a> for API documentation.</p>
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

# ================== 书籍阅读追踪器 API ==================

@app.get("/api/books", response_model=BookResponse)
async def get_books():
    """获取所有书籍，按状态分组"""
    try:
        books_data = book_store.get_all_books()
        return BookResponse(**books_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reading-count", response_model=ReadingCountResponse)
async def get_reading_count():
    """获取当前阅读数量和限制"""
    try:
        count_data = book_store.get_reading_count()
        return ReadingCountResponse(**count_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/books", response_model=Book)
async def create_book(book: BookCreate):
    """创建新书籍"""
    try:
        return book_store.add_book(book)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.patch("/api/books/{book_id}", response_model=Book)
async def update_book(book_id: int, updates: BookUpdate):
    """更新书籍信息"""
    try:
        return book_store.update_book(book_id, updates)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/books/{book_id}")
async def delete_book(book_id: int):
    """删除书籍"""
    try:
        book_store.delete_book(book_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/reading-settings/limit")
async def update_reading_limit(limit_data: LimitUpdate):
    """更新阅读数量限制"""
    try:
        book_store.update_limit(limit_data.limit)
        count_data = book_store.get_reading_count()
        return ReadingCountResponse(**count_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# GitHub同步相关API端点
@app.get("/api/sync/status")
async def get_sync_status():
    """获取GitHub同步状态"""
    try:
        # 调用同步版本的方法
        if store.use_database:
            # 数据库模式暂不支持GitHub同步
            return {
                "enabled": False,
                "reason": "GitHub同步仅在JSON存储模式下可用"
            }
        else:
            return store._store.get_sync_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取同步状态失败: {str(e)}")

@app.post("/api/sync/to-github")
async def sync_to_github():
    """手动同步数据到GitHub"""
    try:
        if store.use_database:
            raise HTTPException(status_code=400, detail="数据库模式下不支持GitHub同步")
        
        success = store._store.manual_sync_to_github()
        if success:
            return {"success": True, "message": "数据已成功同步到GitHub"}
        else:
            return {"success": False, "message": "同步到GitHub失败，请检查配置"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")

@app.post("/api/sync/from-github")
async def sync_from_github():
    """手动从GitHub同步数据"""
    try:
        if store.use_database:
            raise HTTPException(status_code=400, detail="数据库模式下不支持GitHub同步")
        
        success = store._store.manual_sync_from_github()
        if success:
            return {"success": True, "message": "数据已成功从GitHub同步"}
        else:
            return {"success": False, "message": "从GitHub同步失败，请检查配置"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")

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
    
    print(f"Starting Game & Reading Tracker")
    print(f"Environment: {deployment_env}")
    print(f"Server: {host}:{port}")
    print(f"Static files: {Path('static').exists()}")
    print(f"Templates: {Path('templates').exists()}")
    print(f"Debug mode: {debug}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=debug,
        access_log=True,
        log_level="info" if not debug else "debug"
    )