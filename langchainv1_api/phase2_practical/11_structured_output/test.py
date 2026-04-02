"""
学习Pydantic结构化输出模型
"""

import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, tools
from pydantic import BaseModel, Field


load_dotenv(override=True)
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
class WeatherInfo(BaseModel):
    city: str
    temperature: float = Field(..., description="Temperature in Celsius")
    condition: str = Field(..., description="Weather condition, e.g., sunny, rainy")

# @tool
# def get_weather(city: str) -> str:
#     """
#     获取指定城市的天气信息

#     参数:
#         city: 城市名称，如"北京"、"上海"

#     返回:
#         天气信息字符串
#     """
#     # 使用switch-case
#     if city == "北京":
#         return WeatherInfo(city=city, temperature=25.0, condition="sunny").model_dump_json()  # 返回JSON字符串
#     elif city == "上海":
#         return WeatherInfo(city=city, temperature=28.0, condition="cloudy").model_dump_json()
#     elif city == "广州":
#         return WeatherInfo(city=city, temperature=30.0, condition="rainy").model_dump_json()
#     else:
#         return WeatherInfo(city=city, temperature=20.0, condition="sunny").model_dump_json()  # 默认返回晴天，实际应用中可以调用天气API获取真实数据

# # 不要把 with_structured_output 直接套在传给 Agent 的 model 上。
# # 而是使用 create_agent 的 response_format 参数，让 Agent 内部自动处理结构化输出（支持 ProviderStrategy / ToolStrategy）。
# agent = create_agent(
#     model=model,
#     tools=[get_weather],
#     system_prompt="你是一个天气预报助手，提供结构化的天气信息。输出严格按照 WeatherInfo 格式。",
#     response_format=WeatherInfo
# )
# res = agent.invoke({"messages": [{"role": "user", "content": "请告诉我北京的天气。"}]})
# print(res["messages"][-1].content)  # 输出结构化的天气信息

# # 结构化输出结果
# print("\n=== 结构化输出结果（Pydantic 对象）===")
# structured:WeatherInfo = res["structured_response"]   # 自动解析后的 WeatherInfo 对象
# print(structured)
# print(f"城市: {structured.city}")
# print(f"温度: {structured.temperature}°C")
# print(f"天气: {structured.condition}")


# with_structured_output 
model1 = model.with_structured_output(WeatherInfo)  # 直接套在 model 上，Agent 内部不处理结构化输出了
res:WeatherInfo = model1.invoke([SystemMessage(content="请严格按照 WeatherInfo 格式输出"),HumanMessage(content="信阳今天的天气比较晴朗，感觉有将近20度")]) # type: ignore
print("\n=== 结构化输出结果（Pydantic 对象）===")
print(type(res))
print(res.city)
print(res.temperature)
print(res.condition)
from langchain_core.output_parsers import PydanticOutputParser  # 结构化输出解析器

# PydanticParserOutput
parser = PydanticOutputParser(pydantic_object=WeatherInfo)
prompt = ChatPromptTemplate.from_template(
    "你是一个文本助手，提取用户信息:{input}，必须遵守格式{format_instructions}")
prompt = prompt.partial(format_instructions = parser.get_format_instructions())
chain = prompt | model | parser
response:WeatherInfo = chain.invoke({"input": "今天西安天气多云，最高温度30度，最低温度20度，适合外出散步！"})
print("\n=== 结构化输出结果（Pydantic 对象）===")
print(response)
print(type(response))
print(response.city)
print(response.temperature)
print(response.condition)
print(response.model_dump()) # dict