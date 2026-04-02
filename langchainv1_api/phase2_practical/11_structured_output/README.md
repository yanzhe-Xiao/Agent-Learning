# 11 - Structured Output (结构化输出)

## 核心概念

**Structured Output = 将 LLM 的自然语言输出转为结构化 Python 对象**

在 LangChain 1.0 中，使用 `with_structured_output()` 方法结合 Pydantic 模型，可以确保 LLM 返回符合预定义模式的数据。

## 基本用法

### 定义 Pydantic 模型

```python
from pydantic import BaseModel, Field

class Person(BaseModel):
    """人物信息"""
    name: str = Field(description="姓名")
    age: int = Field(description="年龄")
    occupation: str = Field(description="职业")
```

### 使用 with_structured_output()

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("groq:llama-3.3-70b-versatile")

# 创建结构化输出的 LLM
structured_llm = model.with_structured_output(Person)

# 调用
result = structured_llm.invoke("张三是一名 30 岁的软件工程师")

# result 是 Person 实例
print(result.name)       # "张三"
print(result.age)        # 30
print(result.occupation) # "软件工程师"
```

## 核心组件

### 1. Pydantic BaseModel

所有结构化输出的数据模型都必须继承 `BaseModel`：

```python
from pydantic import BaseModel

class MyModel(BaseModel):
    field1: str
    field2: int
```

### 2. Field 描述

使用 `Field()` 添加字段描述，帮助 LLM 理解：

```python
from pydantic import Field

class Book(BaseModel):
    title: str = Field(description="书名")
    author: str = Field(description="作者")
    year: int = Field(description="出版年份")
```

**重要**：`description` 会传递给 LLM，帮助它正确填充字段。

### 3. 类型注解

Pydantic 支持丰富的类型：

```python
from typing import Optional, List

class Product(BaseModel):
    name: str                    # 必填字符串
    price: float                 # 必填浮点数
    description: Optional[str]   # 可选字符串
    tags: List[str]              # 字符串列表
```

## 高级特性

### 可选字段

```python
class User(BaseModel):
    username: str
    email: Optional[str] = None  # 可以为 None
    age: Optional[int] = None
```

### 默认值

```python
class Config(BaseModel):
    timeout: int = 30         # 默认 30
    retry: bool = True        # 默认 True
    max_attempts: int = Field(3, description="最大重试次数")
```

### 枚举类型

```python
from enum import Enum

class Priority(str, Enum):
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"

class Task(BaseModel):
    title: str
    priority: Priority  # 只能是 LOW/MEDIUM/HIGH
```

### 列表提取

```python
class Person(BaseModel):
    name: str
    age: int

class PeopleList(BaseModel):
    people: List[Person]  # 多个 Person 对象

structured_llm = model.with_structured_output(PeopleList)
result = structured_llm.invoke("张三 30岁，李四 25岁")
# result.people = [Person(name="张三", age=30), Person(name="李四", age=25)]
```

### 嵌套模型

```python
class Address(BaseModel):
    city: str
    district: str

class Company(BaseModel):
    name: str
    address: Address  # 嵌套模型

structured_llm = model.with_structured_output(Company)
result = structured_llm.invoke("阿里巴巴在杭州滨江区")
# result.address.city = "杭州"
# result.address.district = "滨江区"
```

## 工作原理

### 传统方式 vs 结构化输出

**传统方式（繁琐）**：

```python
# 1. 提示词要求 JSON
prompt = "以JSON格式返回：{name, age, occupation}"
response = model.invoke(prompt)

# 2. 手动解析
import json
data = json.loads(response.content)

# 3. 手动验证类型
if not isinstance(data['age'], int):
    raise ValueError("age must be int")

# 4. 手动创建对象
person = Person(**data)
```

**结构化输出（简洁）**：
```python
# 一步到位
structured_llm = model.with_structured_output(Person)
person = structured_llm.invoke("张三是一名 30 岁的软件工程师")
# ✅ 自动解析、验证、创建对象
```

### 幕后流程

```
1. Pydantic 模型 → JSON Schema
   Person → {
     "type": "object",
     "properties": {
       "name": {"type": "string", "description": "姓名"},
       "age": {"type": "integer", "description": "年龄"}
     }
   }

2. JSON Schema → LLM (函数调用)
   LLM 被强制返回符合 schema 的 JSON

3. JSON → Pydantic 对象
   自动验证类型并创建 Person 实例
