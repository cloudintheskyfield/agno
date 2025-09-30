import os
import openlit
from langfuse import Langfuse

# 完全禁用 OpenTelemetry metrics 和日志输出
os.environ["OTEL_METRICS_EXPORTER"] = "none"
os.environ["OTEL_LOGS_EXPORTER"] = "none"
os.environ["OTEL_LOG_LEVEL"] = "FATAL"
os.environ["OTEL_PYTHON_LOG_CORRELATION"] = "false"
os.environ["OTEL_PYTHON_LOG_FORMAT"] = ""
os.environ["OTEL_SDK_DISABLED"] = "false"  # 保持 SDK 启用但禁用输出

lf = Langfuse(
  secret_key="sk-lf-08bf994d-8999-44f6-bdbd-f4edcb0da18d",
  public_key="pk-lf-818f2263-e276-4d43-a608-778d8cebf5ff",
  host="http://223.109.239.14:3000"
)

# os.envin['LANGFUSE_HOST'] = 'http://223.109.239.14:3000/'
# os.environ['LANGFUSE_PUBLIC_KEY'] = ''

# if lf.auth_check():
#     print("Langfuse client is authenticated and ready!")
# else:
#     print("Authentication failed. Please check your credentials and host.")

openlit.init(
    tracer=lf._otel_tracer,
    disable_batch=True,
    collect_gpu_stats=False,  # 禁用 GPU 统计以减少输出
    disable_metrics=True,
    # 完全禁用控制台输出
    environment="production"
)

