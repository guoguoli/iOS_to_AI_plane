# 安装Chroma
# pip install chromadb

import chromadb
from chromadb.config import Settings
import os

# 2.1.1 初始化Chroma客户端

# 方式1：持久化存储（推荐）
chroma_client = chromadb.PersistentClient(
    path="./chroma_db"  # 本地存储路径
)

# 方式2：内存模式（仅用于测试，数据不持久化）
chroma_client = chromadb.Client(
    Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="./chroma_db"
    )
)

# 方式3：客户端-服务器模式
# chroma_client = chromadb.HttpClient(host='localhost', port=8000)

# 2.2.1 创建集合
collection = chroma_client.create_collection(
    name="education_knowledge_base",  # 集合名称（唯一）
    metadata={
        "description": "教育知识库集合",
        "hnsw:space": "cosine",  # 距离度量：cosine/l2/ip（内积）
        "hnsw:M": 16,             # HNSW参数
        "hnsw:ef_construction": 200
    }
)

# 2.2.2 获取已有集合
collection = chroma_client.get_collection(name="education_knowledge_base")

# 2.2.3 检查集合是否存在
exists = chroma_client.collection_exists(name="education_knowledge_base")

# 2.2.4 删除集合
chroma_client.delete_collection(name="education_knowledge_base")

# 2.2.5 列出所有集合
all_collections = chroma_client.list_collections()
for col in all_collections:
    print(f"集合: {col.name}, 数据量: {col.count()}")
    
# 2.3.1 添加文档（Add）

# 单个文档
collection.add(
    documents=["二次函数的求导公式是 f'(x) = 2ax + b"],
    metadatas=[{"subject": "数学", "topic": "导数", "difficulty": "基础"}],
    ids=["doc_001"]
)

# 批量添加
batch_data = {
    "ids": [f"doc_{i:03d}" for i in range(1, 101)],
    "documents": [
        "牛顿第二定律：F = ma",
        "欧姆定律：V = IR",
        "光的折射定律：n1·sinθ1 = n2·sinθ2",
        # ... 更多文档
    ],
    "metadatas": [
        {"subject": "物理", "topic": "力学", "difficulty": "中等"},
        {"subject": "物理", "topic": "电学", "difficulty": "基础"},
        {"subject": "物理", "topic": "光学", "difficulty": "中等"},
        # ... 更多元数据
    ],
    "embeddings": None  # Chroma会自动调用embedding模型
}

collection.add(**batch_data)

# 2.3.2 查询文档（Query）
results = collection.query(
    query_texts=["求导的基本法则有哪些？"],  # 查询文本
    n_results=5,  # 返回前5个最相似结果
    where={"difficulty": "中等"},  # 元数据过滤条件
    where_document={"$contains": "导数"}  # 文档内容过滤
)

# 查询结果解析
print(f"文档ID: {results['ids'][0]}")
print(f"距离: {results['distances'][0]}")
print(f"内容: {results['documents'][0]}")
print(f"元数据: {results['metadatas'][0]}")

# 2.3.3 更新文档（Update）
collection.update(
    ids=["doc_001"],
    documents=["更新后的内容：二次函数求导公式"],
    metadatas=[{"subject": "数学", "topic": "导数", "difficulty": "基础"}]
)

# 2.3.4 删除文档（Delete）
collection.delete(ids=["doc_001"])  # 删除指定ID
collection.delete(where={"subject": "物理"})  # 按条件删除

# 2.3.5 获取集合统计
count = collection.count()
print(f"集合中共有 {count} 条文档")

# Chroma 支持的过滤操作符

# 2.4.1 基础比较
collection.query(
    query_texts=["..."],
    where={
        "difficulty": "中等",           # 等于
        "rating": {"$gte": 4.5},        # 大于等于
        "view_count": {"$lt": 1000},    # 小于
    }
)

# 2.4.2 逻辑运算
collection.query(
    query_texts=["..."],
    where={
        "$and": [
            {"subject": "数学"},
            {"difficulty": {"$in": ["基础", "中等"]}}  # IN操作
        ]
    }
)

# 2.4.3 文档内容过滤
collection.query(
    query_texts=["..."],
    where_document={
        "$contains": "函数"  # 包含关键词
    }
)
import dashscope
from dashscope import TextEmbedding
from chromadb.api.models.Collection import Collection

# 配置API Key（建议使用环境变量）
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

def qwen_embed_function(texts: list[str]) -> list[list[float]]:
    """
    通义千问embedding函数
    用于Chroma的embedding parameter
    """
    response = TextEmbedding.call(
        model=TextEmbedding.models.text_embedding_v3,
        input=texts
    )
    
    if response.status_code != 200:
        raise ValueError(f"Embedding调用失败: {response.message}")
    
    embeddings = [
        item['embedding'] for item in response.output['embeddings']
    ]
    return embeddings