```

## 实际应用

### 1. 客户信息提取

```python
class CustomerInfo(BaseModel):
    name: str = Field(description="客户姓名")
    phone: str = Field(description="电话号码")
    email: Optional[str] = Field(None, description="邮箱")
    issue: str = Field(description="问题描述")

structured_llm = model.with_structured_output(CustomerInfo)

conversation = """
客户: 我是李明，电话 138-1234-5678，订单没发货
"""

info = structured_llm.invoke(f"提取客户信息：{conversation}")
# info.name = "李明"
# info.phone = "138-1234-5678"
# info.issue = "订单没发货"
```

**应用**：
- 自动填充 CRM 系统
- 工单自动分类
- 客服辅助

### 2. 产品评论分析

```python
class Review(BaseModel):
    product: str
    rating: int = Field(description="评分 1-5")
    pros: List[str] = Field(description="优点列表")
    cons: List[str] = Field(description="缺点列表")

structured_llm = model.with_structured_output(Review)

review = structured_llm.invoke("""
iPhone 15 很棒！摄像头强大，手感好。但是价格贵，没有充电器。4分。
""")

# review.product = "iPhone 15"
# review.rating = 4
# review.pros = ["摄像头强大", "手感好"]
# review.cons = ["价格贵", "没有充电器"]
```

**应用**：
- 批量处理用户评论
- 自动生成分析报告
- 发现产品改进点

### 3. 文档信息提取

```python
class Invoice(BaseModel):
    invoice_number: str
    date: str
    total_amount: float
    items: List[str]

structured_llm = model.with_structured_output(Invoice)

invoice_text = """
发票号: INV-2024-001
日期: 2024-01-15
总金额: 1299.00
商品: MacBook Pro, AppleCare+
"""

invoice = structured_llm.invoke(f"提取发票信息：{invoice_text}")
# invoice.invoice_number = "INV-2024-001"
# invoice.total_amount = 1299.00
```

**应用**：
- 自动化财务处理
- OCR 后结构化
- 数据录入

## 常见问题

### 1. LLM 未填充某些字段怎么办？

使用 `Optional` 和默认值：

```python
class Data(BaseModel):
    required_field: str              # 必填
    optional_field: Optional[str] = None  # 可选
    with_default: int = 100          # 有默认值
```

### 2. 如何限制字段的可选值？

使用枚举：

```python
from enum import Enum

class Status(str, Enum):
    ACTIVE = "激活"
    INACTIVE = "未激活"

class User(BaseModel):
    status: Status  # 只能是 ACTIVE 或 INACTIVE
```

### 3. 复杂嵌套结构会出错吗？

LLM 能力有限，建议：
- 嵌套层级 ≤ 3 层
- 使用清晰的 `description`
- 必要时拆分成多个调用

### 4. 如何验证提取的准确性？

见下一章 `12_validation_retry` - 验证和重试机制。

### 5. 所有模型都支持吗？

大部分现代模型支持（通过函数调用）：
- ✅ OpenAI (gpt-4, gpt-3.5-turbo)
- ✅ Anthropic (claude-3)
- ✅ Groq (llama-3)
- ❌ 某些旧模型不支持

如果不支持，LangChain 会回退到提示词 + JSON 解析。

## 最佳实践

```python
# 1. 使用清晰的字段描述
class Good(BaseModel):
    created_at: str = Field(description="创建时间，格式 YYYY-MM-DD")

class Bad(BaseModel):
    created_at: str  # 没有描述，LLM 可能格式错误

# 2. 合理使用 Optional
class Good(BaseModel):
    email: Optional[str] = None  # 邮箱可能没有

class Bad(BaseModel):
    email: str  # 强制必填，可能导致提取失败

# 3. 使用枚举限制值
class Good(BaseModel):
    status: Status  # 枚举

class Bad(BaseModel):
    status: str  # 可能返回任意字符串

# 4. 列表设置合理的描述
class Good(BaseModel):
    tags: List[str] = Field(description="产品标签，如 '电子产品', '手机'")

class Bad(BaseModel):
    tags: List[str]  # LLM 不知道该提取什么

# 5. 嵌套模型保持简单
class Good(BaseModel):
    user: User      # 1 层嵌套
    settings: dict  # 复杂数据用 dict

class Bad(BaseModel):
    user: User
        company: Company
            address: Address
                country: Country  # 4 层嵌套，容易出错
