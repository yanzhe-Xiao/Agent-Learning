# 14 - RAG Advanced (RAG 进阶)

## 快速开始

```bash
# 1. 安装额外依赖
pip install rank_bm25 chromadb langchain-classic

# 2. 运行完整示例
cd phase2_practical
python 14_rag_advanced/main.py

# 3. 运行测试（无需 API key）
python 14_rag_advanced/test.py
```

**重要提示（LangChain 1.0）**：
- EnsembleRetriever 在 LangChain 1.0 中已移至 `langchain-classic` 包
- 正确导入：`from langchain_classic.retrievers import EnsembleRetriever`
- ~~错误导入~~：~~`from langchain.retrievers import EnsembleRetriever`~~（已废弃）

## 核心概念

### 为什么需要进阶 RAG？

基础 RAG（只用向量搜索）的局限性：
- ❌ 精确匹配差：搜不到专有名词、版本号
- ❌ 关键词弱：对代码、配置查询效果不佳
- ❌ 鲁棒性低：查询表达不同，结果差异大

**混合检索解决方案**：向量搜索 + BM25 = 全面覆盖

## 1. 向量检索 vs BM25 检索

### 向量检索（Vector Search / Semantic Search）

**原理**：将文本转为向量，计算余弦相似度

**优势**：
- ✅ 理解语义和同义词
- ✅ 处理概念性查询
- ✅ 跨语言查询

**劣势**：
- ❌ 精确匹配差
- ❌ 对专有名词不敏感

**示例**：
```python
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
results = vector_retriever.invoke("LangChain 的核心功能")
```

### BM25 检索（Keyword Search）

**原理**：基于词频(TF-IDF的改进版)，计算词的重要性

**优势**：
- ✅ 精确匹配专有名词
- ✅ 代码、版本号查询准确
- ✅ 速度快，无需嵌入

**劣势**：
- ❌ 不理解语义
- ❌ 同义词无法匹配

**示例**：
```python
from langchain_community.retrievers import BM25Retriever

bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 3

results = bm25_retriever.invoke("langchain>=1.0.0")
```

### 对比测试

| 查询类型 | 查询示例 | 向量搜索 | BM25 | 混合检索 |
|---------|---------|---------|------|---------|
| 语义查询 | "LangChain 的主要功能" | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ |
| 精确匹配 | "langchain>=1.0.0" | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 专有名词 | "BM25 算法" | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 概念查询 | "如何优化性能" | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ |
| 代码查询 | "@tool def search" | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

## 2. EnsembleRetriever（混合检索器）

### 什么是 Ensemble Retriever？

组合多个检索器，使用 **RRF (Reciprocal Rank Fusion)** 算法融合结果。

### RRF 算法原理

```
对于文档 d：
  BM25 排名: rank_bm25(d)
  向量排名: rank_vector(d)

  RRF 得分 = w1 / (k + rank_bm25) + w2 / (k + rank_vector)

  其中：
  - w1, w2 是权重
  - k 是常数（通常为 60）
```

### 基本用法

```python
from langchain_classic.retrievers import EnsembleRetriever

# 创建混合检索器
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.5, 0.5]  # 平衡权重
)

# 使用
results = ensemble_retriever.invoke("查询文本")
```

### 权重配置

```python
# 1. 平衡（默认推荐）
weights=[0.5, 0.5]

# 2. 偏向语义（适合：文章、对话）
weights=[0.4, 0.6]  # BM25 40%, 向量 60%

# 3. 偏向精确匹配（适合：代码、配置）
weights=[0.6, 0.4]  # BM25 60%, 向量 40%

# 4. 纯向量（基础 RAG）
weights=[0.0, 1.0]

# 5. 纯 BM25（传统搜索）
weights=[1.0, 0.0]
```

## 3. 完整实现

### 离线阶段：建立索引

```python
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

# 1. 加载和分割
loader = TextLoader("docs.txt")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = splitter.split_documents(documents)

# 2. 创建向量检索器
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 3. 创建 BM25 检索器
bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 3

# 4. 创建混合检索器
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.4, 0.6]  # 稍偏向语义
)
```

### 在线阶段：RAG 问答

