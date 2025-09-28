"""
你的 VLLM 模型配置示例
使用你提供的具体模型参数
"""

from vllm_with_langfuse import VLLMWithLangfuse
import time
import uuid

def main():
    print("🚀 启动你的 VLLM 模型监控")
    print("=" * 50)
    
    # 使用你的具体配置
    model_config = {
        'model_id': 'Qwen3-Omni-Thinking',
        'base_url': 'http://223.109.239.14:10026/v1/',
        'max_tokens': 32768,
        'temperature': 1
    }
    
    print(f"📋 模型配置:")
    for key, value in model_config.items():
        print(f"   {key}: {value}")
    print()
    
    # 创建客户端
    try:
        client = VLLMWithLangfuse(**model_config)
        print("✅ VLLM 客户端创建成功")
    except Exception as e:
        print(f"❌ 客户端创建失败: {e}")
        return
    
    # 生成唯一的会话ID
    session_id = f"session_{int(time.time())}"
    user_id = "developer_user"
    
    print(f"\n🔗 会话信息:")
    print(f"   会话ID: {session_id}")
    print(f"   用户ID: {user_id}")
    print()
    
    # 测试用例 - 针对你的模型优化
    test_prompts = [
        {
            "prompt": "你好，我是开发者，正在测试模型监控功能。请简单介绍一下你的能力。",
            "metadata": {"type": "capability_test", "language": "chinese"}
        },
        {
            "prompt": "请用中文解释一下什么是 VLLM，以及它的主要优势。",
            "metadata": {"type": "technical_explanation", "topic": "vllm"}
        },
        {
            "prompt": "如果我想监控大语言模型的使用情况，你有什么建议？",
            "metadata": {"type": "consultation", "topic": "monitoring"}
        }
    ]
    
    print(f"🧪 开始执行 {len(test_prompts)} 个测试...")
    print()
    
    results = []
    
    for i, test in enumerate(test_prompts, 1):
        print(f"📝 测试 {i}/{len(test_prompts)}: {test['prompt'][:30]}...")
        
        try:
            start_time = time.time()
            
            # 执行模型调用
            response = client.simple_chat(
                prompt=test["prompt"],
                session_id=session_id,
                user_id=user_id,
                metadata={
                    **test["metadata"],
                    "test_number": i,
                    "timestamp": time.time()
                }
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            result = {
                "test_number": i,
                "success": True,
                "duration": duration,
                "response_length": len(response),
                "prompt": test["prompt"]
            }
            
            results.append(result)
            
            print(f"   ✅ 成功 (耗时: {duration:.2f}s, 回复: {len(response)} 字符)")
            print(f"   📄 回复预览: {response[:100]}...")
            print()
            
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            results.append({
                "test_number": i,
                "success": False,
                "error": str(e),
                "prompt": test["prompt"]
            })
            print()
        
        # 短暂延迟
        time.sleep(0.5)
    
    # 刷新 Langfuse 数据
    print("📊 正在同步数据到 Langfuse...")
    client.flush_langfuse()
    
    # 显示测试结果摘要
    print("\n" + "=" * 50)
    print("📊 测试结果摘要")
    print("=" * 50)
    
    successful_tests = [r for r in results if r.get("success", False)]
    failed_tests = [r for r in results if not r.get("success", False)]
    
    print(f"✅ 成功: {len(successful_tests)}/{len(results)}")
    print(f"❌ 失败: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        avg_duration = sum(r["duration"] for r in successful_tests) / len(successful_tests)
        total_chars = sum(r["response_length"] for r in successful_tests)
        print(f"⏱️ 平均响应时间: {avg_duration:.2f}s")
        print(f"📝 总回复字符数: {total_chars}")
    
    print(f"\n🔗 监控信息:")
    print(f"   会话ID: {session_id}")
    print(f"   Langfuse 仪表板: http://localhost:3000")
    print(f"   模型: {model_config['model_id']}")
    print(f"   服务地址: {model_config['base_url']}")
    
    print("\n🎉 测试完成！请访问 Langfuse 仪表板查看详细数据。")

if __name__ == "__main__":
    main()
