"""
Docker Compose 故障诊断脚本
帮助排查 docker-compose up -d 卡住的问题
"""

import subprocess
import time
import sys
import os

def run_command(cmd, timeout=30):
    """运行命令并返回结果"""
    try:
        print(f"🔍 执行: {cmd}")
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "命令超时"
    except Exception as e:
        return -1, "", str(e)

def check_docker_status():
    """检查 Docker 状态"""
    print("\n🐳 检查 Docker 状态...")
    print("=" * 50)
    
    # 检查 Docker 版本
    code, stdout, stderr = run_command("docker --version")
    if code == 0:
        print(f"✅ Docker 已安装: {stdout.strip()}")
    else:
        print(f"❌ Docker 未安装或无法访问: {stderr}")
        return False
    
    # 检查 Docker 是否运行
    code, stdout, stderr = run_command("docker info")
    if code == 0:
        print("✅ Docker 服务正在运行")
    else:
        print(f"❌ Docker 服务未运行: {stderr}")
        print("💡 请启动 Docker Desktop")
        return False
    
    # 检查 Docker Compose
    code, stdout, stderr = run_command("docker-compose --version")
    if code == 0:
        print(f"✅ Docker Compose 可用: {stdout.strip()}")
    else:
        print(f"❌ Docker Compose 不可用: {stderr}")
        return False
    
    return True

def check_ports():
    """检查端口占用"""
    print("\n🔌 检查端口占用...")
    print("=" * 50)
    
    ports = [3000, 5432]
    
    for port in ports:
        code, stdout, stderr = run_command(f"netstat -an | findstr :{port}")
        if code == 0 and stdout.strip():
            print(f"⚠️ 端口 {port} 已被占用:")
            print(f"   {stdout.strip()}")
        else:
            print(f"✅ 端口 {port} 可用")

def check_docker_compose_file():
    """检查 docker-compose.yml 文件"""
    print("\n📄 检查配置文件...")
    print("=" * 50)
    
    if os.path.exists("docker-compose.yml"):
        print("✅ docker-compose.yml 文件存在")
        
        # 验证配置文件语法
        code, stdout, stderr = run_command("docker-compose config")
        if code == 0:
            print("✅ docker-compose.yml 语法正确")
        else:
            print(f"❌ docker-compose.yml 语法错误: {stderr}")
            return False
    else:
        print("❌ docker-compose.yml 文件不存在")
        return False
    
    return True

def check_docker_resources():
    """检查 Docker 资源"""
    print("\n💾 检查 Docker 资源...")
    print("=" * 50)
    
    # 检查磁盘空间
    code, stdout, stderr = run_command("docker system df")
    if code == 0:
        print("📊 Docker 磁盘使用情况:")
        print(stdout)
    
    # 检查运行中的容器
    code, stdout, stderr = run_command("docker ps")
    if code == 0:
        print("🏃 运行中的容器:")
        if stdout.strip():
            print(stdout)
        else:
            print("   无运行中的容器")

def try_cleanup():
    """尝试清理 Docker 资源"""
    print("\n🧹 尝试清理...")
    print("=" * 50)
    
    # 停止可能存在的容器
    print("停止现有容器...")
    run_command("docker-compose down", timeout=60)
    
    # 清理未使用的资源
    print("清理未使用的资源...")
    run_command("docker system prune -f", timeout=60)
    
    print("✅ 清理完成")

def test_simple_docker():
    """测试简单的 Docker 命令"""
    print("\n🧪 测试基本 Docker 功能...")
    print("=" * 50)
    
    # 测试拉取镜像
    print("测试拉取 hello-world 镜像...")
    code, stdout, stderr = run_command("docker run --rm hello-world", timeout=60)
    
    if code == 0:
        print("✅ Docker 基本功能正常")
        return True
    else:
        print(f"❌ Docker 基本功能异常: {stderr}")
        return False

def suggest_solutions():
    """提供解决方案建议"""
    print("\n💡 解决方案建议...")
    print("=" * 50)
    
    solutions = [
        "1. 重启 Docker Desktop",
        "2. 检查防火墙设置，确保 Docker 可以访问网络",
        "3. 释放端口 3000 和 5432（如果被占用）",
        "4. 增加 Docker Desktop 的内存分配（推荐 4GB+）",
        "5. 切换 Docker Desktop 的存储驱动",
        "6. 临时禁用杀毒软件",
        "7. 使用管理员权限运行命令提示符",
        "8. 检查网络连接，确保可以下载 Docker 镜像"
    ]
    
    for solution in solutions:
        print(f"   {solution}")
    
    print("\n🔧 快速修复命令:")
    print("   docker-compose down")
    print("   docker system prune -f")
    print("   docker-compose up -d --force-recreate")

def main():
    print("🚨 Docker Compose 故障诊断工具")
    print("=" * 60)
    print("正在诊断 docker-compose up -d 卡住的问题...")
    
    # 检查各个组件
    docker_ok = check_docker_status()
    
    if not docker_ok:
        print("\n❌ Docker 基础环境有问题，请先解决 Docker 安装和启动问题")
        suggest_solutions()
        return
    
    check_ports()
    compose_ok = check_docker_compose_file()
    
    if not compose_ok:
        print("\n❌ Docker Compose 配置有问题")
        return
    
    check_docker_resources()
    
    # 尝试清理
    print("\n🤔 是否尝试清理并重新启动？(y/n): ", end="")
    try:
        choice = input().lower()
        if choice == 'y':
            try_cleanup()
            
            print("\n🚀 尝试重新启动...")
            code, stdout, stderr = run_command("docker-compose up -d", timeout=120)
            
            if code == 0:
                print("✅ 启动成功！")
                print("📊 访问 http://localhost:3000 查看 Langfuse")
            else:
                print(f"❌ 启动仍然失败: {stderr}")
                suggest_solutions()
        else:
            suggest_solutions()
    except KeyboardInterrupt:
        print("\n\n操作被取消")
    
    print("\n🔍 如果问题仍然存在，请:")
    print("   1. 查看详细日志: docker-compose logs")
    print("   2. 检查 Docker Desktop 设置")
    print("   3. 考虑使用简化版本: python simple_vllm_test.py")

if __name__ == "__main__":
    main()
