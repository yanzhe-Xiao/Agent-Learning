"""
演示：对话历史过长的问题
"""

import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.redis import RedisSaver  

load_dotenv(override=True)
model_name = os.getenv("MODEL")
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_mini = os.getenv("MODEL_MINI")
model = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
)
print(os.getenv("REDIS_URL"))

def demo_long_conversation():
    """
    演示：对话历史过长的问题
    """
    print("\n" + "="*70)
    print(" 演示：对话历史过长的性能问题")
    print("="*70)

    with RedisSaver.from_conn_string(os.getenv("REDIS_URL")) as checkpointer:
        checkpointer.setup()
        agent = create_agent(
            model=model,
            tools=[],
            system_prompt="你是一个有帮助的助手。",
            checkpointer=checkpointer
        )

        config = {"configurable": {"thread_id": "test_user"}}

        # 模拟 50 轮对话
        print("\n[模拟 5 轮对话...]")
        # for i in range(1, 6):
        #     agent.invoke(
        #         {"messages": [{"role": "user", "content": f"hello,can u tell me the current time? This is round {i}."}]},
        #         config=config
        #     )
        #     if i % 10 == 0:
        #         print(f"  已完成 {i} 轮...")

        print("\n[尝试获取状态，查看加载的消息数量...]")

        # === 关键修复 ===
        state = agent.get_state(config)          # ← 改成 agent.get_state，而不是 checkpointer.get
        if state and state.values:
            messages = state.values.get("messages", [])
            from langchain_core.messages import HumanMessage, AIMessage
            human_messages = [msg.content for msg in messages if isinstance(msg, HumanMessage)]
            ai_messages = [msg.content for msg in messages if isinstance(msg, AIMessage)]
            print(list(zip(human_messages, ai_messages)))
            print(list(msg.content for msg in messages if isinstance(msg, BaseMessage)))
            print(f"\n⚠️ 当前加载的消息数量：{len(messages)}")
            print(f"⚠️ 这意味着每次 invoke 都会加载这么多消息！")

            # 计算大致的 Token 数（简化估算）
            total_chars = sum(len(str(msg)) for msg in messages)
            estimated_tokens = total_chars // 4  # 粗略估算
            print(f"⚠️ 估算 Token 数：~{estimated_tokens}")

            print("\n问题：")
            print("  1. 随着对话增长，每次加载的数据越来越多")
            print("  2. 超过模型上下文窗口限制会报错")
            print("  3. 性能下降，响应变慢")
            print("  4. Token 费用增加")

    is_clean = input("\n是否清理测试数据？(y/n): ").strip().lower() == 'y'
    if is_clean:
        checkpointer.delete_thread("test_user")  # 清理测试数据

def show_solutions():
    """
    展示解决方案
    """
    print("\n" + "="*70)
    print(" 解决方案")
    print("="*70)

    print("""
LangChain 提供了多种策略来管理上下文：

1. 消息修剪（Message Trimming）⭐ 推荐
   - 只保留最近 N 条消息
   - 保留系统消息 + 最近对话

2. 消息摘要（Summarization）
   - 定期总结旧消息
   - 用摘要替换历史

3. 滑动窗口（Sliding Window）
   - 固定窗口大小
   - 自动丢弃旧消息

4. Token 限制
   - 根据 Token 数量裁剪
   - 适配不同模型的上下文窗口

这些策略在 phase2_practical/08_context_management 模块中详细讲解！
    """)

if __name__ == "__main__":
    try:
        demo_long_conversation()
        show_solutions()

        print("\n" + "="*70)
        print(" 下一步")
        print("="*70)
        print("\n查看详细解决方案：")
        print("  cd phase2_practical/08_context_management")
        print("  python main.py")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
