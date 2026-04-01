# 学习InMemorySaver

import dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI


dotenv.load_dotenv(override=True)
import os
MODEL = os.getenv("MODEL")
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL") 

model = ChatOpenAI(
    model=MODEL, # type: ignore
    api_key=API_KEY, # type: ignore
    base_url=BASE_URL
) 
from langgraph.checkpoint.memory import InMemorySaver

memory = InMemorySaver()

agent = create_agent(
    model=model,
    tools=[],
    system_prompt="你是一个有用的助手，帮助用户记住一些信息。",
    checkpointer=memory
)

message = HumanMessage(content="你好，我叫小明。")
config = {"configurable":{"thread_id": "1"}}
res = agent.invoke({"messages": [message]},config=config) # type: ignore
print(res['messages'][-1].content)
# 再次调用agent，看看之前的信息是否被记住了
message = HumanMessage(content="你还记得我叫什么名字吗？")
res = agent.invoke({"messages": [message]},config=config) # type: ignore
print(res['messages'][-1].content)

print(memory.get_tuple(config=config)) # pyright: ignore[reportArgumentType]