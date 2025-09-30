# 🛠️ Team 功能故障排除指南

## 📋 遇到的问题

你在运行 `ws_07_team.py` 时遇到了两个主要问题：

1. **Google 搜索连接错误**：`ConnectionResetError: [WinError 10054]`
2. **OpenTelemetry metrics 输出噪音**：大量 JSON 格式的遥测数据

## ✅ 解决方案

### 1. 禁用 Metrics 输出

我已经创建了多层防护来完全禁用 metrics 输出：

#### 方法1：使用 disable_metrics 模块
```python
# 在脚本开头添加
import disable_metrics
```

#### 方法2：更新 langfuse_self_host 配置
已经更新了 `langfuse_self_host/__init__.py`：
- 设置了更多的环境变量禁用输出
- 禁用了 GPU 统计收集
- 设置为生产环境模式

### 2. 解决网络连接问题

#### 替换搜索工具
- **原来**：`GoogleSearchTools()` - 容易被墙或连接重置
- **现在**：`DuckDuckGoTools()` - 更稳定的搜索服务

#### 创建强健版本
`ws_07_team_robust.py` 包含：
- 多种搜索工具备选方案
- 自动降级机制
- 详细的错误处理和建议

## 🚀 使用方法

### 快速修复版本
```bash
python ws_07_team.py
```

### 强健版本（推荐）
```bash
python ws_07_team_robust.py
```

## 🔍 预期效果

运行修复后的版本，你应该看到：

```
🔇 已禁用所有遥测和 metrics 输出
🚀 启动 Team 测试...
使用 DuckDuckGo 搜索工具替代 Google 搜索以避免连接问题
✅ 成功使用 DuckDuckGo 搜索工具
📝 执行查询: 今天东京天气怎么样?
✅ 查询完成
```

**不会再看到**：
- ❌ 大量的 JSON metrics 数据
- ❌ `Invalid type NoneType for attribute` 错误
- ❌ 连接重置错误

## 🛠️ 故障排除

### 如果仍然有 metrics 输出

1. **检查导入顺序**：
   ```python
   # 确保 disable_metrics 在最前面
   import disable_metrics
   # 然后再导入其他模块
   ```

2. **手动设置环境变量**：
   ```python
   import os
   os.environ["OTEL_METRICS_EXPORTER"] = "none"
   os.environ["OTEL_LOG_LEVEL"] = "FATAL"
   ```

### 如果搜索仍然失败

1. **检查网络连接**：
   ```bash
   ping www.duckduckgo.com
   ```

2. **尝试其他搜索工具**：
   ```python
   # 在 ws_07_team_robust.py 中会自动尝试多种工具
   ```

3. **使用无工具版本**：
   ```python
   agent_2 = Agent(
       name="Weather Agent", 
       role="Provide weather info based on knowledge", 
       model=q72b
       # 不使用任何工具
   )
   ```

## 📝 文件说明

- `ws_07_team.py` - 修复版的原始文件
- `ws_07_team_robust.py` - 强健版本，包含多种备选方案
- `disable_metrics.py` - 禁用遥测输出的工具模块
- `langfuse_self_host/__init__.py` - 更新的 Langfuse 配置

## 💡 最佳实践

1. **总是在脚本开头导入 disable_metrics**
2. **使用 DuckDuckGo 而不是 Google 搜索**
3. **添加错误处理和备选方案**
4. **在生产环境中禁用详细日志**

## 🎯 测试验证

运行以下命令验证修复：

```bash
# 测试基础版本
python ws_07_team.py

# 测试强健版本
python ws_07_team_robust.py
```

如果看到干净的输出（没有 JSON metrics），说明修复成功！
