"""
快速启动脚本 - 无需配置即可开始测试
"""

import os
import sys
import subprocess
import time

def check_docker():
    """检查 Docker 是否可用"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker 已安装: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker 未安装或未运行")
        print("请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop")
        return False

def start_langfuse():
    """启动 Langfuse 服务"""
    print("🚀 启动 Langfuse 服务...")
    
    try:
        # 启动 docker-compose
        result = subprocess.run(['docker-compose', 'up', '-d'], 
                              capture_output=True, text=True, check=True)
        print("✅ Langfuse 服务启动成功!")
        print("📊 Web UI: http://localhost:3000")
        print("🗄️ PostgreSQL: localhost:5432")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def wait_for_service():
    """等待服务启动"""
    print("⏳ 等待服务启动 (约30秒)...")
    
    import requests
    for i in range(30):
        try:
            response = requests.get("http://localhost:3000", timeout=2)
            if response.status_code == 200:
                print("✅ Langfuse 服务已就绪!")
                return True
        except:
            pass
        
        print(f"   等待中... ({i+1}/30)")
        time.sleep(1)
    
    print("⚠️ 服务可能需要更多时间启动，请手动检查 http://localhost:3000")
    return False

def create_env_file():
    """创建基本的 .env 文件"""
    env_content = """# Langfuse 配置 - 启动后在 Web UI 中获取真实的密钥
LANGFUSE_PUBLIC_KEY=pk-lf-placeholder
LANGFUSE_SECRET_KEY=sk-lf-placeholder
LANGFUSE_HOST=http://localhost:3000

# 数据库配置
DATABASE_URL=postgresql://langfuse:langfuse@localhost:5432/langfuse

# 安全配置
NEXTAUTH_SECRET=your-nextauth-secret-here
SALT=your-salt-here
NEXTAUTH_URL=http://localhost:3000

# 可选配置
TELEMETRY_ENABLED=true
LANGFUSE_ENABLE_EXPERIMENTAL_FEATURES=false
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ 创建了 .env 文件")
    else:
        print("ℹ️ .env 文件已存在")

def install_requirements():
    """安装 Python 依赖"""
    print("📦 安装 Python 依赖...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def main():
    print("🎯 Langfuse Self-Hosted 快速启动")
    print("=" * 50)
    
    # 检查 Docker
    if not check_docker():
        return False
    
    # 创建环境文件
    create_env_file()
    
    # 启动服务
    if not start_langfuse():
        return False
    
    # 安装依赖
    if not install_requirements():
        print("⚠️ 依赖安装失败，但服务已启动")
    
    # 等待服务
    wait_for_service()
    
    print("\n🎉 设置完成!")
    print("\n📋 下一步操作:")
    print("1. 访问 http://localhost:3000")
    print("2. 创建管理员账户")
    print("3. 创建新项目并获取 API 密钥")
    print("4. 更新 .env 文件中的 LANGFUSE_PUBLIC_KEY 和 LANGFUSE_SECRET_KEY")
    print("5. 运行测试: python test_integration.py")
    
    print("\n🔧 有用的命令:")
    print("- 查看日志: docker-compose logs -f")
    print("- 停止服务: docker-compose down")
    print("- 重启服务: docker-compose restart")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ 启动失败，请检查错误信息")
        sys.exit(1)
    else:
        print("\n✅ 启动成功!")
