#!/bin/bash

# 一键启动前后端服务脚本

# 检查是否在主目录执行脚本
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "错误：请在项目根目录执行此脚本"
    echo "确保 frontend 和 backend 目录存在"
    exit 1
fi

# 启动后端服务
echo "正在启动后端服务..."
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# 启动前端服务
echo "正在启动前端服务..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# 显示服务状态
echo ""
echo "服务启动信息："
echo "------------------------------------------------"
echo "后端API服务已在 http://localhost:8000 启动 (PID: $BACKEND_PID)"
echo "前端界面已在 http://localhost:3000 启动 (PID: $FRONTEND_PID)"
echo "------------------------------------------------"
echo ""
echo "提示："
echo "- 前端服务需要一些时间初始化，请稍等片刻再访问"
echo "- 按 Ctrl+C 可以停止所有服务"
echo ""

# 等待用户中断信号
trap "echo '正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# 保持脚本运行
wait