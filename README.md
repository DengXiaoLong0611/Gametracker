# 🎮 游戏追踪器

一个优雅的Web应用程序，帮助您管理游戏进度，控制同时进行的游戏数量，避免"开始太多游戏"的焦虑。

## ✨ 功能特点

- 🎯 **游戏状态管理** - 支持"正在游玩"、"已通关"、"已弃坑"三种状态
- 🔢 **并发限制** - 可配置的同时游戏上限（默认3个）
- 📝 **详细记录** - 支持备注、评分(0-10)、原因记录
- 💾 **数据持久化** - 自动保存到JSON文件，重启不丢失
- 🌐 **响应式设计** - 支持桌面和移动设备
- 🔒 **线程安全** - 支持并发访问

## 🚀 部署方式

### 方式1: Docker部署（推荐）

1. **克隆项目**
```bash
git clone <your-repo-url>
cd game-tracker
```

2. **使用Docker Compose**
```bash
docker-compose up -d
```

3. **访问应用**
- 应用地址: http://localhost:8000
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 方式2: 手动部署

1. **环境要求**
- Python 3.11+
- pip

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动应用**
```bash
python app.py
```

### 方式3: 云平台部署

#### Railway部署
1. 登录 [Railway](https://railway.app)
2. 点击 "New Project" → "Deploy from GitHub repo"
3. 选择您的仓库
4. Railway会自动检测并部署

#### Heroku部署
1. 安装Heroku CLI
2. 执行以下命令：
```bash
heroku create your-app-name
git push heroku main
```

#### Vercel部署
1. 登录 [Vercel](https://vercel.com)
2. 导入GitHub项目
3. 自动部署

## ⚙️ 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `HOST` | `0.0.0.0` | 服务器绑定地址 |
| `PORT` | `8000` | 服务器端口 |
| `DEBUG` | `false` | 调试模式 |

## 📋 API接口

### 核心接口
- `GET /` - 主页面
- `GET /health` - 健康检查
- `GET /docs` - API文档

### 游戏管理
- `GET /api/games` - 获取所有游戏
- `POST /api/games` - 添加新游戏
- `PATCH /api/games/{id}` - 更新游戏
- `DELETE /api/games/{id}` - 删除游戏

### 设置管理  
- `GET /api/active-count` - 获取活跃游戏数量
- `POST /api/settings/limit` - 更新并发限制

## 🔧 开发指南

### 本地开发
```bash
# 开发模式运行
DEBUG=true python app.py
```

### 项目结构
```
game-tracker/
├── app.py              # 主应用文件
├── models.py           # 数据模型
├── store.py            # 数据存储层
├── exceptions.py       # 异常处理
├── templates/          # HTML模板
│   └── index.html
├── games_data.json     # 数据文件（自动生成）
├── requirements.txt    # 依赖列表
├── Dockerfile         # Docker配置
├── docker-compose.yml # Docker Compose配置
└── README.md          # 说明文档
```

## 🛡️ 安全特性

- ✅ CORS中间件配置
- ✅ 安全响应头设置
- ✅ XSS保护
- ✅ 内容类型嗅探保护
- ✅ 点击劫持保护
- ✅ 健康检查端点

## 📈 监控和维护

### 健康检查
```bash
curl http://your-domain/health
```

### 数据备份
定期备份 `games_data.json` 文件以防数据丢失。

### 日志监控
应用使用标准日志输出，可通过Docker logs查看：
```bash
docker-compose logs -f game-tracker
```

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 故障排除

### 常见问题

1. **端口被占用**
   - 修改环境变量 `PORT` 或杀死占用进程

2. **数据丢失**
   - 检查 `games_data.json` 文件是否存在
   - 确保应用有写入权限

3. **Docker构建失败**  
   - 确保Docker版本 >= 20.10
   - 检查网络连接

### 获取帮助
- 📧 Email: your-email@example.com
- 🐛 Issues: [GitHub Issues](your-repo-url/issues)

---

Made with ❤️ for gamers who want to stay organized!