```

## 核心要点

1. **with_structured_output(Model)** - 将 LLM 输出转为 Pydantic 对象
2. **Pydantic BaseModel** - 定义数据模式
3. **Field(description=...)** - 帮助 LLM 理解字段含义
4. **Optional[T]** - 可选字段
5. **List[T]** - 列表类型
6. **Enum** - 限制可选值
7. **嵌套模型** - 处理复杂结构（≤3 层）
8. **自动验证** - Pydantic 自动检查类型

## 下一步

**12_validation_retry** - 学习如何验证提取结果并处理错误重试





# 对于Agent而言

**✅ 问题根源已定位**（非常经典的报错）

你的代码在这一行出了问题：

```python
model = model.with_structured_output(WeatherInfo)   # ← 这里
```

执行完这行后，`model` 已经**不再是原来的 `ChatOpenAI` 对象**，而变成了 `RunnableSequence`（模型 + 输出解析器组成的链）。  
而 `create_agent`（底层是 LangGraph）在构建 Agent 时会自动调用 `model.bind_tools(tools)` 来绑定工具，`RunnableSequence` 没有 `bind_tools` 方法，所以报错：

```
AttributeError: 'RunnableSequence' object has no attribute 'bind_tools'
```

这是 **with_structured_output + Agent** 结合时的常见冲突。

---

**正确做法（2026 年官方推荐）**

不要把 `with_structured_output` 直接套在传给 Agent 的 model 上。  
而是使用 **`create_agent` 的 `response_format` 参数**，让 Agent 内部自动处理结构化输出（支持 ProviderStrategy / ToolStrategy）。

### 修复后的完整可运行代码（直接复制替换）

```python
"""
学习Pydantic结构化输出模型 - 正确写法
"""

import os
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv(override=True)

model_name = os.getenv("MODEL", "gpt-3.5-turbo")
base_url = os.getenv("BASE_URL", "http://localhost:8000")
api_key = os.getenv("API_KEY")

# 1. 使用原始模型创建 Agent（必须是原始 ChatModel）
base_model = ChatOpenAI(
    model=model_name,
    base_url=base_url,
    api_key=api_key
)

class WeatherInfo(BaseModel):
    city: str
    temperature: float = Field(..., description="Temperature in Celsius")
    condition: str = Field(..., description="Weather condition, e.g., sunny, rainy")

@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息"""
    if city == "北京":
        return WeatherInfo(city=city, temperature=25.0, condition="sunny").model_dump_json()
    elif city == "上海":
        return WeatherInfo(city=city, temperature=28.0, condition="cloudy").model_dump_json()
    elif city == "广州":
        return WeatherInfo(city=city, temperature=30.0, condition="rainy").model_dump_json()
    else:
        return WeatherInfo(city=city, temperature=20.0, condition="sunny").model_dump_json()

# 2. 创建 Agent + 结构化输出（关键在这里！）
agent = create_agent(
    model=base_model,                    # ← 原始模型
    tools=[get_weather],
    system_prompt="你是一个天气预报助手，请先使用工具获取天气，然后严格按照 WeatherInfo 格式输出结构化信息。",
    response_format=WeatherInfo,         # ← 官方推荐写法，自动结构化输出
)

# 3. 调用 Agent
res = agent.invoke({"messages": [{"role": "user", "content": "请告诉我北京的天气。"}]})

# 4. 查看结果（结构化数据在 'structured_response' 里）
print("=== Agent 完整状态 ===")
print(res)

print("\n=== 结构化输出结果（Pydantic 对象）===")
structured = res["structured_response"]   # 自动解析后的 WeatherInfo 对象
print(structured)
print(f"城市: {structured.city}")
print(f"温度: {structured.temperature}°C")
print(f"天气: {structured.condition}")
```

### 运行后预期输出
```
=== 结构化输出结果（Pydantic 对象）===
city='北京' temperature=25.0 condition='sunny'
城市: 北京
温度: 25.0°C
天气: sunny
```

---

**额外说明**

- `response_format=WeatherInfo` 是官方在 `create_agent` 中专门为结构化输出准备的参数，内部会自动选择最合适的策略（原生 JSON Schema 或 ToolStrategy）。
- 如果你想在普通 chain（非 Agent）中使用结构化输出，才用 `model.with_structured_output()`。
- 工具里返回 `model_dump_json()` 很好，Agent 能轻松读取。

这样就彻底解决了报错，同时符合最新最佳实践。  
想再加 `include_raw=True`（同时返回原始文本）、异步版本、或把 `create_agent` 换成 `create_react_agent` 也行，随时告诉我！🚀
