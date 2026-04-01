# 06 - Agent Loop (Agent 执行循环)

## 核心概念

**Agent 执行循环 = 自动化的"思考-行动-观察"过程**

Agent 不是一次性调用，而是一个循环：
```
用户问题 → AI 思考 → 调用工具 → 观察结果 → 继续思考 → 最终答案
```

## 执行循环详解

### 完整流程

```
┌─────────────┐
│ 用户提问    │
│ HumanMessage│
└──────┬──────┘
       ↓
┌─────────────┐
│ AI 分析问题 │
│ 需要工具？  │
└──────┬──────┘
       ↓ 是
┌─────────────┐
│ AI 决定调用 │
│ AIMessage   │
│ (tool_calls)│
└──────┬──────┘
       ↓
┌─────────────┐
│ 执行工具    │
│ ToolMessage │
└──────┬──────┘
       ↓
┌─────────────┐
│ AI 看结果   │
│ 生成答案    │
│ AIMessage   │
└─────────────┘
```

### 消息历史示例

```python
response = agent.invoke({
    "messages": [{"role": "user", "content": "25 乘以 8"}]
})

# response['messages'] 包含：
[
    HumanMessage(content="25 乘以 8"),
    AIMessage(tool_calls=[{
        'name': 'calculator',
        'args': {'operation': 'multiply', 'a': 25, 'b': 8}
    }]),
    ToolMessage(content="25.0 multiply 8.0 = 200.0"),
    AIMessage(content="25 乘以 8 等于 200")
]
```

## 查看执行过程

### 1. 查看完整历史

```python
response = agent.invoke({"messages": [...]})

for msg in response['messages']:
    print(f"{msg.__class__.__name__}: {msg.content}")
```

### 2. 获取最终答案

```python
# 最后一条消息就是最终答案
final_answer = response['messages'][-1].content
```

### 3. 查看使用的工具

```python
used_tools = []
for msg in response['messages']:
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        for tc in msg.tool_calls:
            used_tools.append(tc['name'])

print(f"使用的工具: {used_tools}")
```

## 流式输出（Streaming）

用于实时显示 Agent 的执行进度和输出。

`stream()` 返回一个生成器，每次产生一个数据块 `chunk`，代表执行过程中的一次更新。  
通过 `stream_mode` 参数，可以控制每个 `chunk` 里包含什么内容。

### 基本用法

```python
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

agent = create_react_agent(model, tools)

for chunk in agent.stream(
    {"messages": [HumanMessage(content="北京天气如何？")]},
    config={"configurable": {"thread_id": "demo-thread"}},
):
    print(chunk)
```

### 支持的 Stream Mode

| 模式 | 返回内容 | 适用场景 |
| --- | --- | --- |
| `"values"` | 每一步执行后的完整状态 | 需要查看完整 `messages` 历史 |
| `"updates"` | 当前步骤的增量更新 | 只关心哪个节点更新了什么 |
| `"messages"` | `(message, metadata)` 元组 | 实现逐字打印、流式聊天 |
| `"debug"` | 详细调试事件 | 排查执行流程问题 |

### 使用说明

- 如果你想直接读取 `chunk["messages"]`，优先显式传 `stream_mode="values"`。
- `updates` 更适合观察 `model`、`tools` 等节点分别返回了什么。
- `messages` 更适合做打字机式输出，因为它会按消息片段或 token 流式返回。

### 各模式详解与示例

下面用“查询天气”的例子说明不同模式下 `chunk` 的结构。

### 1. `stream_mode="values"`

每次返回完整的当前状态字典。随着 Agent 继续执行，`messages` 列表会不断变长。

```python
for chunk in agent.stream(
    {"messages": [HumanMessage(content="北京天气如何？")]},
    stream_mode="values",
):
    print(chunk)
```

输出示例：

```text
--- Chunk 1 ---
{'messages': [HumanMessage(content='北京天气如何？')]}

--- Chunk 2 ---
{'messages': [HumanMessage(...), AIMessage(tool_calls=[...])]}

--- Chunk 3 ---
{'messages': [HumanMessage(...), AIMessage(...), ToolMessage(content='晴天，温度 15°C，空气质量良好')]}

--- Chunk 4 ---
{'messages': [..., AIMessage(content='北京现在是晴天，温度 15°C，空气质量良好。')]}
```

特点：

- 每个 `chunk` 都是完整状态，通常至少包含 `messages`。
- 可以通过 `chunk["messages"][-1]` 读取当前最新消息。
- 最适合教学、调试，以及实时展示完整对话列表。

### 2. `stream_mode="updates"`

只返回当前步骤中发生变化的节点输出，键通常是节点名，值是该节点本次新增的状态片段。

