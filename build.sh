#!/bin/bash

# 生产环境部署脚本

# 检查是否在主目录执行脚本
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "错误：请在项目根目录执行此脚本"
    echo "确保 frontend 和 backend 目录存在"
    exit 1
fi

# 设置默认API地址，可通过环境变量覆盖，需要换成自己的服务器地址
API_BASE_URL=${API_BASE_URL:-"http://10.129.243.43:8001"}

# 构建前端
echo "正在构建前端应用，向后端请求的API地址是: $API_BASE_URL"
cd frontend
VITE_API_BASE_URL=$API_BASE_URL npm run build
cd ..

# 替换原有的后端服务检查和启动逻辑（第21-33行）
# 停止正在运行的后端服务（如果存在）
if pgrep -f "gunicorn.*main:app" > /dev/null; then
    echo "检测到后端服务正在运行，正在停止..."
    pkill -f "gunicorn.*main:app"
    sleep 3  # 等待进程完全结束
fi

# 启动后端服务（生产环境）
echo "正在启动后端服务..."
cd backend
# 使用nohup确保进程在终端关闭后继续运行
nohup gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001 > backend.log 2>&1 &
BACKEND_PID=$!
echo "后端PID: $BACKEND_PID"
cd ..

# 检查前端是否已经在运行
if pgrep -f "serve.*dist" > /dev/null; then
    echo "前端服务已在运行，正在重启以应用更新..."
    # 杀掉现有的前端服务
    pkill -f "serve.*dist"
    sleep 2  # 等待进程完全结束
fi

# 启动前端静态文件服务
echo "正在启动前端服务..."
cd frontend
# 使用nohup确保进程在终端关闭后继续运行
nohup npx serve -s dist -p 3001 > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端PID: $FRONTEND_PID"
cd ..

# 显示服务状态
echo ""
echo "服务启动信息："
echo "------------------------------------------------"
echo "后端API服务已在 http://0.0.0.0:8001 启动 (PID: $BACKEND_PID)"
echo "前端界面已在 3001 端口启动并在8080端口转发 (PID: $FRONTEND_PID)"
echo "API地址设置为: $API_BASE_URL"
echo "日志文件：backend.log, frontend.log"
echo "------------------------------------------------"

# 提示用户如何停止服务
echo ""
echo "要停止服务，请使用以下命令："
echo "kill $BACKEND_PID $FRONTEND_PID"
echo "或使用 pkill -f 'gunicorn|serve'"