```python
from langchain.agents import create_agent
from langchain_core.tools import tool

# 1. 创建检索工具
@tool
def search_docs(query: str) -> str:
    """在文档库中搜索相关信息"""
    docs = ensemble_retriever.invoke(query)
    return "\n\n".join([doc.page_content for doc in docs])

# 2. 创建 Agent
agent = create_agent(
    model=model,
    tools=[search_docs],
    system_prompt="你是助手。使用 search_docs 搜索信息，然后回答问题。"
)

# 3. 问答
response = agent.invoke({
    "messages": [{"role": "user", "content": "LangChain 有什么特性？"}]
})
```

## 4. 性能优化

### 4.1 权重调整策略

```python
# 根据数据类型选择权重
def get_optimal_weights(data_type):
    weights_map = {
        "technical_docs": [0.4, 0.6],  # 偏向语义
        "code_base": [0.6, 0.4],       # 偏向精确
        "mixed": [0.5, 0.5],           # 平衡
        "conversation": [0.3, 0.7],    # 强语义
    }
    return weights_map.get(data_type, [0.5, 0.5])
```

### 4.2 检索数量 (k 值)

```python
# k 值选择
- k=1: 只要最相关的（快，但可能不全面）
- k=3: 推荐（平衡速度和覆盖率）
- k=5: 更全面（但增加噪音和 token 成本）
- k=10: 大量上下文（慢，成本高）
```

### 4.3 监控和评估

```python
# 评估检索质量
def evaluate_retrieval(retriever, query, expected_content):
    results = retriever.invoke(query)

    # 检查是否包含预期内容
    for doc in results:
        if expected_content in doc.page_content:
            return True, results[0].page_content

    return False, results[0].page_content if results else ""

# 测试
success, result = evaluate_retrieval(
    ensemble_retriever,
    "LangChain 1.0 新特性",
    "LangChain 1.0"
)
```

## 5. 常见问题

### Q1: 混合检索一定比单一检索好吗？

**A**: 大多数情况是，但不绝对。

**适合混合**：
- ✅ 查询类型多样（语义 + 精确）
- ✅ 文档包含代码、配置、术语
- ✅ 用户查询质量参差不齐

**可能不需要**：
- 纯对话场景（全语义）
- 纯代码搜索（全精确）
- 性能要求极高（BM25 更快）

### Q2: 如何选择权重？

**A**: 从 `[0.5, 0.5]` 开始，根据测试调整

```python
# 测试流程
1. 收集典型查询（10-20个）
2. 测试不同权重：[0.3,0.7], [0.5,0.5], [0.7,0.3]
3. 对比前3个结果的相关性
4. 选择最优配置
```

### Q3: BM25Retriever 需要额外依赖吗？

**A**: 是的，需要安装 `rank_bm25`

```bash
pip install rank_bm25
```

### Q4: Chroma vs Pinecone vs FAISS？

| 特性 | Chroma | Pinecone | FAISS |
|-----|--------|----------|-------|
| 部署 | 本地 | 云端 | 本地 |
| 速度 | 中 | 快 | 最快 |
| 扩展性 | 小规模 | 大规模 | 中规模 |
| 成本 | 免费 | 免费层 | 免费 |
| 易用性 | 高 | 高 | 中 |
| **推荐** | 开发 | 生产 | 离线/高性能 |

### Q5: 混合检索会慢吗？

**A**: 会慢一点，但影响小

```
单一向量搜索: ~50ms
单一 BM25:    ~10ms
混合检索:      ~60ms  (并行执行)

增加: ~10ms，可接受
```

### Q6: 如何处理大量文档？

```python
# 策略 1: 分层检索
1. 先用 BM25 快速过滤到 top-100
2. 再用向量搜索精选 top-3

# 策略 2: 预过滤
1. 用元数据过滤（日期、分类）
2. 在子集上做混合检索

# 策略 3: 缓存热门查询
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query):
    return ensemble_retriever.invoke(query)
```

## 6. 最佳实践

### 6.1 生产环境检查清单

