import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

# ==================== 1. 初始化 embedding（必须和当初建库时用同一个模型！） ====================
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ==================== 2. 加载已存在的 Pinecone 向量库 ====================
vectorstore = PineconeVectorStore.from_existing_index(
    index_name="langchain-rag-demo",   # ← 你的索引名字
    embedding=embeddings
)

print("✅ 成功加载现有向量数据库！")
print(f"当前记录数量: {vectorstore.index.describe_index_stats()['total_vector_count']}")