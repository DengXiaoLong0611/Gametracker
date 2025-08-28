#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏追踪器 - 简化启动脚本
用于本地开发和测试
"""

import uvicorn
import sys
import os

# 设置控制台编码
if sys.platform == "win32":
    os.system("chcp 65001 >nul")

if __name__ == "__main__":
    print("Game Tracker Starting...")
    print("Application will start at http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(
        "app:app",
        host="127.0.0.1",  # 本地访问
        port=8000,          # 标准端口
        reload=True,        # 开发模式自动重载
        log_level="info"
    ) 