# # ... existing code ...

import os
import base64
from pathlib import Path

import dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
dotenv.load_dotenv()
prefix = "OPENROUTER_"
base_url = os.getenv(f"{prefix}BASE_URL")
api_key = os.getenv(f"{prefix}API_KEY")
model_name = os.getenv(f"{prefix}MODEL")

model = ChatOpenAI(
    model=model_name, # type: ignore
    api_key=api_key, # type: ignore
    base_url=base_url,
)

# images_path = Path(__file__).parent / "images"
# image_file = images_path / "qq_music.png"

# # 检查图片是否存在
# if not image_file.exists():
#     print(f"❌ 图片不存在：{image_file}")
#     print("请将 qq_music.png 放入 images/ 目录")
#     exit()

# # 将图片编码为 base64
# with open(image_file, "rb") as f:
#     image_base64 = base64.b64encode(f.read()).decode("utf-8")

# # 获取 MIME 类型
# mime_type = "image/png" if image_file.suffix.lower() == ".png" else "image/jpeg"

# messages=[
#     SystemMessage(content="你是一个图像分析专家，能够理解和分析图片内容。"),
#     HumanMessage(content=[
#         {"type": "text", "text": "请分析这张图片的内容。"},
#         {
#             "type": "image_url",
#             "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}
#         }
#     ])
# ]

# response = model.invoke(messages)
# print(response.content)
# print("=" * 60)
# agent = create_agent(
#     model=model,
#     tools=[],
#     system_prompt="你是一个图像分析专家，能够理解和分析图片内容。",
# )

# images_path = Path(__file__).parent / "images"
# image_file = images_path / "qq_music.png"

# if not image_file.exists():
#     raise FileNotFoundError(f"图片不存在：{image_file}")

# with open(image_file, "rb") as f:
#     image_base64 = base64.b64encode(f.read()).decode("utf-8")

# mime_type = "image/png" if image_file.suffix.lower() == ".png" else "image/jpeg"

# result = agent.invoke(
#     {
#         "messages": [
#             {
#                 "role": "user",
#                 "content": [
#                     {"type": "text", "text": "请分析这张图片的内容。"},
#                     {
#                         "type": "image_url",
#                         "image_url": {
#                             "url": f"data:{mime_type};base64,{image_base64}"
#                         },
#                     },
#                 ]
#             }
#         ]
#     }
# )

# print(result["messages"][-1].content)

import base64
import mimetypes
from pathlib import Path

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
# 也可以换成支持图像输入的别的模型，例如 Gemini / Anthropic

# ALLOWED_ROOT = Path("/absolute/path/to/your/images").resolve()

# def _safe_resolve(path: str) -> Path:
#     p = (ALLOWED_ROOT / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
#     if ALLOWED_ROOT not in p.parents and p != ALLOWED_ROOT:
#         raise ValueError(f"Path not allowed: {p}")
#     if not p.exists():
#         raise FileNotFoundError(f"File not found: {p}")
#     return p

@tool
def read_local_image(path: str):
    """Read a local image and return it to the model as multimodal content.

    Use this tool whenever you need to inspect an image rather than guess.
    Examples:
    - screenshots / UI / charts / diagrams
    - asking what's in an image
    - checking colors, layout, objects, labels, or visible text

    Args:
        path: Absolute path, or a path relative to the allowed image root.
    """
    p = Path(path).resolve()
    mime_type, _ = mimetypes.guess_type(str(p))
    if mime_type is None or not mime_type.startswith("image/"):
        raise ValueError(f"Not an image file: {p}")

    image_b64 = base64.b64encode(p.read_bytes()).decode("utf-8")

    # 返回 LangChain 标准多模态 content block
    return [
        {
            "type": "image",
            "base64": image_b64,
            "mime_type": mime_type,
        }
    ]

# model = ChatOpenAI(
#     model="gpt-4.1-mini",   # 换成你实际使用的支持看图模型
#     temperature=0,
# )

agent = create_agent(
    model=model,
    tools=[read_local_image],
    system_prompt=(
        "You are a careful vision-capable assistant.\n"
        "Do not guess image contents.\n"
        "If the user asks anything that depends on inspecting an image, please pay attention to the fact that our system is Windows"
        "you must call read_local_image first."
    ),
)

result = agent.invoke({
    "messages": [
        {
            "role": "user",
            # 使用原始字符串避免转义问题，或使用 Path 构建绝对路径
            "content": r"看看 D:\Projects\Agent-Learning\langchainv1_api\phase3_advanced\19_image_input\images\sample.png 这个女生穿了什么颜色的衣服？"
        }
    ]
})

print(result['messages'][-1].content)