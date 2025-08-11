@echo off
chcp 65001 >nul
echo 🎮 启动游戏追踪器...

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python环境
    pause
    exit /b 1
)

REM 检查依赖
echo 📦 检查依赖...
pip install -r requirements.txt

REM 设置环境变量
if not defined HOST set HOST=0.0.0.0
if not defined PORT set PORT=8000
if not defined DEBUG set DEBUG=false

echo 🚀 在端口 %PORT% 上启动应用...
echo 🌐 访问地址: http://localhost:%PORT%
echo 📋 API文档: http://localhost:%PORT%/docs
echo ❤️  健康检查: http://localhost:%PORT%/health
echo.
echo 按 Ctrl+C 停止服务器
echo.

REM 启动应用
python app.py
pause