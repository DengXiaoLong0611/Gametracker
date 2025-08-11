#!/bin/bash

# 游戏追踪器启动脚本

echo "🎮 启动游戏追踪器..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3环境"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
pip install -r requirements.txt

# 设置环境变量
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}
export DEBUG=${DEBUG:-false}

echo "🚀 在端口 $PORT 上启动应用..."
echo "🌐 访问地址: http://localhost:$PORT"
echo "📋 API文档: http://localhost:$PORT/docs"
echo "❤️  健康检查: http://localhost:$PORT/health"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动应用
python3 app.py