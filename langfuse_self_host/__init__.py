import os
import openlit
from langfuse import Langfuse

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
    collect_gpu_stats=True
)

