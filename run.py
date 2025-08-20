#!/usr/bin/env python3
"""
游戏追踪器 - 简化启动脚本
用于本地开发和测试
"""

import uvicorn

if __name__ == "__main__":
    print("🚀 启动游戏追踪器...")
    print("📱 应用将在 http://localhost:8000 启动")
    print("📚 API文档: http://localhost:8000/docs")
    print("🔍 健康检查: http://localhost:8000/health")
    print("按 Ctrl+C 停止应用")
    
    uvicorn.run(
        "app:app",
        host="127.0.0.1",  # 本地访问
        port=8000,          # 标准端口
        reload=True,        # 开发模式自动重载
        log_level="info"
    ) 