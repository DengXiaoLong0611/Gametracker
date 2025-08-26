# 🚀 游戏追踪器部署指南

## 概述

本文档记录了游戏追踪器从JSON存储升级到PostgreSQL数据库的完整部署流程。

## 📋 方案A：Render平台升级部署（推荐）

### 前提条件
- ✅ 现有Render Web Service正在运行
- ✅ GitHub仓库已连接到Render
- ✅ 代码已推送到GitHub

### 详细步骤

#### 1. 添加PostgreSQL数据库
```
操作路径：Render Dashboard → 你的现有服务旁边 → New → PostgreSQL

配置选项：
- Name: game-tracker-db（或你喜欢的名称）
- Database: game_tracker
- User: 自动生成
- Plan: Free（免费套餐，足够个人使用）
- Region: 选择与Web Service相同的区域
```

#### 2. 连接数据库到现有服务
```
操作路径：你的Web Service → Environment → Add Environment Variable

添加环境变量：
键: DATABASE_URL
值: postgresql://username:password@hostname:port/database
（Render会在PostgreSQL创建完成后自动提供此连接字符串）

注意：连接字符串会自动显示在PostgreSQL服务的Info页面
```

#### 3. 推送代码触发重新部署
```bash
# 确保所有更改已提交
git status

# 如果有未提交的更改
git add .
git commit -m "🗄️ 添加PostgreSQL数据库支持和数据迁移功能"

# 推送到GitHub（触发Render自动重新部署）
git push origin main
```

#### 4. 监控部署过程
```
在Render Dashboard中监控：
- Web Service → Logs 查看启动日志
- 寻找数据库初始化和迁移相关日志
- 确认没有错误信息
```

#### 5. 验证部署成功
```bash
# 检查应用健康状态
curl https://gametracker-m37i.onrender.com/health

# 预期响应：
{
  "status": "healthy",
  "message": "游戏追踪器运行正常",
  "active_games": 0,
  "database_mode": true
}

# 检查API功能
curl https://gametracker-m37i.onrender.com/api/games
```

## 🔧 技术细节

### 存储模式切换逻辑
1. 应用启动时检测 `DATABASE_URL` 环境变量
2. 如果存在 → 使用PostgreSQL模式
3. 如果不存在 → 使用JSON文件模式（向后兼容）

### 数据迁移机制
- **自动触发**：应用启动时自动检测并创建数据库表
- **迁移逻辑**：如果检测到现有JSON数据，自动迁移到数据库
- **备份保护**：原JSON文件不会被删除，可作为备份

## 🚨 故障排除

### 常见问题1：数据库连接失败
**症状**：应用启动失败，日志显示数据库连接错误

**解决方案**：
1. 检查 `DATABASE_URL` 环境变量格式
2. 确认PostgreSQL实例状态正常
3. 检查防火墙和网络设置

### 常见问题2：数据迁移失败
**症状**：应用启动成功，但游戏数据丢失

**解决方案**：
```bash
# 手动运行迁移脚本
python migrate_json_to_db.py

# 或使用自动化部署脚本
python deploy.py
```

### 常见问题3：性能问题
**症状**：响应时间变慢

**解决方案**：
1. 检查数据库连接池配置
2. 监控数据库查询性能
3. 考虑添加数据库索引

## 📝 回滚方案

如果需要回滚到JSON模式：
1. 移除 `DATABASE_URL` 环境变量
2. 重新部署应用
3. 应用会自动切换回JSON存储模式

## 📊 部署后验证清单

- [ ] 健康检查API返回 `database_mode: true`
- [ ] 游戏CRUD操作功能正常
- [ ] 并发游戏限制逻辑工作正常  
- [ ] 数据持久化（重启后数据不丢失）
- [ ] 响应时间在可接受范围内

## 📞 支持信息

如果遇到问题，可以检查：
1. Render部署日志
2. PostgreSQL连接状态
3. 应用健康检查端点
4. GitHub Actions（如果配置了CI/CD）

---

*最后更新：2025年*