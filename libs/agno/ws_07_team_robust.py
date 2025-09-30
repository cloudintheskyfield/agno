"""
更强健的 Team 测试版本
包含多种工具备选方案和错误处理
"""

from agno.team import Team
from agno.agent import Agent
from agno.vllm import q72b
import sys

def create_weather_agent_with_fallback():
    """创建带有备选工具的天气 Agent"""
    
    # 尝试不同的搜索工具
    tools_to_try = [
        ("DuckDuckGo", "agno.tools.duckduckgo", "DuckDuckGoTools"),
        ("Tavily", "agno.tools.tavily", "TavilyTools"),
        ("SerpAPI", "agno.tools.serpapi", "SerpApiTools"),
    ]
    
    for tool_name, module_name, class_name in tools_to_try:
        try:
            module = __import__(module_name, fromlist=[class_name])
            tool_class = getattr(module, class_name)
            tools = [tool_class()]
            
            agent = Agent(
                name="Weather Agent", 
                role="Get the weather information", 
                model=q72b, 
                tools=tools
            )
            
            print(f"✅ 成功使用 {tool_name} 搜索工具")
            return agent
            
        except ImportError as e:
            print(f"⚠️ {tool_name} 工具不可用: {e}")
            continue
        except Exception as e:
            print(f"⚠️ {tool_name} 工具初始化失败: {e}")
            continue
    
    # 如果所有工具都失败，创建无工具的 Agent
    print("⚠️ 所有搜索工具都不可用，创建无工具的 Agent")
    return Agent(
        name="Weather Agent", 
        role="Provide general weather information based on knowledge", 
        model=q72b
    )

def main():
    """主函数"""
    print("🚀 启动强健版 Team 测试...")
    print("=" * 50)
    
    # 创建新闻 Agent
    agent_1 = Agent(
        name="News Agent", 
        role="Get the latest news and current events", 
        model=q72b
    )
    
    # 创建带备选方案的天气 Agent
    agent_2 = create_weather_agent_with_fallback()
    
    # 创建 Team
    team = Team(
        name="News and Weather Team", 
        members=[agent_1, agent_2], 
        model=q72b
    )
    
    # 测试查询
    queries = [
        "今天东京天气怎么样?",
        "What's the weather like in Tokyo today?",
        "Tell me about current weather conditions in Tokyo"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n📝 测试查询 {i}: {query}")
        print("-" * 40)
        
        try:
            result = team.run(query)
            print("✅ 查询成功完成")
            
            # 如果结果太长，只显示前500个字符
            if hasattr(result, 'content') and len(str(result.content)) > 500:
                print(f"📄 结果预览: {str(result.content)[:500]}...")
            elif hasattr(result, 'content'):
                print(f"📄 结果: {result.content}")
            else:
                print(f"📄 结果: {str(result)[:500]}...")
                
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            print(f"错误类型: {type(e).__name__}")
            
            # 提供具体的解决建议
            if "Connection" in str(e):
                print("💡 建议: 检查网络连接")
            elif "SSL" in str(e):
                print("💡 建议: 可能是 SSL 证书问题，尝试使用其他网络")
            elif "timeout" in str(e).lower():
                print("💡 建议: 网络超时，稍后重试")
            else:
                print("💡 建议: 检查工具配置和 API 密钥")
            
            continue
    
    print("\n" + "=" * 50)
    print("🎉 测试完成")

if __name__ == "__main__":
    main()
