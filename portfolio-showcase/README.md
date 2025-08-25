# 🎨 Portfolio Showcase - 个人作品集展示系统

一个现代化的个人作品集展示和管理平台，支持多种媒体类型，提供优雅的展示界面和强大的管理功能。

## ✨ 功能特点

### 📸 多媒体支持
- **图片作品**: 支持JPG、PNG、GIF、WebP等格式
- **文字创作**: 支持文章、诗歌、小说等文字作品
- **视频作品**: 支持MP4、MOV、AVI等视频格式  
- **音频作品**: 支持MP3、WAV、OGG等音频格式
- **文档类型**: 支持PDF、Word、Markdown等文档

### 🎯 核心功能
- **作品管理**: 创建、编辑、删除、分类管理作品
- **智能分类**: 支持自定义分类和标签系统
- **状态管理**: 草稿、已发布、已归档、精选等状态
- **搜索功能**: 全文搜索，按分类、标签筛选
- **统计分析**: 浏览量、点赞数、下载次数等统计

### 🌟 展示特性
- **响应式设计**: 完美适配桌面、平板、手机
- **精美UI**: 现代化的界面设计和交互效果
- **图片优化**: 自动生成缩略图，支持懒加载
- **SEO友好**: 完整的元数据和结构化数据
- **社交分享**: 支持各大社交平台分享

### 🔧 技术特性
- **数据库存储**: 支持PostgreSQL、MySQL、SQLite
- **文件处理**: 智能压缩、水印、格式转换
- **缓存系统**: Redis缓存提升性能
- **API接口**: 完整的RESTful API
- **容器化**: Docker部署支持

## 🚀 快速开始

### 环境要求
- Python 3.11+
- PostgreSQL 13+ (推荐) 或 SQLite
- Redis (可选，用于缓存)
- Docker & Docker Compose (可选)

### 本地开发

1. **克隆项目**
```bash
git clone <repository-url>
cd portfolio-showcase
```

2. **创建虚拟环境**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等参数
```

5. **初始化数据库**
```bash
# 如果使用SQLite (默认)
mkdir -p database

# 如果使用PostgreSQL
# 请先创建数据库和用户
```

6. **启动应用**
```bash
python -m app.main
```

7. **访问应用**
- 前端页面: http://localhost:8000
- API文档: http://localhost:8000/admin/docs
- 管理后台: http://localhost:8000/admin

### Docker部署

1. **使用Docker Compose (推荐)**
```bash
# 构建和启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

2. **单独Docker部署**
```bash
# 构建镜像
docker build -t portfolio-showcase .

# 运行容器
docker run -d \
  --name portfolio-app \
  -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./database/portfolio.db \
  -v $(pwd)/static/uploads:/app/static/uploads \
  portfolio-showcase
```

## 🔧 配置说明

### 数据库配置

**PostgreSQL (推荐生产环境)**
```env
DATABASE_URL=postgresql://username:password@localhost:5432/portfolio_db
```

**SQLite (开发环境)**
```env
DATABASE_URL=sqlite:///./database/portfolio.db
```

### 文件上传配置
```env
MAX_FILE_SIZE=50MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,webp,mp4,mov,mp3,pdf
THUMBNAIL_SIZE=300,300
IMAGE_QUALITY=85
```

### 第三方服务配置
```env
# Cloudinary (图片CDN)
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name

# 邮件服务
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 📁 项目结构

```
portfolio-showcase/
├── app/                    # 应用核心代码
│   ├── __init__.py
│   ├── main.py            # FastAPI应用主文件
│   ├── models.py          # 数据库模型
│   ├── schemas.py         # Pydantic模式
│   ├── database.py        # 数据库连接
│   └── utils.py           # 工具函数
├── static/                 # 静态文件
│   ├── css/               # 样式文件
│   ├── js/                # JavaScript文件
│   ├── images/            # 图片资源
│   └── uploads/           # 用户上传文件
├── templates/             # HTML模板
│   ├── base.html          # 基础模板
│   ├── index.html         # 首页模板
│   └── admin/             # 管理后台模板
├── database/              # 数据库文件
├── logs/                  # 日志文件
├── nginx/                 # Nginx配置
├── docker-compose.yml     # Docker Compose配置
├── Dockerfile             # Docker镜像配置
├── requirements.txt       # Python依赖
├── .env.example           # 环境变量示例
└── README.md             # 项目文档
```

## 🎨 界面预览

### 首页展示
- 精选作品轮播
- 最新作品网格展示
- 分类导航
- 统计信息

### 作品列表
- 瀑布流布局
- 分类筛选
- 标签过滤
- 搜索功能

### 作品详情
- 大图展示
- 作品信息
- 相关推荐
- 社交分享

### 管理后台
- 作品管理
- 分类管理
- 标签管理
- 统计分析

## 📊 API文档

### 作品管理
```
GET    /api/works          # 获取作品列表
POST   /api/works          # 创建作品
GET    /api/works/{id}     # 获取单个作品
PUT    /api/works/{id}     # 更新作品
DELETE /api/works/{id}     # 删除作品
```

### 分类管理
```
GET    /api/categories     # 获取分类列表
POST   /api/categories     # 创建分类
PUT    /api/categories/{id} # 更新分类
DELETE /api/categories/{id} # 删除分类
```

### 文件上传
```
POST   /api/upload         # 上传文件
```

### 统计信息
```
GET    /api/stats          # 获取统计数据
```

## 🔐 安全特性

- **文件类型验证**: 严格限制上传文件类型
- **文件大小限制**: 防止大文件上传攻击
- **SQL注入防护**: 使用ORM防止SQL注入
- **XSS防护**: 自动转义用户输入
- **CSRF防护**: 内置CSRF令牌验证
- **安全头部**: 设置安全相关HTTP头部

## 🚀 部署指南

### 生产环境部署

1. **服务器要求**
   - 2核4GB内存以上
   - 50GB存储空间
   - Ubuntu 20.04+ 或 CentOS 7+

2. **域名和SSL**
   - 配置域名解析
   - 申请SSL证书
   - 配置Nginx反向代理

3. **数据库优化**
   - 配置PostgreSQL连接池
   - 设置适当的索引
   - 定期备份数据

4. **监控和日志**
   - 配置日志轮转
   - 设置监控报警
   - 性能优化

### 云服务部署

**腾讯云**
- 云服务器CVM
- 云数据库PostgreSQL
- 对象存储COS
- 内容分发CDN

**阿里云**
- ECS云服务器
- RDS数据库
- OSS对象存储  
- CDN加速

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📝 更新日志

### v1.0.0 (2025-01-20)
- 🎉 首次发布
- ✨ 支持多媒体作品展示
- 🎨 现代化UI设计
- 🔧 完整的管理后台
- 📱 响应式设计
- 🚀 Docker部署支持

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 常见问题

**Q: 支持哪些图片格式？**
A: 支持JPG、PNG、GIF、WebP、SVG等主流格式。

**Q: 文件上传大小限制是多少？**
A: 默认50MB，可以通过环境变量配置。

**Q: 是否支持视频预览？**
A: 支持MP4、WebM等格式的视频预览播放。

**Q: 如何备份数据？**
A: 可以通过数据库备份和文件目录备份两种方式。

**Q: 是否支持多用户？**
A: 当前版本为单用户系统，多用户功能在规划中。

## 📞 支持

- 📧 邮箱: contact@example.com
- 🐛 问题反馈: [GitHub Issues](repository-url/issues)
- 📖 文档: [在线文档](documentation-url)
- 💬 讨论: [GitHub Discussions](repository-url/discussions)

---

Made with ❤️ by [Your Name]