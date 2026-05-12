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
# 新版 chromadb 的写法，旧版的 Settings(chroma_db_impl=...) 已废弃
chroma_client = chromadb.EphemeralClient()

# 方式3：客户端-服务器模式
# chroma_client = chromadb.HttpClient(host='localhost', port=8000)

# 2.2.1 创建集合
# 注意：新版 chromadb 中 hnsw:M / hnsw:ef_construction 不能放 metadata，
# 只支持 hnsw:space 等少量配置在 metadata 里
collection = chroma_client.create_collection(
    name="education_knowledge_base",  # 集合名称（唯一）
    metadata={
        "description": "教育知识库集合",
        "hnsw:space": "cosine",  # 距离度量：cosine/l2/ip（内积）
    }
)
print("✅ 创建集合成功")

# 2.2.2 获取已有集合
collection = chroma_client.get_collection(name="education_knowledge_base")

# 2.2.3 检查集合是否存在（新版API：用 list_collections 判断）
existing_names = [c.name for c in chroma_client.list_collections()]
exists = "education_knowledge_base" in existing_names
print(f"✅ 集合是否存在: {exists}")

# 2.2.5 列出所有集合
all_collections = chroma_client.list_collections()
for col in all_collections:
    print(f"集合: {col.name}, 数据量: {col.count()}")
    
# 2.3.1 添加文档（Add）
# 注意：不指定 embedding_function 时，Chroma 默认会下载 all-MiniLM-L6-v2 模型（需联网）
# 为了演示，这里直接传入预先生成的 embeddings（维度1536 模拟 dashscope text-embedding-v3）
import random
random.seed(42)

def mock_embedding(dim: int = 1536) -> list[float]:
    """生成随机单位向量（仅演示用，生产环境请替换为真实 embedding）"""
    vec = [random.gauss(0, 1) for _ in range(dim)]
    norm = sum(x**2 for x in vec) ** 0.5
    return [x / norm for x in vec]

# 单个文档
collection.add(
    documents=["二次函数的求导公式是 f'(x) = 2ax + b"],
    embeddings=[mock_embedding()],
    metadatas=[{"subject": "数学", "topic": "导数", "difficulty": "基础"}],
    ids=["doc_001"]
)
print("✅ 单条文档添加成功")

# 批量添加（文档、元数据、ids 数量必须一致）
batch_data = {
    "ids": ["doc_101", "doc_102", "doc_103"],
    "documents": [
        "牛顿第二定律：F = ma",
        "欧姆定律：V = IR",
        "光的折射定律：n1·sinθ1 = n2·sinθ2",
    ],
    "embeddings": [mock_embedding(), mock_embedding(), mock_embedding()],
    "metadatas": [
        {"subject": "物理", "topic": "力学", "difficulty": "中等"},
        {"subject": "物理", "topic": "电学", "difficulty": "基础"},
        {"subject": "物理", "topic": "光学", "difficulty": "中等"},
    ],
}

collection.add(**batch_data)
print("✅ 批量文档添加成功")

# 2.3.2 查询文档（Query）
# 传 query_embeddings 代替 query_texts，绕过自动 embedding 下载
results = collection.query(
    query_embeddings=[mock_embedding()],  # 生产环境用 DashScope embedding
    n_results=2,  # 返回前2个最相似结果
    where={"subject": "数学"},  # 元数据过滤条件
)

# 查询结果解析
print(f"\n🔍 查询结果：")
print(f"文档ID: {results['ids'][0]}")
print(f"距离: {results['distances'][0]}")
print(f"内容: {results['documents'][0]}")
print(f"元数据: {results['metadatas'][0]}")

# 2.3.3 更新文档（Update）
collection.update(
    ids=["doc_001"],
    documents=["更新后的内容：二次函数求导公式 f'(x) = 2ax + b"],
    embeddings=[mock_embedding()],
    metadatas=[{"subject": "数学", "topic": "导数", "difficulty": "基础"}]
)
print("\n✅ 文档更新成功")

# 2.3.5 获取集合统计
count = collection.count()
print(f"集合中共有 {count} 条文档")

# Chroma 支持的过滤操作符

# 2.4.1 基础比较
results2 = collection.query(
    query_embeddings=[mock_embedding()],
    n_results=2,
    where={
        "subject": "物理",           # 等于
    }
)
print(f"\n🔍 过滤查询结果(物理): {results2['documents'][0]}")

# 2.4.2 逻辑运算
results3 = collection.query(
    query_embeddings=[mock_embedding()],
    n_results=3,
    where={
        "$and": [
            {"subject": "物理"},
            {"difficulty": {"$in": ["基础", "中等"]}}  # IN操作
        ]
    }
)
print(f"🔍 逻辑运算查询结果: {results3['documents'][0]}")

# 2.3.4 删除文档（Delete）
collection.delete(ids=["doc_001"])  # 删除指定ID
print(f"\n✅ 删除doc_001后，集合共有 {collection.count()} 条文档")

