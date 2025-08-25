from fastapi import FastAPI, Request, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
import shutil
import uuid
from pathlib import Path
import mimetypes
from PIL import Image
import json

from .database import get_db, create_tables, init_database
from .models import Work, Category, Tag, WorkTag, Settings, WorkType, WorkStatus
from .schemas import (
    WorkCreate, WorkUpdate, Work as WorkSchema, WorkSummary, WorkListResponse,
    CategoryCreate, CategoryUpdate, Category as CategorySchema,
    TagCreate, Tag as TagSchema,
    FileUploadResponse, StatsResponse
)

def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="作品集展示系统",
        description="个人作品展示和管理平台",
        version="1.0.0",
        docs_url="/admin/docs",  # 管理后台API文档
        redoc_url="/admin/redoc"
    )
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 静态文件和模板
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.templates = Jinja2Templates(directory="templates")
    
    # 确保上传目录存在
    upload_dir = Path("static/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    return app

app = create_app()

# 启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    create_tables()
    init_database()

# ==================== 前端页面路由 ====================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """首页 - 作品展示"""
    # 获取精选作品
    featured_works = db.query(Work).filter(
        Work.is_featured == True,
        Work.is_public == True,
        Work.status == WorkStatus.PUBLISHED
    ).order_by(Work.sort_order, Work.created_at.desc()).limit(6).all()
    
    # 获取最新作品
    recent_works = db.query(Work).filter(
        Work.is_public == True,
        Work.status == WorkStatus.PUBLISHED
    ).order_by(Work.created_at.desc()).limit(12).all()
    
    # 获取分类
    categories = db.query(Category).order_by(Category.sort_order).all()
    
    return app.templates.TemplateResponse("index.html", {
        "request": request,
        "featured_works": featured_works,
        "recent_works": recent_works,
        "categories": categories
    })

@app.get("/works", response_class=HTMLResponse)
async def works_page(
    request: Request,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """作品列表页"""
    query = db.query(Work).filter(
        Work.is_public == True,
        Work.status == WorkStatus.PUBLISHED
    )
    
    # 分类筛选
    if category:
        cat = db.query(Category).filter(Category.name == category).first()
        if cat:
            query = query.filter(Work.category_id == cat.id)
    
    # 标签筛选
    if tag:
        tag_obj = db.query(Tag).filter(Tag.name == tag).first()
        if tag_obj:
            query = query.join(WorkTag).filter(WorkTag.tag_id == tag_obj.id)
    
    # 搜索
    if search:
        query = query.filter(Work.title.contains(search) | Work.description.contains(search))
    
    works = query.order_by(Work.sort_order, Work.created_at.desc()).all()
    categories = db.query(Category).order_by(Category.sort_order).all()
    popular_tags = db.query(Tag).order_by(Tag.usage_count.desc()).limit(20).all()
    
    return app.templates.TemplateResponse("works.html", {
        "request": request,
        "works": works,
        "categories": categories,
        "popular_tags": popular_tags,
        "current_category": category,
        "current_tag": tag,
        "search_query": search
    })

@app.get("/work/{work_id}", response_class=HTMLResponse)
async def work_detail(request: Request, work_id: int, db: Session = Depends(get_db)):
    """作品详情页"""
    work = db.query(Work).filter(Work.id == work_id, Work.is_public == True).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")
    
    # 增加浏览次数
    work.view_count += 1
    db.commit()
    
    # 获取相关作品
    related_works = db.query(Work).filter(
        Work.category_id == work.category_id,
        Work.id != work_id,
        Work.is_public == True,
        Work.status == WorkStatus.PUBLISHED
    ).limit(6).all()
    
    return app.templates.TemplateResponse("work_detail.html", {
        "request": request,
        "work": work,
        "related_works": related_works
    })

@app.get("/admin", response_class=HTMLResponse) 
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """管理后台首页"""
    stats = get_stats(db)
    recent_works = db.query(Work).order_by(Work.created_at.desc()).limit(10).all()
    
    return app.templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_works": recent_works
    })

# ==================== API路由 ====================

