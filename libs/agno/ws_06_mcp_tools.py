from agno.vllm import q72b
from agno.agent import Agent
from agno.tools.mcp import MCPTools

async def run_mcp_agent():

    # Initialize the MCP tools
    mcp_tools = MCPTools(command=f"uvx mcp-server-git")

    # Connect to the MCP server
    await mcp_tools.connect()

    agent = Agent(model=q72b, tools=[mcp_tools], markdown=True)
    await agent.aprint_response("What is the license for this project?", stream=False)


import asyncio
asyncio.run(run_mcp_agent())
