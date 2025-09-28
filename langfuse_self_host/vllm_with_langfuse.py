"""
VLLM 模型调用与 Langfuse 集成示例
记录模型调用的详细信息，包括输入、输出、延迟等
"""

import os
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse import observe
from openai import OpenAI
import time
from typing import Optional, Dict, Any

# 加载环境变量
load_dotenv()

class VLLMWithLangfuse:
    def __init__(self,
                 model_id: str = 'Qwen3-Omni-Thinking',
                 base_url: str = 'http://223.109.239.14:10026/v1/',
                 max_tokens: int = 32768,
                 temperature: float = 1.0):
        """
        初始化 VLLM 客户端和 Langfuse
        """
        self.model_id = model_id
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.temperature = temperature

        # 初始化 OpenAI 客户端（用于 VLLM）
        self.client = OpenAI(
            api_key="EMPTY",  # VLLM 不需要真实的 API key
            base_url=base_url
        )

        # 初始化 Langfuse
        self.langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
        )

        print(f"✅ VLLM 客户端初始化完成")
        print(f"   模型: {self.model_id}")
        print(f"   基础URL: {self.base_url}")
        print(f"   Langfuse Host: {os.getenv('LANGFUSE_HOST', 'http://localhost:3000')}")

    @observe(name="vllm_chat_completion")
    def chat_completion(self,
                       messages: list,
                       stream: bool = False,
                       session_id: Optional[str] = None,
                       user_id: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行聊天完成请求并记录到 Langfuse
        """
        start_time = time.time()

        try:
            # 准备请求参数
            request_params = {
                "model": self.model_id,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": stream
            }

            # 调用 VLLM API
            response = self.client.chat.completions.create(**request_params)

            end_time = time.time()
            latency = end_time - start_time

            # 处理响应
            if stream:
                # 流式响应处理
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        yield content

                response_data = {
                    "content": full_response,
                    "model": self.model_id,
                    "usage": {"completion_tokens": len(full_response.split())},
                    "latency": latency
                }
            else:
                # 非流式响应处理
                response_data = {
                    "content": response.choices[0].message.content,
                    "model": response.model,
                    "usage": response.usage.model_dump() if response.usage else {},
                    "latency": latency
                }

            # 记录到 Langfuse
            self._log_to_langfuse(
                messages=messages,
                response=response_data,
                session_id=session_id,
                user_id=user_id,
                metadata=metadata or {}
            )

            return response_data

        except Exception as e:
            end_time = time.time()
            latency = end_time - start_time

            # 记录错误到 Langfuse
            self._log_error_to_langfuse(
                messages=messages,
                error=str(e),
                latency=latency,
                session_id=session_id,
                user_id=user_id,
                metadata=metadata or {}
            )

            raise e

    def _log_to_langfuse(self,
                        messages: list,
                        response: Dict[str, Any],
                        session_id: Optional[str] = None,
                        user_id: Optional[str] = None,
                        metadata: Dict[str, Any] = None):
        """记录成功的调用到 Langfuse"""
        try:
            # 创建生成记录
            generation = self.langfuse.generation(
                name="vllm_chat_completion",
                model=self.model_id,
                input=messages,
                output=response["content"],
                usage={
                    "input": sum(len(msg.get("content", "").split()) for msg in messages),
                    "output": response["usage"].get("completion_tokens", 0),
                    "total": response["usage"].get("total_tokens", 0)
                },
                metadata={
                    **metadata,
                    "base_url": self.base_url,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "latency": response["latency"]
                },
                session_id=session_id,
                user_id=user_id
            )

            print(f"✅ 成功记录到 Langfuse: {generation.id}")

        except Exception as e:
            print(f"❌ 记录到 Langfuse 失败: {e}")

    def _log_error_to_langfuse(self,
                              messages: list,
                              error: str,
                              latency: float,
                              session_id: Optional[str] = None,
                              user_id: Optional[str] = None,
                              metadata: Dict[str, Any] = None):
        """记录错误的调用到 Langfuse"""
        try:
            # 创建错误记录
            generation = self.langfuse.generation(
                name="vllm_chat_completion_error",
                model=self.model_id,
                input=messages,
                output=f"ERROR: {error}",
                metadata={
                    **metadata,
                    "base_url": self.base_url,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "latency": latency,
                    "error": error
                },
                session_id=session_id,
                user_id=user_id,
                level="ERROR"
            )

            print(f"❌ 错误记录到 Langfuse: {generation.id}")

        except Exception as e:
            print(f"❌ 记录错误到 Langfuse 失败: {e}")

    def simple_chat(self, prompt: str, **kwargs) -> str:
        """简单的聊天接口"""
        messages = [{"role": "user", "content": prompt}]
        response = self.chat_completion(messages, **kwargs)
        return response["content"]

    def flush_langfuse(self):
        """刷新 Langfuse 缓冲区，确保所有数据都被发送"""
        self.langfuse.flush()
        print("✅ Langfuse 数据已刷新")


# 使用示例
if __name__ == "__main__":
    # 创建 VLLM 客户端
    vllm_client = VLLMWithLangfuse(
        model_id='Qwen3-Omni-Thinking',
        base_url='http://223.109.239.14:10026/v1/',
        max_tokens=32768,
        temperature=1.0
    )

    # 测试对话
    print("\n🤖 开始测试对话...")

    try:
        # 简单对话测试
        response = vllm_client.simple_chat(
            "你好，请简单介绍一下你自己。",
            session_id="test_session_001",
            user_id="test_user",
            metadata={"test_type": "simple_chat", "version": "1.0"}
        )

        print(f"\n🤖 AI 回复: {response}")

        # 多轮对话测试
        messages = [
            {"role": "user", "content": "请告诉我今天的天气如何？"},
            {"role": "assistant", "content": "抱歉，我无法获取实时天气信息。"},
            {"role": "user", "content": "那你能做什么呢？"}
        ]

        response = vllm_client.chat_completion(
            messages=messages,
            session_id="test_session_002",
            user_id="test_user",
            metadata={"test_type": "multi_turn", "version": "1.0"}
        )

        print(f"\n🤖 多轮对话回复: {response['content']}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")

    finally:
        # 确保数据被发送到 Langfuse
        vllm_client.flush_langfuse()
        print("\n✅ 测试完成，数据已记录到 Langfuse")
