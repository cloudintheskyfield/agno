"""
简单的 VLLM + Langfuse 集成测试脚本
"""

from vllm_with_langfuse import VLLMWithLangfuse
import time

def main():
    print("🚀 开始 VLLM + Langfuse 集成测试")
    
    # 创建客户端
    client = VLLMWithLangfuse()
    
    # 测试用例
    test_cases = [
        {
            "prompt": "请用中文简单介绍一下人工智能的发展历史",
            "session_id": "test_001",
            "metadata": {"category": "AI_history", "language": "chinese"}
        },
        {
            "prompt": "What are the main advantages of using VLLM for model serving?",
            "session_id": "test_002", 
            "metadata": {"category": "technical", "language": "english"}
        },
        {
            "prompt": "请解释一下什么是大语言模型？",
            "session_id": "test_003",
            "metadata": {"category": "LLM_explanation", "language": "chinese"}
        }
    ]
    
    print(f"\n📝 准备执行 {len(test_cases)} 个测试用例...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 测试用例 {i}/{len(test_cases)}")
        print(f"   提示: {test_case['prompt'][:50]}...")
        
        try:
            start_time = time.time()
            
            # 执行测试
            response = client.simple_chat(
                prompt=test_case["prompt"],
                session_id=test_case["session_id"],
                user_id="test_user",
                metadata=test_case["metadata"]
            )
            
            end_time = time.time()
            
            print(f"   ✅ 成功 (耗时: {end_time - start_time:.2f}s)")
            print(f"   📝 回复长度: {len(response)} 字符")
            print(f"   🔗 会话ID: {test_case['session_id']}")
            print()
            
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            print()
        
        # 短暂延迟
        time.sleep(1)
    
    # 刷新 Langfuse 缓冲区
    client.flush_langfuse()
    
    print("🎉 所有测试完成！")
    print("📊 请访问 http://localhost:3000 查看 Langfuse 仪表板")

if __name__ == "__main__":
    main()