```python
# ✅ 检查清单
1. [ ] 使用混合检索而非单一方法
2. [ ] 根据数据类型调整权重
3. [ ] 设置合适的 k 值（推荐 3-5）
4. [ ] 监控检索质量（定期评估）
5. [ ] 使用持久化向量存储
6. [ ] 缓存热门查询
7. [ ] 设置超时和重试机制
```

### 6.2 代码模板

```python
# 生产级混合 RAG 系统
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class HybridRAGSystem:
    def __init__(self, documents, weights=[0.5, 0.5]):
        # 初始化
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # 向量存储
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory="./chroma_db"
        )

        # BM25
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        self.bm25_retriever.k = 5

        # 混合检索
        vector_retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 5}
        )

        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self.bm25_retriever, vector_retriever],
            weights=weights
        )

    @lru_cache(maxsize=100)
    def search(self, query: str, k: int = 3):
        """缓存的搜索"""
        try:
            results = self.ensemble_retriever.invoke(query)
            return results[:k]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def create_rag_agent(self, model):
        """创建 RAG Agent"""
        @tool
        def search_docs(query: str) -> str:
            """搜索文档"""
            docs = self.search(query)
            return "\n\n".join([doc.page_content for doc in docs])

        return create_agent(
            model=model,
            tools=[search_docs],
            system_prompt="你是助手。使用 search_docs 搜索信息。"
        )
```

### 6.3 测试套件

```python
# 测试混合检索效果
test_cases = [
    {
        "query": "LangChain 核心组件",
        "expected_keywords": ["Models", "Prompts", "Agents"],
        "type": "semantic"
    },
    {
        "query": "langchain>=1.0.0",
        "expected_keywords": ["版本", "1.0.0"],
        "type": "exact"
    },
    {
        "query": "BM25 算法原理",
        "expected_keywords": ["BM25", "词频", "TF-IDF"],
        "type": "hybrid"
    }
]

def run_tests(retriever):
    passed = 0
    for test in test_cases:
        results = retriever.invoke(test["query"])
        content = " ".join([doc.page_content for doc in results])

        if all(kw in content for kw in test["expected_keywords"]):
            passed += 1
            print(f"✓ {test['type']}: {test['query']}")
        else:
            print(f"✗ {test['type']}: {test['query']}")

    print(f"\n通过: {passed}/{len(test_cases)}")
```

## 7. 进一步学习

### 下一步主题

- **重排序 (Reranking)**: 使用 CrossEncoder 重新排序
- **查询优化**: Query rewriting, HyDE
- **元数据过滤**: 根据时间、分类过滤
- **多查询**: 生成多个查询变体
- **上下文压缩**: 减少无关信息

### 相关资源

- LangChain 文档: https://python.langchain.com/docs/how_to/ensemble_retriever/
- BM25 论文: https://en.wikipedia.org/wiki/Okapi_BM25
- RRF 算法: https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf

## 核心要点总结

1. **混合检索 = 向量 + BM25** - 结合两者优势
2. **EnsembleRetriever** - LangChain 的标准组合器
3. **RRF 算法** - 融合多个排名结果
4. **权重调整** - 根据数据类型优化
5. **生产就绪** - 监控、缓存、容错

混合检索是现代 RAG 系统的标准配置，能显著提升检索质量和鲁棒性！





RRF，全称是倒数排序融合（Reciprocal Rank Fusion），它是一种在RAG系统中用来整合多个不同检索结果的关键算法。它的核心是**不看分数看排名**。

当我们同时使用关键词搜索（如BM25）和向量搜索等多种检索方式时，RRF能巧妙地将它们各自给出的排名融合成一个更优的新排名[reference:0][reference:1]。

### 🤔 为什么要用RRF？解决不同分数的“不可比”难题

不同的检索方法产生的分数“单位”完全不同，直接比较就像“苹果和桔子”：
*   **关键词搜索**：返回的是基于词频统计的分数，比如 **12.4**[reference:2]。
*   **向量搜索**：返回的是基于语义相似度的距离，比如 **0.85**[reference:3]。
RRF的巧妙之处在于**完全忽略这些无法直接比较的原始分数，只看每个文档在各自结果列表里的排名位置**，从而避免了复杂的分数归一化处理[reference:4][reference:5]。

