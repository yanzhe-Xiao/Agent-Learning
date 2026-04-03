# ... existing code ...

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

images_path = Path(__file__).parent / "images"
image_file = images_path / "qq_music.png"

# 检查图片是否存在
if not image_file.exists():
    print(f"❌ 图片不存在：{image_file}")
    print("请将 qq_music.png 放入 images/ 目录")
    exit()

# 将图片编码为 base64
with open(image_file, "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

# 获取 MIME 类型
mime_type = "image/png" if image_file.suffix.lower() == ".png" else "image/jpeg"

messages=[
    SystemMessage(content="你是一个图像分析专家，能够理解和分析图片内容。"),
    HumanMessage(content=[
        {"type": "text", "text": "请分析这张图片的内容。"},
        {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}
        }
    ])
]

response = model.invoke(messages)
print(response.content)
print("=" * 60)
agent = create_agent(
    model=model,
    tools=[],
    system_prompt="你是一个图像分析专家，能够理解和分析图片内容。",
)

images_path = Path(__file__).parent / "images"
image_file = images_path / "qq_music.png"

if not image_file.exists():
    raise FileNotFoundError(f"图片不存在：{image_file}")

with open(image_file, "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

mime_type = "image/png" if image_file.suffix.lower() == ".png" else "image/jpeg"

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请分析这张图片的内容。"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_base64}"
                        },
                    },
                ],
            }
        ]
    }
)

print(result["messages"][-1].content)