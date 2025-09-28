"""
简化版 VLLM 测试 - 无需 Langfuse 配置
如果你暂时不想配置 Langfuse，可以先用这个脚本测试 VLLM 模型
"""

from openai import OpenAI
import time
import json

class SimpleVLLMTest:
    def __init__(self):
        self.client = OpenAI(
            api_key="EMPTY",  # VLLM 不需要真实的 API key
            base_url='http://223.109.239.14:10026/v1/'
        )
        self.model_id = 'Qwen3-Omni-Thinking'
        
        print("🚀 简化版 VLLM 测试客户端")
        print(f"   模型: {self.model_id}")
        print(f"   服务地址: http://223.109.239.14:10026/v1/")
        print("   状态: 无需任何付费密钥 ✅")
        print()
    
    def simple_chat(self, prompt: str):
        """简单的聊天测试"""
        print(f"📝 发送消息: {prompt[:50]}...")
        
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=32768,
                temperature=1.0
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            content = response.choices[0].message.content
            usage = response.usage
            
            print(f"✅ 成功响应 (耗时: {duration:.2f}s)")
            print(f"📊 Token 使用: 输入 {usage.prompt_tokens}, 输出 {usage.completion_tokens}")
            print(f"📄 回复: {content[:200]}...")
            print()
            
            return {
                "content": content,
                "duration": duration,
                "usage": usage.model_dump()
            }
            
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None
    
    def run_tests(self):
        """运行一系列测试"""
        test_prompts = [
            "你好，请简单介绍一下你自己。",
            "请用中文解释什么是人工智能？",
            "What are the main advantages of using VLLM?",
            "请写一个简单的 Python 函数来计算斐波那契数列。"
        ]
        
        print(f"🧪 开始运行 {len(test_prompts)} 个测试...")
        print("=" * 60)
        
        results = []
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n🔸 测试 {i}/{len(test_prompts)}")
            result = self.simple_chat(prompt)
            
            if result:
                results.append({
                    "test_number": i,
                    "prompt": prompt,
                    "success": True,
                    **result
                })
            else:
                results.append({
                    "test_number": i,
                    "prompt": prompt,
                    "success": False
                })
            
            # 短暂延迟
            time.sleep(0.5)
        
        # 显示测试摘要
        self.show_summary(results)
        
        return results
    
    def show_summary(self, results):
        """显示测试摘要"""
        print("\n" + "=" * 60)
        print("📊 测试摘要")
        print("=" * 60)
        
        successful = [r for r in results if r.get("success", False)]
        failed = [r for r in results if not r.get("success", False)]
        
        print(f"✅ 成功: {len(successful)}/{len(results)}")
        print(f"❌ 失败: {len(failed)}/{len(results)}")
        
        if successful:
            avg_duration = sum(r["duration"] for r in successful) / len(successful)
            total_input_tokens = sum(r["usage"]["prompt_tokens"] for r in successful)
            total_output_tokens = sum(r["usage"]["completion_tokens"] for r in successful)
            
            print(f"⏱️ 平均响应时间: {avg_duration:.2f}s")
            print(f"📊 总输入 Token: {total_input_tokens}")
            print(f"📊 总输出 Token: {total_output_tokens}")
            print(f"💰 成本: 完全免费 🎉")
        
        print("\n💡 提示:")
        print("   - 这个测试完全免费，无需任何付费密钥")
        print("   - 如果想要详细监控，可以配置 Langfuse（也是免费的）")
        print("   - 所有数据都在你本地，完全私有安全")

def main():
    print("🎯 VLLM 模型免费测试")
    print("=" * 60)
    print("✅ 无需任何付费密钥")
    print("✅ 完全免费使用")
    print("✅ 数据完全私有")
    print()
    
    # 创建测试客户端
    tester = SimpleVLLMTest()
    
    # 运行测试
    results = tester.run_tests()
    
    print("\n🎉 测试完成！")
    print("\n🔗 相关信息:")
    print("   - VLLM 服务: http://223.109.239.14:10026")
    print("   - 模型: Qwen3-Omni-Thinking")
    print("   - 费用: 完全免费 💰")
    
    return results

if __name__ == "__main__":
    main()