### 🧮 RRF公式详解：排名越高，贡献越大

RRF通过一个简单的公式计算每个文档的最终得分：得分越高的文档，最终排名越靠前[reference:6]。

> **公式**: `Score(d) = Σ 1 / (k + rank_i(d))`

公式里的关键部分含义如下：
*   **`rank_i(d)`**: 文档`d`在第`i`个检索结果列表中的**排名**[reference:7][reference:8]。如果某个列表里没有这个文档，该项贡献就是`0`[reference:9]。
*   **`k` (平滑常数)**: 一个重要的**调和参数**，通常取值为 **60**[reference:10][reference:11][reference:12]。它起到“平衡器”的作用，避免排名非常靠后的文档贡献值几乎为零，也让排名第一的文档不至于有压倒性优势。

### 💡 RRF算法示例演算

假设我们有两个检索结果列表，需要将它们融合[reference:13]：
*   **列表 A (关键词检索)**: 1. Doc1, 2. Doc2, 3. Doc3
*   **列表 B (向量检索)**: 1. Doc2, 2. Doc4, 3. Doc1
**参数 `k=60`**。

计算每个文档的RRF得分（保留五位小数）：

1.  **Doc1**: 在A中排名第1，在B中排名第3。
    *   得分 = `1/(60+1) + 1/(60+3)` = `1/61 + 1/63` ≈ `0.01639 + 0.01587` = **0.03226**

2.  **Doc2**: 在A中排名第2，在B中排名第1。
    *   得分 = `1/(60+2) + 1/(60+1)` = `1/62 + 1/61` ≈ `0.01613 + 0.01639` = **0.03252**

3.  **Doc3**: 仅在A中排名第3。
    *   得分 = `1/(60+3)` = `1/63` ≈ **0.01587**

4.  **Doc4**: 仅在B中排名第2。
    *   得分 = `1/(60+2)` = `1/62` ≈ **0.01613**

最终，按得分从高到低排序，融合后的新排名为：
**1. Doc2 (0.03252) → 2. Doc1 (0.03226) → 3. Doc4 (0.01613) → 4. Doc3 (0.01587)**
Doc2因其在两个列表中均排名靠前而胜出，这体现了RRF“求共识”的核心思想[reference:14]。

### ⚖️ `k`值的“平衡”艺术

`k`值的选择会直接影响融合结果：
*   **较小的 `k` (如 1~10)**：会**极度放大**排名第一的优势，提升精准度，但风险是容易让某个检索器的“偏见”主导结果[reference:15]。
*   **较大的 `k` (推荐 60)**：会**鼓励共识**，一个文档如果在多个检索器中表现都不错，会比只在某个检索器中排第一的文档得分更高，提升结果的召回率和鲁棒性[reference:16]。

### ✨ RRF在RAG系统中的优势

RRF的优势契合了RAG系统对高质量检索的追求[reference:17][reference:18]：
*   **无需分数归一化**：直接绕过了分数不可比的核心难题。
*   **实现简单且鲁棒**：计算逻辑清晰，不易受单一检索器异常分数的影响。
*   **追求共识更可靠**：融合多路信息，找到各方都认可的文档，综合结果更稳定、可靠。

### ⚙️ RRF的演进与变体

基础的RRF也有一些改进方向：
*   **加权RRF**：允许为不同检索器设置不同的权重。例如，当明确查询需要精确匹配关键词时，可给予BM25检索器更高的权重[reference:19][reference:20]。
*   **处理无结果项**：对于未出现在某个检索列表中的文档，标准做法是贡献为0，这等价于将其排名视为无穷大[reference:21]。

### 💎 总结：为什么RAG需要RRF？

简单来说，RRF通过**“共识”**的力量，解决了多路检索结果“无法比较”的难题，以极低的成本显著提升了RAG系统检索阶段的**准确性和鲁棒性**，从而为后续的答案生成提供了更可靠的事实基础，有效减少“胡说八道”的可能。





在 LangChain 的新版本里，官方的 `EnsembleRetriever` 确实移到了 `langchain-classic` 包中[reference:0]。不过，实现 RRF 算法最简单、最可靠的方式，其实还是直接使用 `langchain-classic` 包。这样做能保证代码的稳定性和未来的兼容性。

