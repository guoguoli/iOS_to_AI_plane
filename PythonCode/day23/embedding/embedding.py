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

"""
RAG为什么需要Embedding？

问题: 如何让机器理解"相似"的概念？
- "函数求导" 和 "导数计算" 是否相似？
- "苹果"（水果）和 "苹果"（公司）是否相似？

答案: 将文本映射到向量空间
- 语义相似的文本 → 空间中距离近的点
- 语义不同的文本 → 空间中距离远的点
"""

# 向量空间的几何直觉
class VectorSpaceVisualization:
    """向量空间的几何理解"""
    
    @staticmethod
    def explain_vector_space():
        """用iOS开发类比解释向量空间"""
        
        print("""
向量空间就像iOS中的坐标系系统：

1. 二维向量空间 (2D)
   - 就像UIView的frame (x, y)
   - 例子: (0.3, 0.7) 表示某个位置

2. 高维向量空间（1536维，通义千问）
   - 每一维代表一种"语义特征"
   - 维度0: 数学相关度
   - 维度1: 难度水平
   - 维度2: 教学年级
   - 维度3: ... (1536个特征)

3. 语义相似度 = 向量夹角
   - 余弦相似度: cos(θ)
   - θ越小，相似度越高
   - θ=0度: 完全相同（相似度=1）
   - θ=90度: 完全不相关（相似度=0）

类比iOS Core Graphics:
- CGAffineTransform: 旋转、缩放、平移
- 在向量空间中: 向量运算可以"旋转"语义
  "苹果" + "科技" - "水果" ≈ "iPhone"
        """)

# RAG中Embedding的作用
def rag_embedding_pipeline():
    """RAG管道中Embedding的位置"""
    
    print("""
完整RAG流程:
┌─────────────────────────────────────────────────────────┐
│ 1. 文档处理                                              │
│    文档 → 分块(Chunking) → [文本1, 文本2, 文本3, ...]    │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────┐
│ 2. 向量化 ← Day23重点                                    │
│    文本1 → Embedding模型 → [0.12, 0.34, ..., 0.78]      │
│    文本2 → Embedding模型 → [0.09, 0.41, ..., 0.65]      │
│    文本3 → Embedding模型 → [0.21, 0.28, ..., 0.82]      │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────┐
│ 3. 向量存储 ← Day22重点                                  │
│    存储到向量数据库（Chroma/Pinecone等）                 │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────┐
│ 4. 查询处理                                              │
│    用户查询 → Embedding模型 → 查询向量                  │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────┐
│ 5. 相似度检索 ← Day22重点                                │
│    查询向量 vs 文档向量 → 找到最相似的K个                │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────┐
│ 6. 上下文生成                                            │
│    检索结果 + 原始问题 → LLM生成答案                    │
└─────────────────────────────────────────────────────────┘

Day23重点关注第2步：向量化
""")
"""
Embedding模型选型决策矩阵
"""

class EmbeddingModelComparison:
    """Embedding模型对比"""
    
    MODELS = {
        "通义千问-text-embedding-v3": {
            "维度": 1536,
            "部署方式": "云端API",
            "成本": "按量付费",
            "中文能力": "★★★★★",
            "性能": "★★★★★",
            "速度": "★★★★☆",
            "离线支持": "否",
            "适用规模": "中小规模",
            "成都教育科技": "推荐（初期）"
        },
        "BGE-large-zh": {
            "维度": 1024,
            "部署方式": "本地部署",
            "成本": "免费（需GPU）",
            "中文能力": "★★★★☆",
            "性能": "★★★★☆",
            "速度": "★★★☆☆",
            "离线支持": "是",
            "适用规模": "超大规模",
            "成都教育科技": "生产环境（大数据量）"
        },
        "M3E-large": {
            "维度": 1024,
            "部署方式": "本地部署",
            "成本": "免费（需GPU）",
            "中文能力": "★★★★☆",
            "性能": "★★★★☆",
            "速度": "★★★☆☆",
            "离线支持": "是",
            "适用规模": "中英混合",
            "成都教育科技": "中英双语场景"
        }
    }
    
    @classmethod
    def select_model(
        cls,
        has_gpu: bool = False,
        is_offline: bool = False,
        data_scale: str = "小",
        budget: str = "有限"
    ) -> str:
        """
        根据场景推荐模型
        
        Args:
            has_gpu: 是否有GPU资源
            is_offline: 是否需要离线部署
            data_scale: 数据规模（小/中/大）
            budget: 预算情况（有限/充足）
        
        Returns:
            推荐的模型名称
        """
        # 决策逻辑
        if is_offline and has_gpu:
            if data_scale in ["大", "中"]:
                return "BGE-large-zh"
            else:
                return "M3E-large"
        elif not has_gpu:
            # 无GPU，只能用云端API
            return "通义千问-text-embedding-v3"
        else:
            # 默认推荐
            return "通义千问-text-embedding-v3"
    
    @classmethod
    def print_comparison(cls):
        """打印模型对比表"""
        print("""
┌──────────────────┬──────┬────────┬──────┬──────┬──────┬────────┐
│ 模型             │ 维度 │ 部署   │ 成本 │ 离线 │ 性能 │ 适用   │
├──────────────────┼──────┼────────┼──────┼──────┼──────┼────────┤
│ 通义千问v3       │ 1536 │ 云端   │ 付费 │ 否   │ ★★★★│ 中小   │
│ BGE-large-zh     │ 1024 │ 本地   │ 免费 │ 是   │ ★★★★│ 大规模 │
│ M3E-large        │ 1024 │ 本地   │ 免费 │ 是   │ ★★★★│ 中英   │
└──────────────────┴──────┴────────┴──────┴──────┴──────┴────────┘

成都教育科技公司选型建议:
1. 初创期/验证阶段 → 通义千问v3（快速开发，按量付费）
2. 成长期/数据量增长 → 通义千问v3（成本仍可控）
3. 成熟期/数据量大+隐私要求 → BGE-large-zh（本地部署）
4. 中英双语产品 → M3E-large（多语言支持）
""")