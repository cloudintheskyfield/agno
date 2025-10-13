from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb
from agno.vllm import q72b
from agno.agent import Agent

db = SqliteDb(db_file="tmp/data.db")


agent = Agent(name="Agent 1", role="You answer questions in Chinese", model=q72b, enable_user_memories=True, enable_agentic_memory=True, db=db)

team = Team(
    # model=OpenAIChat(id="gpt-5-mini"),
    model=q72b,
    members=[
        Agent(name="Agent 1", role="You answer questions in English", model=q72b),
        Agent(name="Agent 2", role="You answer questions in Chinese", model=q72b),
        Agent(name="Agent 3", role="You answer questions in French", model=q72b),
    ],
    db=db,
    respond_directly=True,
)

user_1_id = "user_101"
user_2_id = "user_102"

user_1_session_id = "session_101"
user_2_session_id = "session_102"

# # Start the session with user 1 (This means "how are you?" in French)
# team.print_response(
#     "comment ça va?",
#     user_id=user_1_id,
#     session_id=user_1_session_id,
# )
# # Continue the session with user 1 (This means "tell me a joke" in French)
# team.print_response("Raconte-moi une blague.", user_id=user_1_id, session_id=user_1_session_id)
#
# # Start the session with user 2
# team.print_response("Tell me about quantum physics.", user_id=user_2_id, session_id=user_2_session_id)


# team.print_response('你之前讲过什么笑话', user_id=user_1_id, session_id=user_1_session_id)

# Continue the session with user 2
agent.print_response("What is the speed of light?", user_id=user_2_id, session_id=user_2_session_id)
#
# # Ask the agent to give a summary of the conversation, this will use the history from the previous messages (but only for user 1)
agent.print_response(
    "你叫小明",
    user_id=user_1_id,
    session_id=user_1_session_id,
)
agent.print_response(
    "用户说你的名字叫什么来着",
    user_id=user_1_id,
    session_id=user_1_session_id,
)
agent.print_response(
    "Give me a summary of our conversation.",
    user_id=user_1_id,
    session_id=user_1_session_id,
)
