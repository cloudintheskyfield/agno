from agno.agent import Agent
from agno.vllm import q72b

def get_shopping_list(session_state: dict) -> str:
    """Get the shopping list."""
    return session_state["shopping_list"]

agent = Agent(model=q72b, tools=[get_shopping_list], session_state={"shopping_list": ["milk", "bread", "eggs"]}, markdown=True)
agent.print_response("What's on my shopping list?", stream=False)
