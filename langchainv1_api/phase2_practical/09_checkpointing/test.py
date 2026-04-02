"""
自己写Redis/MySQL的checkpointing代码，测试一下是否能正确保存和恢复对话状态。
"""

import os

import dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
dotenv.load_dotenv(override=True)
from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver
from langgraph.checkpoint.redis import RedisSaver

model_name = os.getenv("MODEL", "gpt-3.5-turbo")
base_url = os.getenv("BASE_URL", "http://localhost:8000")
api_key = os.getenv("API_KEY")

mysql_url = os.getenv("MYSQL_URL")
redis_url = os.getenv("REDIS_URL")

model = ChatOpenAI(
    model=model_name,
    base_url=base_url,
    api_key=api_key
)

with PyMySQLSaver.from_conn_string(mysql_url or "") as mysql_saver:
    mysql_saver.setup()
    agent = create_agent(
        model=model,
        checkpointer=mysql_saver,
        system_prompt="你是我的人工智能助手，帮助我完成各种任务。",
    )
    config = {"configurable": {"thread_id": "test_thread_mysql"}}
    res = agent.invoke({"messages": [{"role": "user", "content": "什么是langchain？"}]}, config=config )
    print(f"Agent: {res['messages'][-1].content}")

    res = agent.invoke({"messages": [{"role": "user", "content": "你能否告诉我上次我们聊了什么吗？"}]}, config=config )
    print(f"Agent: {res['messages'][-1].content}")

    mysql_saver.delete_thread("test_thread_mysql")

with RedisSaver.from_conn_string(redis_url or "") as redis_saver:
    redis_saver.setup()
    agent = create_agent(
        model=model,
        checkpointer=redis_saver,
        system_prompt="你是我的人工智能助手，帮助我完成各种任务。",
    )
    config = {"configurable": {"thread_id": "test_thread_redis"}}
    res = agent.invoke({"messages": [{"role": "user", "content": "什么是langchain？"}]}, config=config )
    print(f"Agent: {res['messages'][-1].content}")

    res = agent.invoke({"messages": [{"role": "user", "content": "你能否告诉我上次我们聊了什么吗？"}]}, config=config )
    print(f"Agent: {res['messages'][-1].content}")

    redis_saver.delete_thread("test_thread_redis")