# Langfuse Self-Hosted + VLLM 集成

这个项目提供了一个完整的 self-hosted Langfuse 设置，用于监控和记录你的 VLLM 模型调用。

## 🚀 快速开始

### 1. 启动 Langfuse 服务

#### Windows 用户:
```bash
# 双击运行
start_langfuse.bat

# 或在命令行中运行
docker-compose up -d
```

#### Linux/Mac 用户:
```bash
docker-compose up -d
```

### 2. 访问 Langfuse Web UI

打开浏览器访问: http://localhost:3000

首次访问时需要创建管理员账户。

### 3. 配置环境变量

1. 复制环境配置文件:
```bash
cp env.example .env
```

2. 在 Langfuse Web UI 中创建项目并获取 API 密钥

3. 编辑 `.env` 文件，填入你的 API 密钥:
```env
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=http://localhost:3000
```

### 4. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 5. 运行测试

```bash
# 运行集成测试
python test_integration.py

# 或直接运行主脚本
python vllm_with_langfuse.py
```

## 📊 功能特性

### ✅ 已实现功能

- **完整的模型调用记录**: 记录输入、输出、延迟、使用情况
- **错误跟踪**: 自动记录和分类错误
- **会话管理**: 支持会话ID和用户ID跟踪
- **元数据支持**: 可以添加自定义元数据
- **流式响应支持**: 支持流式和非流式响应
- **自动指标计算**: 自动计算 token 使用量和延迟

### 📈 监控指标

- **延迟监控**: 每次调用的响应时间
- **Token 使用量**: 输入和输出 token 统计
- **错误率**: 成功/失败调用比率
- **使用模式**: 按用户、会话、时间的使用分析

## 🔧 配置说明

### VLLM 模型配置

```python
from vllm_with_langfuse import VLLMWithLangfuse

client = VLLMWithLangfuse(
    model_id='Qwen3-Omni-Thinking',           # 你的模型ID
    base_url='http://223.109.239.14:10026/v1/', # VLLM 服务地址
    max_tokens=32768,                         # 最大输出长度
    temperature=1.0                           # 温度参数
)
```

### 基本使用

```python
# 简单对话
response = client.simple_chat(
    "你好，请介绍一下你自己",
    session_id="user_session_001",
    user_id="user_123",
    metadata={"source": "web_app", "version": "1.0"}
)

# 多轮对话
messages = [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
    {"role": "user", "content": "请介绍一下AI的发展历史"}
]

response = client.chat_completion(
    messages=messages,
    session_id="session_001",
    user_id="user_123"
)
```

## 🗂️ 项目结构

```
langfuse_self_host/
├── docker-compose.yml      # Docker Compose 配置
├── env.example            # 环境变量示例
├── requirements.txt       # Python 依赖
├── vllm_with_langfuse.py # 主要集成代码
├── test_integration.py   # 测试脚本
├── start_langfuse.bat    # Windows 启动脚本
├── README.md             # 说明文档
└── data/                 # 数据目录 (自动创建)
    ├── postgres/         # PostgreSQL 数据
    └── langfuse/         # Langfuse 数据
```

## 🔍 故障排除

### 常见问题

1. **Docker 启动失败**
   - 确保 Docker 已安装并正在运行
   - 检查端口 3000 和 5432 是否被占用

2. **无法连接到 VLLM 服务**
   - 检查 VLLM 服务是否正在运行
   - 确认 base_url 地址是否正确

3. **Langfuse 连接失败**
   - 检查 API 密钥是否正确
   - 确认 Langfuse 服务是否已启动

4. **数据不显示在 Langfuse 中**
   - 调用 `client.flush_langfuse()` 刷新缓冲区
   - 检查网络连接和 API 密钥

### 日志查看

```bash
# 查看服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f langfuse-server
docker-compose logs -f db
```

### 停止服务

```bash
# 停止服务但保留数据
docker-compose down

# 停止服务并删除数据
docker-compose down -v
```

## 📝 许可证

本项目基于 MIT 许可证开源。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

如有问题，请创建 Issue 或联系维护者。
