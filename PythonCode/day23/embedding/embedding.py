# Day22 核心概念回顾
"""
1. 向量数据库的作用
   - 存储高维向量（由Embedding模型生成）
   - 支持近似最近邻（ANN）检索
   - 提供元数据过滤能力

2. 主流向量数据库
   - Chroma: 轻量级、Python优先（推荐学习）
   - Pinecone: 云服务、免运维
   - Milvus: 分布式、高性能

3. 检索策略
   - 多阶段检索: 粗检索 → 精检索 → 重排序
   - 混合检索: BM25关键词 + 向量语义
   - 查询改写: Multi-Query、HyDE、Sub-Query

4. 相似度计算
   - 余弦相似度: 文本语义检索首选
   - 欧氏距离: 图像特征匹配
   - 点积: 已标准化向量（性能更优）
"""

# Day22 已掌握的向量检索基础
from dashscope import TextEmbedding

def simple_embedding_and_search(query: str, documents: list[str]) -> str:
    """Day22 简单的向量检索示例"""
    
    # 1. 获取查询向量
    query_response = TextEmbedding.call(
        model=TextEmbedding.models.text_embedding_v3,
        input=query
    )
    query_vec = query_response.output['embeddings'][0]['embedding']
    
    # 2. 计算所有文档向量
    doc_response = TextEmbedding.call(
        model=TextEmbedding.models.text_embedding_v3,
        input=documents
    )
    doc_vectors = [item['embedding'] for item in doc_response.output['embeddings']]
    
    # 3. 余弦相似度计算（Day22已掌握）
    best_idx = 0
    best_score = -1
    
    for idx, doc_vec in enumerate(doc_vectors):
        score = sum(q * d for q, d in zip(query_vec, doc_vec))
        score /= (sum(q*q for q in query_vec)**0.5 * sum(d*d for d in doc_vec)** 0.5)
        
        if score > best_score:
            best_score = score
            best_idx = idx
    
    return documents[best_idx]

# Day23 要深化什么？
"""
Day22: 关注"如何用向量数据库存储和检索"
Day23: 关注"如何生成高质量的向量"（Embedding本身）

就像iOS开发：
- Day22 = 如何存储和查询CoreData中的数据
- Day23 = 如何设计和构建数据模型
"""