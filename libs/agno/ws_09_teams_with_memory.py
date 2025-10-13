from agno.team import Team
from agno.db.sqlite import SqliteDb
from agno.agent import Agent
from agno.vllm import q72b, q3o

db = SqliteDb(db_file="agno.db")

agent = Agent(name="Agent 1", role="You answer questions in Chinese", model=q72b, telemetry=False)
agent2 = Agent(name="Agent 2", role="You answer questions in Chinese, man like", model=q72b, telemetry=False)


team_with_memory = Team(
    name="Team with Memory",
    members=[agent, agent2],
    db=db,
    enable_user_memories=True,
    model=q72b,
telemetry=False
)

# team_with_memory.print_response("Hi! My name is John Doe.")
team_with_memory.print_response("What is my name?")