```python
for chunk in agent.stream(
    {"messages": [HumanMessage(content="10 加 20 等于多少？")]},
    stream_mode="updates",
):
    print(chunk)
```

输出示例：

```text
--- Chunk 1 ---
{'model': {'messages': [AIMessage(tool_calls=[...])]}}

--- Chunk 2 ---
{'tools': {'messages': [ToolMessage(content='10.0 add 20.0 = 30.0')]}}

--- Chunk 3 ---
{'model': {'messages': [AIMessage(content='10 加 20 等于 30。')]}}
```

特点：

- 结构通常是 `{节点名: {更新内容}}`。
- 可以精确看到是 `model` 还是 `tools` 节点产生了更新。
- 更适合按节点做监控、日志记录和增量处理。

### 3. `stream_mode="messages"`

直接返回 `(message, metadata)` 元组。  
其中 `message` 是消息对象或消息片段，`metadata` 里通常会包含 `langgraph_node` 等信息。

```python
for msg, metadata in agent.stream(
    {"messages": [HumanMessage(content="北京天气如何？")]},
    stream_mode="messages",
):
    print(f"消息: {msg.content}, 元数据: {metadata}")
```

输出示例：

```text
消息: (空), 元数据: {'langgraph_node': 'model', ...}
消息: 晴天，温度 15°C，空气质量良好, 元数据: {'langgraph_node': 'tools', ...}
消息: 北京, 元数据: {'langgraph_node': 'model', ...}
消息: 现在, 元数据: {...}
消息: 是, 元数据: {...}
消息: 晴天，元数据: {...}
...
```

特点：

- 每产生一个消息片段，就会立即返回一次。
- 对于 `AIMessageChunk`，`content` 往往只是最终回答的一部分。
- 非常适合实现类似 ChatGPT 的逐字输出效果。

注意：

- 当模型决定调用工具时，可能先返回一个没有可见 `content`、但包含 `tool_calls` 的消息。
- 因此做前端展示时，不能只按 `content` 是否为空来判断是否“没有事件”。

### 4. `stream_mode="debug"`

返回详细调试事件。每个 `chunk` 会包含更丰富的执行过程信息，适合排查图执行流程。

```python
for chunk in agent.stream(
    {"messages": [HumanMessage(content="北京天气如何？")]},
    stream_mode="debug",
):
    print(chunk)
```

输出示例：

```text
--- Debug Chunk ---
type: checkpoint
payload 包含: ['config', 'values', 'metadata', 'next', ...]

--- Debug Chunk ---
type: task
payload 包含: ['id', 'name', 'input', ...]

--- Debug Chunk ---
type: task_result
payload 包含: ['id', 'result', ...]
```

特点：

- 数据量最大，只适合开发和调试阶段。
- 可以按 `type` 过滤你关心的事件，例如 `checkpoint`、`task`、`task_result`。
- 适合排查“为什么某个节点没执行”或“工具调用过程发生了什么”。

### 实际应用建议

- 实现聊天界面：使用 `messages` 模式，逐字打印 AI 回复。
- 记录完整对话：使用 `values` 模式，保存完整 `messages`。
- 监控特定节点：使用 `updates` 模式，只记录 `tools` 或 `model` 节点输出。
- 调试复杂流程：使用 `debug` 模式，查看完整执行事件。

### 完整示例代码

```python
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    return f"{city} 现在是晴天，温度 25°C。"


tools = [get_weather]
agent = create_react_agent(model, tools)

print("=" * 40)
print("流式输出（逐字）")
print("=" * 40)

for msg, metadata in agent.stream(
    {"messages": [HumanMessage(content="北京天气如何？")]},
    stream_mode="messages",
):
    if isinstance(msg, AIMessageChunk) and msg.content:
        print(msg.content, end="", flush=True)

print("\n")
```

通过选择合适的 `stream_mode`，可以灵活控制流式输出的粒度，满足从教学演示到生产环境的不同需求。

### stream vs invoke

| 方法 | 返回 | 用途 |
|-----|------|------|
| `invoke()` | 完整结果 | 等待完成后一次性获取 |
| `stream()` | 生成器 | 实时获取中间步骤 |

## 消息类型

### HumanMessage
用户的输入

```python
HumanMessage(content="北京天气如何？")
```

### AIMessage（两种情况）

**情况1：调用工具**
```python
AIMessage(
    content="",
    tool_calls=[{
        'name': 'get_weather',
        'args': {'city': '北京'},
        'id': 'call_xxx'
    }]
)
```

**情况2：最终答案**
```python
AIMessage(content="北京今天晴天，温度 15°C")
```

