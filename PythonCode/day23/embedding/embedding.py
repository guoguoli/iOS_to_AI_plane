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
"""
词嵌入的问题:
- 如何表示一句话或一个段落？
- 简单平均词向量会丢失语法结构和词序信息

Sentence-BERT（SBERT，2019）
- 基于BERT的句嵌入模型
- 使用Siamese Network训练
- 输出: 固定长度的句子向量
- 优势: 保留语义信息，适合语义相似度计算
"""

# 句嵌入 vs 词嵌入
class EmbeddingComparison:
    """句嵌入与词嵌入的对比"""
    
    @staticmethod
    def word_embedding_approach(sentence: str):
        """词嵌入方式: 平均所有词向量"""
        words = sentence.split()  # 简化分词
        word_vectors = [get_word_vector(w) for w in words]
        
        # 简单平均
        sentence_vector = [
            sum(v[i] for v in word_vectors) / len(word_vectors)
            for i in range(len(word_vectors[0]))
        ]
        
        return sentence_vector
    
    @staticmethod
    def sentence_embedding_approach(sentence: str):
        """句嵌入方式: 直接使用SBERT"""
        return get_sentence_vector(sentence)

# 类比iOS中的图层处理
"""
词嵌入平均 = CALayer的简单叠加（没有考虑层级关系）
句嵌入 = 复杂的UIView组合（包含约束、层级、动画）
"""

# 通义千问text-embedding-v3的句嵌入能力
from dashscope import TextEmbedding

def sentence_embedding_example():
    """通义千问句嵌入示例"""
    
    # 两个语义相似但用词不同的句子
    sentence1 = "如何求解二次函数的导数？"
    sentence2 = "二次函数求导的方法有哪些？"
    
    response = TextEmbedding.call(
        model=TextEmbedding.models.text_embedding_v3,
        input=[sentence1, sentence2],
        parameters={"text_type": "query"}  # 查询类型embedding
    )
    
    embeddings = [
        item['embedding'] for item in response.output['embeddings']
    ]
    
    # 计算相似度
    similarity = cosine_similarity(embeddings[0], embeddings[1])
    print(f"语义相似度: {similarity:.4f}")  # 应该 > 0.8
    
    """
文档嵌入的挑战:
- 文档长度可能远超模型的上下文窗口
- 如何保留长文档的全局信息？

解决方案:
1. 分块 + 聚合（Chunking + Aggregation）
2. 层级化Embedding（Hierarchical Embedding）
3. Matryoshka Representation Learning（俄罗斯套娃式表示）
"""

# 文档嵌入实现方案
class DocumentEmbedding:
    """文档嵌入策略"""
    
    @staticmethod
    def chunk_and_average(document: str, chunk_size: int = 500):
        """策略1: 分块 + 平均"""
        
        # 1. 将文档分块
        chunks = [
            document[i:i+chunk_size]
            for i in range(0, len(document), chunk_size)
        ]
        
        # 2. 每个chunk单独embedding
        chunk_embeddings = get_embeddings_batch(chunks)
        
        # 3. 平均所有chunk向量
        doc_embedding = [
            sum(emb[i] for emb in chunk_embeddings) / len(chunk_embeddings)
            for i in range(len(chunk_embeddings[0]))
        ]
        
        return doc_embedding
    
    @staticmethod
    def hierarchical_embedding(document: str):
        """策略2: 层级化Embedding"""
        
        # 层级1: 句子级
        sentences = document.split('。')
        sentence_embeddings = get_embeddings_batch(sentences)
        
        # 层级2: 段落级（句子平均）
        paragraphs = []
        current_para = []
        
        for sent, emb in zip(sentences, sentence_embeddings):
            current_para.append(emb)
            if len(current_para) >= 3:  # 每3句组成一段
                paragraphs.append(current_para)
                current_para = []
        
        # 层级3: 文档级（段落平均）
        doc_embedding = [
            sum(
                sum(emb[i] for emb in para) / len(para)
                for para in paragraphs
            ) / len(paragraphs)
            for i in range(len(paragraphs[0][0]))
        ]
        
        return doc_embedding

# 类比iOS中的复杂视图层级
"""
文档嵌入 ≈ 复杂的UI层级结构
句子 = UITableViewCell
段落 = UITableView Section
文档 = UIViewController

每个层级都有自己的embedding表示
"""