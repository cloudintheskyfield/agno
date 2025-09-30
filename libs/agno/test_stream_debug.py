"""
测试流式输出调试功能
"""

from agno.agent import Agent
from agno.models.vllm import VLLM
from agno.tools.hackernews import HackerNewsTools
from stream_debug_utils import enable_stream_debug, disable_stream_debug

def test_stream_debug():
    """测试流式输出调试功能"""
    
    print("🧪 测试流式输出调试功能")
    print("=" * 50)
    
    # 启用详细调试模式
    enable_stream_debug(verbose=True)
    
    # 创建模型和 Agent
    model = VLLM(
        id='Qwen3-Omni-Thinking',
        base_url='http://223.109.239.14:10026/v1/',
        max_tokens=32768,
        temperature=1
    )
    
    agent = Agent(
        model=model,
        tools=[HackerNewsTools()],
        tool_choice="none",
        markdown=True,
    )
    
    # 测试流式响应
    print("\n🚀 开始测试流式响应...")
    
    try:
        # 使用流式输出
        response = agent.print_response(
            "请简单介绍一下你自己，用中文回答。", 
            stream=True
        )
        
        print("\n✅ 流式响应测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 测试说明:")
    print("• 你应该看到每个 chunk 的详细信息")
    print("• 包括 chunk 编号、内容长度、累计长度")
    print("• 以及每个 chunk 的实际内容")
    print("• 最后会显示整体统计信息")

def test_simple_mode():
    """测试简洁模式"""
    
    print("\n🧪 测试简洁调试模式")
    print("=" * 50)
    
    # 启用简洁调试模式
    enable_stream_debug(verbose=False)
    
    model = VLLM(
        id='Qwen3-Omni-Thinking',
        base_url='http://223.109.239.14:10026/v1/',
        max_tokens=1000,  # 较短的响应
        temperature=1
    )
    
    agent = Agent(
        model=model,
        tool_choice="none",
        markdown=True,
    )
    
    try:
        # 简短的测试
        response = agent.print_response(
            "说一句话", 
            stream=True
        )
        
        print("\n✅ 简洁模式测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")

def test_disabled_mode():
    """测试禁用调试模式"""
    
    print("\n🧪 测试禁用调试模式")
    print("=" * 50)
    
    # 禁用调试
    disable_stream_debug()
    
    model = VLLM(
        id='Qwen3-Omni-Thinking',
        base_url='http://223.109.239.14:10026/v1/',
        max_tokens=500,
        temperature=1
    )
    
    agent = Agent(
        model=model,
        tool_choice="none",
        markdown=True,
    )
    
    try:
        # 测试无调试输出
        response = agent.print_response(
            "Hello", 
            stream=True
        )
        
        print("\n✅ 禁用模式测试完成（应该没有调试输出）")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")

if __name__ == "__main__":
    print("🎯 流式输出调试功能测试套件")
    print("=" * 60)
    
    # 运行所有测试
    test_stream_debug()
    test_simple_mode() 
    test_disabled_mode()
    
    print("\n🎉 所有测试完成！")
    print("\n💡 使用提示:")
    print("• 在你的代码中导入: from stream_debug_utils import enable_stream_debug")
    print("• 启用调试: enable_stream_debug(verbose=True)  # 详细模式")
    print("• 启用调试: enable_stream_debug(verbose=False) # 简洁模式")
    print("• 禁用调试: disable_stream_debug()")
    print("• 调试信息会自动显示在控制台中")
