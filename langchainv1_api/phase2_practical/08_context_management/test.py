
import os

import dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI


dotenv.load_dotenv(override=True)
model_name = os.getenv("MODEL")
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_mini = os.getenv("MODEL_MINI")
model = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
)
model_mini = ChatOpenAI(
    model=model_mini, 
    api_key=api_key,
    base_url=base_url,
)
from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()
from langchain.agents.middleware.summarization import SummarizationMiddleware
agent = create_agent(
    model=model,
    tools=[],
    system_prompt="你是一个有用的助手，协助用户完成任务。你会根据用户的输入，分析并提供相关信息和建议。",
    checkpointer=memory,
    middleware=[
        SummarizationMiddleware(
            model=model_mini,
            trigger=("tokens",1000),
            keep=("tokens",300)
            # trigger=("fraction", 0.8),           # ← 关键改动：使用模型最大上下文的 80%
            # keep=("fraction", 0.3),              # ← 推荐同时改 keep：保留最近 30% 的上下文
        )
    ]
)


config = {
    "configurable":{
        "thread_id": "thread_12345",
    }
}

questions = [
    "请分析一下当前的市场趋势，并提供一些投资建议。",
    "你能帮我总结一下最近的科技新闻吗？",
    "我想了解一下人工智能在医疗领域的应用，你能给我一些相关的信息吗？",
    "你还记得我们说了什么吗？"
]

for question in questions:
    print("用户提问：", question)
    res = agent.invoke({"messages":[HumanMessage(content=question)]}, config=config)
    print("助手回答：", res['messages'][-1].content)
