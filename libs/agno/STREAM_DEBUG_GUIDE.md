# 🔄 流式输出调试功能使用指南

## 📋 功能概述

我已经为你的 VLLM 模型添加了详细的流式输出调试功能，现在你可以：

- 📦 查看每个 chunk 的详细信息（编号、长度、内容）
- 📊 获取流式响应的统计信息（总 chunk 数、总长度、耗时等）
- 🔍 分析响应的生成模式和性能
- 🎯 调试流式输出的问题

## ✅ 已修改的文件

### 1. 核心模型文件
- `agno/models/base.py` - 添加了流式调试功能
- `agno/models/aws/bedrock.py` - 为 AWS Bedrock 添加调试

### 2. 调试工具
- `stream_debug_utils.py` - 完整的流式调试工具类
- `test_stream_debug.py` - 测试脚本
- `run.py` - 已启用调试的示例

## 🚀 使用方法

### 方法1：在代码中启用调试

```python
from agno.agent import Agent
from agno.models.vllm import VLLM
from stream_debug_utils import enable_stream_debug

# 启用详细调试模式
enable_stream_debug(verbose=True)

# 创建你的模型和 Agent
model = VLLM(
    id='Qwen3-Omni-Thinking',
    base_url='http://223.109.239.14:10026/v1/',
    max_tokens=32768
)

agent = Agent(
    model=model,
    tool_choice="none",
    markdown=True,
)

# 使用流式输出 - 现在会显示调试信息
agent.print_response("你好，请介绍一下你自己", stream=True)
```

### 方法2：运行现有的测试脚本

```bash
# 运行已配置好的测试
python run.py

# 或运行专门的测试脚本
python test_stream_debug.py
```

## 📊 调试输出示例

启用调试后，你会看到类似这样的输出：

```
🚀 开始流式响应 [VLLM] - 14:30:25
============================================================
📦 Chunk #001 | 长度:  15 | 累计:   15
   内容: 你好！我是一个
📦 Chunk #002 | 长度:  12 | 累计:   27  
   内容: AI助手，很高兴
📦 Chunk #003 | 长度:  18 | 累计:   45
   内容: 为你提供帮助。我可以
   🔄 包含换行符
📦 Chunk #004 | 长度:  20 | 累计:   65
   内容: 回答问题、协助分析、
   📝 包含句子结束符
============================================================
✅ 流式响应完成 - 14:30:28
📊 统计信息:
   • 总 chunk 数: 4
   • 总内容长度: 65 字符
   • 耗时: 2.34 秒
   • 平均 chunk 大小: 16.3 字符
   • 平均 chunk 间隔: 585.0 毫秒
```

## 🎛️ 调试模式

### 详细模式 (verbose=True)
```python
enable_stream_debug(verbose=True)
```
- 显示完整的 chunk 内容
- 显示响应对象的类型和属性
- 显示特殊内容标记（换行符、句子结束符等）

### 简洁模式 (verbose=False)
```python
enable_stream_debug(verbose=False)
```
- 只显示基本信息和内容预览
- 适合生产环境或长响应的调试

### 禁用调试
```python
from stream_debug_utils import disable_stream_debug
disable_stream_debug()
```

## 🔧 高级功能

### 手动控制调试过程

```python
from stream_debug_utils import StreamDebugger

# 创建自定义调试器
debugger = StreamDebugger(enabled=True, verbose=True)

# 手动开始调试
debugger.start_stream("My Custom Model")

# 在你的流式循环中
for chunk in your_stream:
    debugger.log_chunk(chunk)

# 结束调试
debugger.end_stream()
```

### 分析特定的响应模式

调试输出会自动标记：
- 🔄 包含换行符的 chunk
- 📝 包含句子结束符的 chunk  
- 📦 无内容的元数据 chunk

## 🎯 实际应用场景

### 1. 性能分析
- 查看 chunk 大小分布
- 分析响应延迟模式
- 优化流式输出体验

### 2. 问题诊断
- 检查是否有丢失的 chunk
- 验证内容完整性
- 调试流式中断问题

### 3. 模型比较
- 比较不同模型的流式输出模式
- 分析响应质量和速度

## 📝 注意事项

1. **性能影响**：调试模式会增加一些输出开销，生产环境建议使用简洁模式或禁用
2. **内容长度**：对于很长的响应，建议使用简洁模式避免控制台输出过多
3. **编码问题**：确保控制台支持 UTF-8 编码以正确显示中文内容

## 🛠️ 故障排除

### 如果调试信息没有显示

1. **检查导入**：
   ```python
   try:
       from stream_debug_utils import enable_stream_debug
       enable_stream_debug(verbose=True)
       print("✅ 调试已启用")
   except ImportError as e:
       print(f"❌ 导入失败: {e}")
   ```

2. **检查流式输出**：
   确保你使用的是 `stream=True`：
   ```python
   agent.print_response("test", stream=True)  # ✅ 正确
   agent.print_response("test", stream=False) # ❌ 不会触发调试
   ```

3. **检查模型支持**：
   确保你的模型支持流式输出

### 如果输出格式异常

- 检查控制台编码设置
- 尝试简洁模式：`enable_stream_debug(verbose=False)`
- 检查 Python 版本兼容性

## 🎉 开始使用

现在你可以运行 `python run.py` 来测试流式输出调试功能！

你将看到每个 chunk 的详细信息，帮助你更好地理解和优化你的 VLLM 模型的流式响应。
