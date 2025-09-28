@echo off
echo 🚀 启动 Langfuse Self-Hosted 服务...
echo.

echo 📋 检查 Docker 是否运行...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未安装或未运行，请先安装并启动 Docker
    pause
    exit /b 1
)

echo ✅ Docker 已就绪
echo.

echo 🐳 启动 Langfuse 服务...
docker-compose up -d

if %errorlevel% equ 0 (
    echo.
    echo ✅ Langfuse 服务启动成功！
    echo.
    echo 📊 访问地址:
    echo    Langfuse Web UI: http://localhost:3000
    echo    PostgreSQL: localhost:5432
    echo.
    echo 🔑 默认登录信息:
    echo    首次访问时需要创建管理员账户
    echo.
    echo 💡 提示:
    echo    - 等待约30秒让服务完全启动
    echo    - 使用 Ctrl+C 停止服务
    echo    - 或运行 docker-compose down 停止服务
    echo.
) else (
    echo ❌ 启动失败，请检查错误信息
)

pause