@app.get("/api/works", response_model=WorkListResponse)
async def get_works(
    page: int = 1,
    per_page: int = 12,
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    work_type: Optional[WorkType] = None,
    status: Optional[WorkStatus] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取作品列表"""
    query = db.query(Work)
    
    if category_id:
        query = query.filter(Work.category_id == category_id)
    if tag_id:
        query = query.join(WorkTag).filter(WorkTag.tag_id == tag_id)
    if work_type:
        query = query.filter(Work.work_type == work_type)
    if status:
        query = query.filter(Work.status == status)
    if search:
        query = query.filter(Work.title.contains(search) | Work.description.contains(search))
    
    total = query.count()
    works = query.order_by(Work.sort_order, Work.created_at.desc())\
                .offset((page - 1) * per_page)\
                .limit(per_page).all()
    
    return WorkListResponse(
        works=works,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page
    )

@app.post("/api/works", response_model=WorkSchema)
async def create_work(work: WorkCreate, db: Session = Depends(get_db)):
    """创建作品"""
    db_work = Work(**work.dict(exclude={"tag_ids"}))
    db.add(db_work)
    db.commit()
    db.refresh(db_work)
    
    # 添加标签关联
    if work.tag_ids:
        for tag_id in work.tag_ids:
            work_tag = WorkTag(work_id=db_work.id, tag_id=tag_id)
            db.add(work_tag)
        db.commit()
    
    return db_work

@app.get("/api/works/{work_id}", response_model=WorkSchema)
async def get_work(work_id: int, db: Session = Depends(get_db)):
    """获取单个作品"""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")
    return work

@app.put("/api/works/{work_id}", response_model=WorkSchema)
async def update_work(work_id: int, work: WorkUpdate, db: Session = Depends(get_db)):
    """更新作品"""
    db_work = db.query(Work).filter(Work.id == work_id).first()
    if not db_work:
        raise HTTPException(status_code=404, detail="作品不存在")
    
    # 更新基本信息
    update_data = work.dict(exclude_unset=True, exclude={"tag_ids"})
    for field, value in update_data.items():
        setattr(db_work, field, value)
    
    # 更新标签关联
    if work.tag_ids is not None:
        # 删除现有标签关联
        db.query(WorkTag).filter(WorkTag.work_id == work_id).delete()
        # 添加新的标签关联
        for tag_id in work.tag_ids:
            work_tag = WorkTag(work_id=work_id, tag_id=tag_id)
            db.add(work_tag)
    
    db.commit()
    db.refresh(db_work)
    return db_work

@app.delete("/api/works/{work_id}")
async def delete_work(work_id: int, db: Session = Depends(get_db)):
    """删除作品"""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")
    
    # 删除关联的标签
    db.query(WorkTag).filter(WorkTag.work_id == work_id).delete()
    
    # 删除文件
    if work.file_path and os.path.exists(work.file_path):
        os.remove(work.file_path)
    if work.thumbnail_path and os.path.exists(work.thumbnail_path):
        os.remove(work.thumbnail_path)
    
    db.delete(work)
    db.commit()
    
    return {"message": "作品删除成功"}

# 分类管理API
@app.get("/api/categories", response_model=List[CategorySchema])
async def get_categories(db: Session = Depends(get_db)):
    """获取所有分类"""
    return db.query(Category).order_by(Category.sort_order).all()

@app.post("/api/categories", response_model=CategorySchema)
async def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """创建分类"""
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# 标签管理API  
@app.get("/api/tags", response_model=List[TagSchema])
async def get_tags(db: Session = Depends(get_db)):
    """获取所有标签"""
    return db.query(Tag).order_by(Tag.usage_count.desc()).all()

@app.post("/api/tags", response_model=TagSchema)  
async def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    """创建标签"""
    db_tag = Tag(**tag.dict())
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

# 文件上传API
@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    work_type: WorkType = Form(WorkType.OTHER)
):
    """文件上传"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    # 生成唯一文件名
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = f"static/uploads/{unique_filename}"
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 获取文件信息
    file_size = os.path.getsize(file_path)
    mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    
    response_data = {
        "filename": file.filename,
        "file_path": file_path,
        "file_size": file_size,
        "mime_type": mime_type
    }
    
    # 如果是图片，生成缩略图和获取尺寸
    if mime_type.startswith("image/"):
        try:
            with Image.open(file_path) as img:
                response_data["width"] = img.width
                response_data["height"] = img.height
                
                # 生成缩略图
                thumbnail_size = (300, 300)
                img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                thumbnail_path = f"static/uploads/thumb_{unique_filename}"
                img.save(thumbnail_path, optimize=True, quality=85)
                response_data["thumbnail_path"] = thumbnail_path
        except Exception as e:
            print(f"处理图片失败: {e}")
    
    return FileUploadResponse(**response_data)

# 统计API
@app.get("/api/stats", response_model=StatsResponse)
async def get_stats_api(db: Session = Depends(get_db)):
    """获取统计信息"""
    return get_stats(db)

def get_stats(db: Session) -> StatsResponse:
    """获取统计数据"""
    total_works = db.query(Work).count()
    published_works = db.query(Work).filter(Work.status == WorkStatus.PUBLISHED).count()
    draft_works = db.query(Work).filter(Work.status == WorkStatus.DRAFT).count()
    total_views = db.query(Work).with_entities(db.func.sum(Work.view_count)).scalar() or 0
    total_likes = db.query(Work).with_entities(db.func.sum(Work.like_count)).scalar() or 0
    categories_count = db.query(Category).count()
    tags_count = db.query(Tag).count()
    
    return StatsResponse(
        total_works=total_works,
        published_works=published_works,
        draft_works=draft_works,
        total_views=total_views,
        total_likes=total_likes,
        categories_count=categories_count,
        tags_count=tags_count
    )

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "作品集系统运行正常"}

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"🎨 Starting Portfolio Showcase")
    print(f"📡 Server: {host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        access_log=True,
        log_level="info" if not debug else "debug"
    )