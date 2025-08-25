#!/usr/bin/env python3
"""
Portfolio Showcase - 启动脚本
用于本地开发和测试
"""

import os
import uvicorn
from pathlib import Path

def main():
    """启动应用"""
    # 确保必要的目录存在
    directories = [
        "static/uploads",
        "static/images", 
        "database",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("🎨 Portfolio Showcase - 个人作品集系统")
    print("=" * 50)
    print("📁 项目目录:", os.getcwd())
    print("📡 本地访问: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/admin/docs") 
    print("🔧 管理后台: http://localhost:8000/admin")
    print("=" * 50)
    print("按 Ctrl+C 停止服务")
    print()
    
    # 开发环境配置
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,           # 开发模式自动重载
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()