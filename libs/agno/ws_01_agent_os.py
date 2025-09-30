from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.os import AgentOS
from agno.models.vllm import VLLM
from agno.tools.mcp import MCPTools
from agno.vllm import model



# Create the Agent
agno_agent = Agent(
    name="Agno Agent",
    model=model,
    # Add a database to the Agent
    db=SqliteDb(db_file="agno.db"),
    # Add the Agno MCP server to the Agent
    tools=[MCPTools(transport="streamable-http", url="https://docs.agno.com/mcp")],
    tool_choice="none",  # 禁用自动工具选择，因为VLLM服务器没有启用--enable-auto-tool-choice
    # Add the previous session history to the context
    add_history_to_context=True,
    markdown=True,
    stream=True
)


# Create the AgentOS
agent_os = AgentOS(agents=[agno_agent])
# Get the FastAPI app for the AgentOS
app = agent_os.get_app()


# 启动 AgentOS 应用
if __name__ == "__main__":
    """启动 AgentOS 应用

    你可以在以下地址查看配置和可用的应用:
    http://localhost:7777/config
    """
    print("正在启动 AgentOS 应用...")
    print("应用将在 http://localhost:7777 启动")
    print("配置页面: http://localhost:7777/config")
    agent_os.serve(app="ws_01_agent_os:app", reload=True, port=7777)
