# 🎮 游戏追踪器 (Game Tracker)

一个优雅的 FastAPI Web 应用程序，帮助您管理游戏进度，控制同时进行的游戏数量，避免"开始太多游戏"的焦虑。

## ✨ 功能特点

- 🎯 **六种游戏状态** - ACTIVE(活跃)、PAUSED(暂停)、CASUAL(休闲)、PLANNED(计划)、FINISHED(完成)、DROPPED(弃坑)
- 🔢 **智能并发限制** - 默认最多5个活跃游戏，可自定义调整
- 📝 **详细游戏信息** - 支持备注、开始时间、结束时间记录
- 💾 **双模式存储** - 支持 JSON 文件存储和 PostgreSQL 数据库存储
- 🌐 **现代 Web 界面** - 基于 FastAPI 的响应式设计
- 🔒 **线程安全** - 支持并发访问和操作
- 🏥 **健康检查** - 内置监控端点

## 🚀 快速开始

### 本地开发

1. **克隆项目**
```bash
git clone https://github.com/your-username/game_tracker.git
cd game_tracker
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动应用**
```bash
# JSON 模式启动（默认）
python app.py

# 或者使用调试模式
DEBUG=true python app.py
```

4. **访问应用**
- 应用地址: http://localhost:8001
- API 文档: http://localhost:8001/docs
- 健康检查: http://localhost:8001/health

### 数据库模式（生产环境）

如需使用 PostgreSQL 数据库：

```bash
# 设置数据库连接
export DATABASE_URL="postgresql://user:password@localhost:5432/game_tracker"

# 启动应用
python app.py
```

## ⚙️ 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DATABASE_URL` | - | PostgreSQL连接字符串（可选）|
| `USE_DATABASE` | `false` | 强制使用数据库模式 |
| `HOST` | `0.0.0.0` | 服务器绑定地址 |
| `PORT` | `8001` | 服务器端口 |
| `DEBUG` | `false` | 调试模式 |
| `DEPLOYMENT_ENV` | `local` | 部署环境 (local/tencent-container/tencent-scf) |

## 📋 API 接口

### 核心接口
- `GET /` - 主页面
- `GET /health` - 健康检查和存储模式状态
- `GET /docs` - 交互式 API 文档

### 游戏管理
- `GET /api/games` - 获取所有游戏（按状态分组）
- `POST /api/games` - 添加新游戏
- `PATCH /api/games/{id}` - 更新游戏状态/信息
- `DELETE /api/games/{id}` - 删除游戏

### 统计与设置
- `GET /api/active-count` - 获取当前活跃游戏数量和限制
- `POST /api/settings/limit` - 更新并发游戏限制

## 🏗️ 架构设计

### 存储模式

应用支持两种存储模式，启动时自动选择：

1. **JSON 模式**（默认）
   - 文件存储在 `games_data.json`
   - 适合单机部署和开发环境
   - 线程安全，支持并发访问

2. **数据库模式**
   - 使用 PostgreSQL 数据库
   - 适合生产环境和云部署
   - 支持高并发和数据持久化

### 项目结构
```
game_tracker/
├── 📁 核心应用
│   ├── app.py                  # FastAPI 主应用
│   ├── models.py               # Pydantic 数据模型
│   ├── db_models.py            # SQLAlchemy 数据库模型
│   ├── database.py             # 数据库连接管理
│   └── exceptions.py           # 自定义异常类
├── 📁 存储层
│   ├── store.py                # JSON 文件存储
│   ├── store_db.py             # PostgreSQL 存储
│   └── store_adapter.py        # 存储模式选择器
├── 📁 Web 界面
│   ├── templates/index.html    # 主要界面
│   └── static/                 # 静态资源
├── 📁 数据和配置
│   ├── games_data.json         # JSON 数据文件
│   ├── requirements.txt        # Python 依赖
│   └── .env.example            # 环境变量模板
└── 📁 文档
    ├── README.md               # 项目说明
    ├── CLAUDE.md               # 开发指南
    └── LICENSE                 # 开源许可
```

## 🛡️ 安全特性

- ✅ CORS 中间件配置
- ✅ 安全响应头（X-Content-Type-Options, X-Frame-Options, X-XSS-Protection）
- ✅ Pydantic 数据验证
- ✅ SQL 注入防护（SQLAlchemy ORM）
- ✅ 线程安全的文件操作
- ✅ 健康检查端点监控

## 📈 监控与维护

### 健康检查
```bash
# 检查应用状态和存储模式
curl http://localhost:8001/health

# 响应示例
{
  "status": "healthy",
  "database_mode": false,
  "active_games": 2,
  "total_games": 15
}
```

### 数据备份

**JSON 模式：**
```bash
# 备份数据文件
cp games_data.json games_data_backup_$(date +%Y%m%d).json
```

**数据库模式：**
```bash
# 使用 pg_dump 备份数据库
pg_dump $DATABASE_URL > backup.sql
```

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/新功能`)
3. 提交更改 (`git commit -m '添加某某功能'`)
4. 推送到分支 (`git push origin feature/新功能`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🛠️ 技术栈

- **后端框架**: FastAPI
- **数据验证**: Pydantic
- **数据库**: PostgreSQL + SQLAlchemy（可选）
- **存储**: JSON 文件 + 文件锁（默认）
- **前端**: HTML + Vanilla JavaScript
- **部署**: Python 3.8+

## 🆘 常见问题

**Q: 如何在 JSON 模式和数据库模式之间切换？**
A: 设置 `DATABASE_URL` 环境变量会自动切换到数据库模式，删除该变量则使用 JSON 模式。

**Q: 数据会自动迁移吗？**
A: 是的，首次启动数据库模式时会自动从 `games_data.json` 迁移数据。

**Q: 支持多用户吗？**
A: 当前版本为单用户设计，如需多用户支持请提交 Issue 讨论。

**Q: 可以修改游戏状态的定义吗？**
A: 游戏状态在 `models.py` 中定义，可以根据需要修改，但需要考虑数据兼容性。

---

🎮 **Made with ❤️ for organized gamers!**