# 2.2.4 删除集合（放在最后演示）
chroma_client.delete_collection(name="education_knowledge_base")
print("✅ 集合已删除")

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
# 生产环境：embedding_function=qwen_embed_function
# 演示环境：不传 embedding_function，手动传 embeddings
collection = chroma_client.create_collection(
    name="knowledge_base",
)

# 添加文档（演示用 mock embedding，生产环境由 qwen_embed_function 自动生成）
collection.add(
    documents=["RAG系统主要由检索和生成两部分组成"],
    embeddings=[mock_embedding()],
    ids=["doc_001"]
)
print("✅ knowledge_base 文档添加成功")

# 查询时传 query_embeddings（生产环境可改回 query_texts + 自定义 embedding_function）
results = collection.query(
    query_embeddings=[mock_embedding()],
    n_results=1
)
print(f"✅ knowledge_base 查询结果: {results['documents'][0]}")
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
    
"""
查询改写三大策略：
1. Multi-Query：生成多个相似问题 → 扩大检索角度
2. HyDE：先生成假答案 → 用答案去检索（更准）
3. Sub-Query：拆分子问题 → 复杂问题拆解检索
"""

# ======================
# 1. Multi-Query（你原来的，我保留）
# ======================
MULTI_QUERY_PROMPT = """请将这个问题改写成3个不同的表述方式，
保持原意但使用不同的词汇和句式，以便从多个角度检索相关信息。

原问题：{query}

改写后的3个问题（每行一个）："""

def generate_multi_queries(query: str, llm_api) -> list[str]:
    prompt = MULTI_QUERY_PROMPT.format(query=query)
    response = llm_api.call(prompt)
    queries = [q.strip() for q in response.split('\n') if q.strip()]
    return queries[:3]

# ======================
# 2. HyDE 核心代码（新增）
# ======================
HYDE_PROMPT = """请根据问题，直接生成一段简短、专业、准确的回答，
不要多余解释，我要用这段文字去检索知识库。

问题：{query}

回答："""

def generate_hyde_document(query: str, llm_api) -> str:
    """HyDE：生成假设性答案"""
    prompt = HYDE_PROMPT.format(query=query)
    answer = llm_api.call(prompt).strip()
    return answer

# ======================
# 3. Sub-Query 核心代码（新增）
# ======================
SUB_QUERY_PROMPT = """请将复杂问题拆解成 2～4 个简单、独立、可直接检索的小问题。

复杂问题：{query}

拆解后的子问题（每行一个）："""

def generate_sub_queries(query: str, llm_api) -> list[str]:
    """拆分成多个子问题"""
    prompt = SUB_QUERY_PROMPT.format(query=query)
    response = llm_api.call(prompt)
    sub_queries = [q.strip() for q in response.split('\n') if q.strip()]
    return sub_queries

# ======================
# 三大检索函数（完整）
# ======================

def multi_query_retrieval(query: str, collection, llm_api) -> list[dict]:
    """多查询检索：扩大角度"""
    queries = generate_multi_queries(query, llm_api)
    queries.append(query)
    all_results = []
    for q in queries:
        res = collection.query(query_texts=[q], n_results=10)
        all_results.extend(res["documents"][0])
    return list(set(all_results))

def hyde_retrieval(query: str, collection, llm_api) -> list[dict]:
    """HyDE 检索：用生成的假答案去搜，精度极高"""
    fake_answer = generate_hyde_document(query, llm_api)
    res = collection.query(query_texts=[fake_answer], n_results=15)
    return res["documents"][0]

def sub_query_retrieval(query: str, collection, llm_api) -> list[dict]:
    """子问题检索：拆解复杂问题"""
    sub_queries = generate_sub_queries(query, llm_api)
    all_results = []
    for q in sub_queries:
        res = collection.query(query_texts=[q], n_results=8)
        all_results.extend(res["documents"][0])
    return list(set(all_results))


"""
混合检索 = 关键词检索 + 向量检索

优势：
- 关键词检索：精准匹配专业术语（如数学公式）
- 向量检索：理解语义相似性
- 结合两者：兼顾精确性和语义理解

RRF（倒数秩融合）算法：
score_doc = Σ(1/(k + rank_i)) for i in queries
k 通常取60
"""

from collections import defaultdict