### ToolMessage
工具执行的结果

```python
ToolMessage(
    content="晴天，温度 15°C",
    name="get_weather"
)
```

### SystemMessage
系统指令（通过 `system_prompt` 设置）

```python
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt="你是一个helpful assistant"
)
```

## 多步骤执行

Agent 可以多次调用工具：

```python
# 问题：先算 10 + 20，然后乘以 3
response = agent.invoke({
    "messages": [{"role": "user", "content": "先算 10 + 20，然后乘以 3"}]
})

# Agent 可能会：
# 1. 调用 calculator(add, 10, 20) → 30
# 2. 调用 calculator(multiply, 30, 3) → 90
# 3. 返回最终答案
```

统计工具调用次数：
```python
tool_calls_count = sum(
    len(msg.tool_calls) if hasattr(msg, 'tool_calls') and msg.tool_calls else 0
    for msg in response['messages']
)
```

## 调试技巧

### 1. 打印所有消息

```python
for i, msg in enumerate(response['messages'], 1):
    print(f"\n--- 消息 {i}: {msg.__class__.__name__} ---")

    if hasattr(msg, 'content'):
        print(f"内容: {msg.content}")

    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        for tc in msg.tool_calls:
            print(f"工具: {tc['name']}, 参数: {tc['args']}")
```

### 2. 使用 stream 查看步骤

```python
step = 0
for chunk in agent.stream(input):
    step += 1
    print(f"步骤 {step}:")
    if 'messages' in chunk:
        latest = chunk['messages'][-1]
        print(f"  类型: {latest.__class__.__name__}")
```

### 3. 检查是否使用工具

```python
has_tool_calls = any(
    hasattr(msg, 'tool_calls') and msg.tool_calls
    for msg in response['messages']
)

if has_tool_calls:
    print("Agent 使用了工具")
else:
    print("Agent 直接回答")
```

## 常见问题

### 1. 如何知道 Agent 何时完成？

**答：当 AIMessage 不包含 tool_calls 时**

```python
for msg in response['messages']:
    if isinstance(msg, AIMessage):
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            print("还在调用工具...")
        else:
            print("完成！最终答案：", msg.content)
```

### 2. Agent 可以调用多少次工具？

**答：默认没有限制，直到得到最终答案**

但可能会：
- 超时
- 达到 token 限制
- 模型决定停止

### 3. 如何限制工具调用次数？

LangChain 1.0 的 `create_agent` 默认使用 LangGraph，可以通过配置限制：

```python
# 注意：这是高级用法，后续会详细学习
config = {
    "recursion_limit": 5  # 最多 5 步
}

response = agent.invoke(input, config=config)
```

## 最佳实践

### 1. 生产环境获取答案

```python
try:
    response = agent.invoke(input)
    final_answer = response['messages'][-1].content
    return final_answer
except Exception as e:
    logger.error(f"Agent 错误: {e}")
    return "抱歉，出现错误"
```

### 2. 用户体验优化

```python
# 使用流式输出
print("正在思考...")
for chunk in agent.stream(input):
    if 'messages' in chunk:
        latest = chunk['messages'][-1]
        # 显示进度
```

### 3. 调试和监控

```python
response = agent.invoke(input)

# 记录使用的工具
tools_used = [
    tc['name']
    for msg in response['messages']
    if hasattr(msg, 'tool_calls') and msg.tool_calls
    for tc in msg.tool_calls
]

logger.info(f"工具使用: {tools_used}")
```

### 4. 错误处理

```python
try:
    response = agent.invoke(input)

    # 检查是否成功
    if not response['messages']:
        raise ValueError("没有收到响应")

    final = response['messages'][-1]
    if not hasattr(final, 'content') or not final.content:
        raise ValueError("没有最终答案")

    return final.content

except Exception as e:
    # 记录详细错误
    logger.error(f"Agent 执行失败: {e}", exc_info=True)
    return None
```

## 运行示例

```bash
# 运行所有示例
python main.py

# 测试
python test.py
```

## 核心要点总结

1. **执行循环**：问题 → 工具调用 → 结果 → 答案
2. **messages 历史**：记录完整对话过程
3. **流式输出**：`stream()` 实时显示进度
4. **消息类型**：HumanMessage、AIMessage、ToolMessage
5. **最终答案**：`response['messages'][-1].content`

## 下一步

**阶段一（基础）完成！**

已学习：
- 01: 环境搭建和模型调用
- 02: 提示词模板
- 03: 消息类型和对话
- 04: 自定义工具
- 05: Simple Agent
- 06: Agent 执行循环

**下一阶段：phase2_intermediate**
- 内存和状态管理
- 中间件架构
- 结构化输出
