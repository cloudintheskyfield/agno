@echo off
echo 🚨 Docker Compose 问题修复工具
echo ================================

echo.
echo 🔍 步骤 1: 检查 Docker 状态
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未安装或未启动
    echo 💡 请启动 Docker Desktop 后重试
    pause
    exit /b 1
)
echo ✅ Docker 已安装

echo.
echo 🛑 步骤 2: 停止现有服务
echo 正在停止可能存在的容器...
docker-compose down 2>nul
timeout /t 3 >nul

echo.
echo 🧹 步骤 3: 清理 Docker 资源
echo 正在清理未使用的资源...
docker system prune -f
timeout /t 2 >nul

echo.
echo 🔌 步骤 4: 检查端口占用
echo 检查端口 3000...
netstat -an | findstr :3000 >nul
if %errorlevel% equ 0 (
    echo ⚠️ 端口 3000 被占用，可能需要手动释放
) else (
    echo ✅ 端口 3000 可用
)

echo 检查端口 5432...
netstat -an | findstr :5432 >nul
if %errorlevel% equ 0 (
    echo ⚠️ 端口 5432 被占用，可能需要手动释放
) else (
    echo ✅ 端口 5432 可用
)

echo.
echo 🚀 步骤 5: 尝试启动简化版本
echo 使用简化的 Docker Compose 配置...
docker-compose -f docker-compose-simple.yml up -d

if %errorlevel% equ 0 (
    echo.
    echo ✅ 启动成功！
    echo 📊 Langfuse 地址: http://localhost:3000
    echo 🗄️ PostgreSQL: localhost:5432
    echo.
    echo ⏳ 等待服务完全启动（约30秒）...
    timeout /t 30 >nul
    echo.
    echo 🎉 服务应该已经就绪！
    echo 请访问 http://localhost:3000 查看 Langfuse
) else (
    echo.
    echo ❌ 启动仍然失败
    echo.
    echo 💡 可能的解决方案:
    echo    1. 重启 Docker Desktop
    echo    2. 以管理员身份运行此脚本
    echo    3. 检查防火墙设置
    echo    4. 增加 Docker 内存分配
    echo    5. 使用无 Docker 版本: python simple_vllm_test.py
    echo.
    echo 📋 查看详细日志:
    echo    docker-compose -f docker-compose-simple.yml logs
)

echo.
pause
