"""
完全禁用 OpenTelemetry metrics 输出的工具
在任何脚本开头导入此模块即可禁用所有 metrics 输出
"""

import os
import sys
import logging

def disable_all_telemetry():
    """完全禁用所有遥测输出"""
    
    # 设置环境变量禁用 OpenTelemetry
    telemetry_vars = {
        "OTEL_METRICS_EXPORTER": "none",
        "OTEL_LOGS_EXPORTER": "none", 
        "OTEL_TRACES_EXPORTER": "none",
        "OTEL_LOG_LEVEL": "FATAL",
        "OTEL_PYTHON_LOG_CORRELATION": "false",
        "OTEL_PYTHON_LOG_FORMAT": "",
        "OTEL_RESOURCE_ATTRIBUTES": "",
        "OTEL_SERVICE_NAME": "",
        "OTEL_SDK_DISABLED": "false",
        # OpenLIT 相关
        "OPENLIT_DISABLE_METRICS": "true",
        "OPENLIT_DISABLE_LOGGING": "true",
    }
    
    for key, value in telemetry_vars.items():
        os.environ[key] = value
    
    # 禁用相关的日志记录器
    loggers_to_disable = [
        "opentelemetry",
        "openlit",
        "httpx",
        "urllib3",
        "requests",
        "httpcore"
    ]
    
    for logger_name in loggers_to_disable:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)
        logger.disabled = True
    
    # 重定向标准输出中的 JSON 输出
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    class FilteredOutput:
        def __init__(self, original):
            self.original = original
            self.buffer = ""
        
        def write(self, text):
            # 过滤掉包含 metrics 的 JSON 输出
            if text.strip():
                # 检查是否是 metrics JSON
                if (text.strip().startswith('{') and 
                    ('resource_metrics' in text or 
                     'scope_metrics' in text or
                     'telemetry.sdk' in text)):
                    return  # 不输出
                
                # 检查是否是 OpenTelemetry 错误
                if ('Invalid type NoneType for attribute' in text and 
                    'gen_ai.' in text):
                    return  # 不输出
            
            self.original.write(text)
        
        def flush(self):
            if hasattr(self.original, 'flush'):
                self.original.flush()
        
        def __getattr__(self, name):
            return getattr(self.original, name)
    
    # 应用过滤器
    sys.stdout = FilteredOutput(original_stdout)
    sys.stderr = FilteredOutput(original_stderr)
    
    print("🔇 已禁用所有遥测和 metrics 输出")

# 自动执行禁用
disable_all_telemetry()