## 🛠️ 方案一：使用 langchain-classic（推荐）

这是官方推荐的方式，能直接复用成熟的 `EnsembleRetriever`，同时确保未来升级时的兼容性。

### 安装与导入

```bash
pip install langchain langchain-classic
```

```python
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
```

### 代码实现

```python
# 1. 准备文档
documents = [
    Document(page_content="笨笨是一只很喜欢睡觉的猫咪"),
    Document(page_content="我喜欢在夜晚听音乐，这让我感到放松。"),
    # ... 更多文档
]

# 2. 构建关键词检索器 (BM25)
bm25_retriever = BM25Retriever.from_documents(documents)
bm25_retriever.k = 4

# 3. 构建语义检索器 (FAISS)
embeddings = OpenAIEmbeddings()
faiss_db = FAISS.from_documents(documents, embeddings)
faiss_retriever = faiss_db.as_retriever(search_kwargs={"k": 4})

# 4. 构建集成检索器，使用 RRF 算法融合
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, faiss_retriever],
    weights=[0.5, 0.5],   # 为每个检索器分配权重
    c=60                  # RRF 算法中的平滑常数，默认是 60
)
```

## ⚙️ 方案二：自定义实现 RRF（学习或轻量级场景）

如果确实不想依赖 `langchain-classic`，也可以自己实现 RRF 算法。这种方式更轻量，也方便你理解 RRF 的内部机制。

### 实现思路

```python
from typing import List, Dict, Any
from collections import defaultdict

def reciprocal_rank_fusion(
    results_list: List[List[Document]], 
    weights: List[float] = None, 
    k: int = 60
) -> List[Document]:
    """对多个检索器的结果进行 RRF 融合"""
    # 初始化得分字典和权重
    scores = defaultdict(float)
    if weights is None:
        weights = [1.0] * len(results_list)
    
    # 遍历每个检索器的结果
    for i, results in enumerate(results_list):
        weight = weights[i]
        # 计算每个文档的 RRF 得分
        for rank, doc in enumerate(results, start=1):
            # 使用 page_content 作为唯一标识
            doc_id = doc.page_content
            scores[doc_id] += weight / (k + rank)
    
    # 根据得分排序并返回文档列表
    sorted_doc_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    
    # 恢复完整的 Document 对象（需要维护一个 id -> Document 的映射）
    # 此处为简化代码，建议在实际使用时维护一个映射表
    return [doc for doc_id in sorted_doc_ids for doc in results_list[0] if doc.page_content == doc_id]

# 使用示例
results_1 = bm25_retriever.get_relevant_documents("query")
results_2 = faiss_retriever.get_relevant_documents("query")
fused_results = reciprocal_rank_fusion([results_1, results_2], weights=[0.5, 0.5])
```

### 关键细节：识别唯一文档

RRF 算法需要一个稳定、唯一的标识符来区分文档，并将来自不同检索器的结果正确合并。使用 `page_content` 作为标识符是最简单的方法，但可能会因为重复或相似内容导致误判。更稳妥的做法是提前为每个文档分配一个全局唯一的 `id` 字段。

```python
def get_doc_id(doc: Document) -> str:
    # 优先使用 metadata 中的 id 字段
    if doc.metadata and doc.metadata.get('id'):
        return doc.metadata['id']
    # 回退到 page_content
    return doc.page_content
```

## 💎 总结：两种方案的对比与选择

| 方案                         | 优点                               | 缺点                                 |
| :--------------------------- | :--------------------------------- | :----------------------------------- |
| **使用 `langchain-classic`** | 官方维护，功能完善，代码简洁       | 需要多安装一个包，但这是最稳妥的选择 |
| **自定义实现 RRF**           | 无额外依赖，完全可控，便于理解算法 | 需要自行处理文档去重、权重等细节     |

总的来说，**推荐使用 `langchain-classic`**，因为它能让你在 LangChain 1.0 的新架构下，用最少的代码实现功能，并且能获得官方的长期支持。自定义实现则更适合学习研究，或在极简环境下临时使用。