# 创建集合时指定embedding函数
collection = chroma_client.create_collection(
    name="knowledge_base",
    embedding_function=qwen_embed_function  # 自定义embedding函数
)

# 添加文档（使用自定义embedding）
collection.add(
    documents=["RAG系统主要由检索和生成两部分组成"],
    ids=["doc_001"]
)

# 查询时也会自动使用自定义embedding
results = collection.query(
    query_texts=["什么是RAG系统？"],
    n_results=3
)
# 2.6.1 批量操作优化
def batch_import_documents(
    collection: Collection,
    documents: list[str],
    metadatas: list[dict],
    batch_size: int = 100
):
    """批量导入文档（分批处理）"""
    
    total = len(documents)
    for i in range(0, total, batch_size):
        batch_docs = documents[i:i + batch_size]
        batch_meta = metadatas[i:i + batch_size]
        batch_ids = [f"doc_{i + j}" for j in range(len(batch_docs))]
        
        collection.add(
            documents=batch_docs,
            metadatas=batch_meta,
            ids=batch_ids
        )
        
        print(f"进度: {min(i + batch_size, total)}/{total}")

# 2.6.2 HNSW参数优化
def create_optimized_collection(
    client,
    name: str,
    data_scale: int = 10000
):
    """根据数据规模创建优化后的集合"""
    
    # 根据数据规模调整HNSW参数
    if data_scale < 1000:
        hnsw_config = {"M": 16, "efConstruction": 100}
    elif data_scale < 100000:
        hnsw_config = {"M": 32, "efConstruction": 200}
    else:
        hnsw_config = {"M": 48, "efConstruction": 400}
    
    return client.create_collection(
        name=name,
        metadata={
            "hnsw:space": "cosine",
            **hnsw_config
        }
    )

# 2.6.3 异步写入（生产环境）
import asyncio
from concurrent.futures import ThreadPoolExecutor

def parallel_embedding(texts: list[str], workers: int = 4) -> list:
    """并行获取embedding"""
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(qwen_embed_function, [text])
            for text in texts
        ]
        results = [f.result()[0] for f in futures]
    return results
"""
关键指标定义

1. 召回率（Recall@K）
   - 正确结果中被检索到的比例
   - Recall@K = |Relevant ∩ Retrieved@K| / |Relevant|
   
2. 精确率（Precision@K）
   - 检索结果中正确的比例
   - Precision@K = |Relevant ∩ Retrieved@K| / K
   
3. MRR（Mean Reciprocal Rank）
   - 第一个正确答案排名的倒数平均值
   - MRR = (1/N) × Σ(1/rank_i)
   
4. NDCG（Normalized Discounted Cumulative Gain）
   - 考虑排名位置的打分指标
   - NDCG = DCG / IDCG

【重点】RAG场景推荐指标组合：
- 离线评估：Recall@10 + MRR
- 在线评估：用户满意度 + 答案准确率
"""

def evaluate_retrieval(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int = 10
) -> dict:
    """计算检索评估指标"""
    
    retrieved_at_k = set(retrieved_ids[:k])
    
    # 召回率
    recall = len(retrieved_at_k & relevant_ids) / len(relevant_ids)
    
    # 精确率
    precision = len(retrieved_at_k & relevant_ids) / k
    
    # MRR
    mrr = 0
    for i, doc_id in enumerate(retrieved_ids[:k]):
        if doc_id in relevant_ids:
            mrr = 1 / (i + 1)
            break
    
    return {
        "recall": recall,
        "precision": precision,
        "mrr": mrr
    }

# 多阶段检索实现
class MultiStageRetrieval:
    """多阶段检索器"""
    
    def __init__(self, vector_store):
        self.vector_store = vector_store
    
    def coarse_retrieval(self, query: str, top_k: int = 100) -> list[dict]:
        """第一阶段：粗检索，快速召回候选"""
        
        results = self.vector_store.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        return self._format_results(results)
    
    def rerank(self, query: str, candidates: list[dict], top_k: int = 10) -> list[dict]:
        """第二阶段：重排序，使用交叉编码器精排"""
        
        # 方法1：基于相似度分数重排
        scored = []
        for item in candidates:
            score = item.get('score', 0)
            # 加入其他特征（BM25分数、关键词匹配等）
            bonus = self._keyword_bonus(query, item['document'])
            scored.append({**item, 'final_score': score + bonus})
        
        # 按最终分数排序
        scored.sort(key=lambda x: x['final_score'], reverse=True)
        
        return scored[:top_k]
    
    def retrieve(self, query: str, final_k: int = 5) -> list[dict]:
        """完整的多阶段检索流程"""
        
        # 阶段1：粗检索
        candidates = self.coarse_retrieval(query, top_k=100)
        
        # 阶段2：重排序
        results = self.rerank(query, candidates, top_k=final_k)
        
        return results