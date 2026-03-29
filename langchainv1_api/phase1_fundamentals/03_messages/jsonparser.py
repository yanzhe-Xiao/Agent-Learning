# json 解析器

# 加载环境变量
import os

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


load_dotenv(override=True)
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL", "gpt-5.4-mini")
BASE_URL = os.getenv("BASE_URL", "https://api.groq.com/openai/v1")


# 初始化模型
model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY, # type: ignore
    base_url=BASE_URL
)

parser = JsonOutputParser()

prompt = ChatPromptTemplate.from_messages(
    messages=  [
        ("system", "你是返回的结果都要为 JSON 格式。要有confidence字段，表示对答案的自信程度，范围是0-1。"),
        ("human", "请回答{question}，并且只返回 JSON 格式的结果。")
    ]
)
chain = prompt | model | parser
res = chain.invoke({"question": "介绍一下 Python 编程语言。"})
print("解析后的结果：")
print(res)
print("\nconfidence 字段的值：")
print(res['confidence'])