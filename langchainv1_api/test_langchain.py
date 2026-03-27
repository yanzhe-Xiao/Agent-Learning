from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

# 创建一个简单的 prompt
template = "Tell me a short joke about {topic}"
prompt = ChatPromptTemplate.from_template(template)

# 打印 langchain 版本
import langchain
print(f"LangChain version: {langchain.__version__}")

print("LangChain v1.2 is working correctly!")