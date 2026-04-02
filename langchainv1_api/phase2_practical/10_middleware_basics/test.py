## 自己写一个中间件
import os
from typing import Callable

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse, before_model
from langchain.agents.middleware.types import wrap_model_call
from langchain_core.messages import SystemMessage

@wrap_model_call
def my_middleware(request:ModelRequest,handler:Callable[[ModelRequest],ModelResponse])->ModelResponse:
    """
    功能完整中间件：
    1. 拦截模型调用
    2. 自动重试 + 指数退避
    3. 精细错误处理 + 日志
    4. 重写响应（追加提示 + 更新状态）
    """
    max_retries = 3
    base_delay = 1.0  # 初始退避时间（秒）
    for attempt in range(max_retries):
        try:
            print(f"第 {attempt+1} 次尝试调用模型...")
            response: ModelResponse = handler(request)  # 调用下一个中间件或模型
            # 在这里可以修改 response，例如追加提示信息
            response.result.append(SystemMessage(content="（这是中间件追加的提示）"))
            return response
        except Exception as e:
            print(f"调用模型失败: {e}")
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # 指数退避
                print(f"等待 {delay:.2f} 秒后重试...")
                import time; time.sleep(delay)
            else:
                print("已达到最大重试次数，放弃调用模型。")
                raise e  # 最后一次失败后抛出异常
    return None  # type: ignore # 这个 return 实际上永远不会被执行到，因为要么成功返回 response，要么抛出异常
    
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
import dotenv
dotenv.load_dotenv(override=True)
prefix = ""
model_name = os.getenv(f"{prefix}MODEL", "gpt-3.5-turbo")
base_url = os.getenv(f"{prefix}BASE_URL", "http://localhost:8000")
api_key = os.getenv(f"{prefix}API_KEY")

mysql_url = os.getenv("MYSQL_URL")
redis_url = os.getenv("REDIS_URL")

model = ChatOpenAI(
    model=model_name,
    base_url=base_url,
    api_key=api_key
)
agent = create_agent(
    model=model,
    middleware=[my_middleware],  # 添加自定义中间件
    system_prompt="你是我的人工智能助手，帮助我完成各种任务。",
)

res = agent.invoke({"messages": [{"role": "user", "content": "什么是langchain？"}]})
print(f"Agent: {res['messages'][-2].content}")
print(f"Agent: {res['messages'][-1].content}")