def reciprocal_rank_fusion(
    result_lists: list[list[tuple]],
    k: int = 60
) -> list[tuple]:
    """
    倒数秩融合算法
    
    Args:
        result_lists: 多个检索结果列表，每个列表是 (doc_id, score) 的元组
        k: 融合参数，通常60
    
    Returns:
        按RRF分数排序的文档列表
    """
    
    doc_scores = defaultdict(float)
    
    for result_list in result_lists:
        for rank, (doc_id, _) in enumerate(result_list):
            # RRF公式: 1 / (k + rank)
            doc_scores[doc_id] += 1 / (k + rank)
    
    # 按RRF分数排序
    sorted_docs = sorted(
        doc_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return sorted_docs

# BM25 + 向量检索的混合实现
class HybridSearch:
    """混合搜索器"""
    
    def __init__(self, collection, vector_store):
        self.collection = collection
        self.vector_store = vector_store
    
    def keyword_search(self, query: str, top_k: int = 20) -> list[tuple]:
        """BM25关键词检索（Chroma内置支持）"""
        
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where_document={"$contains": query.split()[0]}  # 简单关键词过滤
        )
        
        return list(zip(
            results['ids'][0],
            [1 / (i + 1) for i in range(len(results['ids'][0]))]  # 简化的排名分数
        ))
    
    def vector_search(self, query: str, top_k: int = 20) -> list[tuple]:
        """向量检索"""
        
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # 转换为 (id, distance) 格式
        return list(zip(
            results['ids'][0],
            results['distances'][0]
        ))
    
    def hybrid_search(self, query: str, top_k: int = 10) -> list[dict]:
        """混合检索主流程"""
        
        # 1. 分别执行两种检索
        keyword_results = self.keyword_search(query, top_k=30)
        vector_results = self.vector_search(query, top_k=30)
        
        # 2. RRF融合
        fused = reciprocal_rank_fusion([keyword_results, vector_results])
        
        # 3. 返回最终结果
        final_results = []
        for doc_id, rrf_score in fused[:top_k]:
            # 获取文档详情
            doc = self.collection.get(ids=[doc_id])
            final_results.append({
                'id': doc_id,
                'document': doc['documents'][0],
                'metadata': doc['metadatas'][0],
                'rrf_score': rrf_score
            })
        
        return final_results
    
"""
元数据过滤实战场景

场景1：教育题库 - 按难度筛选
场景2：医疗知识库 - 按科室筛选
场景3：产品库 - 按品牌/价格区间筛选
"""

# 教育题库元数据设计
question_metadata = {
    "subject": "数学",           # 学科
    "grade": "高二",             # 年级
    "topic": "导数",             # 知识点
    "difficulty": "中等",        # 难度
    "question_type": "解答题",   # 题型
    "usage_count": 1523,         # 使用次数（用于热门推荐）
    "last_updated": "2024-01-15" # 更新时间
}

"""
上下文窗口管理的重要性

通义千问上下文限制：
- qwen-turbo: 8K tokens
- qwen-plus: 32K tokens
- qwen-max: 8K tokens

如果检索结果超过限制，需要：
1. 按相似度分数截断
2. 智能压缩上下文
3. 摘要式抽取关键信息
"""

class ContextManager:
    """上下文管理器"""
    
    def __init__(self, max_tokens: int = 6000):
        self.max_tokens = max_tokens
    
    def estimate_tokens(self, text: str) -> int:
        """估算token数量（中文约1.5字符≈1 token）"""
        return len(text) // 2
    
    def truncate_by_score(
        self,
        results: list[dict],
        max_tokens: int = None
    ) -> list[dict]:
        """按分数和长度截断"""
        
        max_tokens = max_tokens or self.max_tokens
        current_tokens = 0
        selected = []
        
        for item in results:
            tokens = self.estimate_tokens(item['document'])
            if current_tokens + tokens <= max_tokens:
                selected.append(item)
                current_tokens += tokens
        
        return selected
    
    def compress_context(
        self,
        documents: list[str],
        max_docs: int = 5
    ) -> str:
        """压缩上下文：取最相关的文档"""
        
        # 限制文档数量
        selected = documents[:max_docs]
        
        return "\n\n".join([
            f"【文档{i+1}】{doc}"
            for i, doc in enumerate(selected)
        ])

"""
重排序策略

1. 基于相似度分数简单排序
2. 基于多样性的排序（避免内容重复）
3. 基于业务规则的排序（如热门优先）
4. 基于学习排序模型（如BGE-Reranker）
"""

class Reranker:
    """检索结果重排序"""
    
    def __init__(self, llm_api):
        self.llm_api = llm_api
    
    def rerank_by_diversity(
        self,
        results: list[dict],
        max_similar: float = 0.9
    ) -> list[dict]:
        """基于多样性重排：降低相似文档的排名"""
        
        reranked = []
        used_topics = set()
        
        for item in results:
            topic = item.get('metadata', {}).get('topic', '')
            
            # 如果主题重复，降低优先级
            if topic in used_topics:
                item['adjusted_score'] = item.get('score', 0) * 0.8
            else:
                item['adjusted_score'] = item.get('score', 0)
                used_topics.add(topic)
            
            reranked.append(item)
        
        return sorted(reranked, key=lambda x: x['adjusted_score'], reverse=True)
    
    def rerank_by_business_rules(
        self,
        results: list[dict],
        rules: list[dict]
    ) -> list[dict]:
        """基于业务规则重排"""
        
        for item in results:
            score = item.get('score', 0)
            metadata = item.get('metadata', {})
            
            # 规则1：热门内容加权
            if metadata.get('usage_count', 0) > 1000:
                score *= 1.1
            
            # 规则2：新内容加权
            # if metadata.get('is_new', False):
            #     score *= 1.2
            
            # 规则3：名师内容加权
            if metadata.get('is_premium', False):
                score *= 1.15
            
            item['final_score'] = score
        
        return sorted(results, key=lambda x: x['final_score'], reverse=True)