import numpy as np

def similarity_metrics(a: np.ndarray, b: np.ndarray) -> dict:
    """计算三种相似度指标"""
    
    # 1. 余弦相似度（推荐用于文本语义检索）
    cos_sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    # 2. 欧氏距离（需要归一化才能转为相似度）
    euclidean_dist = np.linalg.norm(a - b)
    
    # 3. 点积/内积
    dot_product = np.dot(a, b)
    
    return {
        "cosine_similarity": float(cos_sim),
        "euclidean_distance": float(euclidean_dist),
        "dot_product": float(dot_product)
    }

# 【重要】什么时候用什么？
# 
# 场景1：文本语义搜索
# → 使用余弦相似度（通义千问embedding已标准化）
#
# 场景2：已标准化的向量（如使用normalize=True）
# → 点积等价于余弦相似度，性能更快
#
# 场景3：图像特征匹配
# → 欧氏距离或余弦相似度都可以

# 通义千问embedding的归一化设置
from dashscope import TextEmbedding

response = TextEmbedding.call(
    model=TextEmbedding.models.text_embedding_v3,
    input="RAG向量检索技术",
    parameters={
        "text_type": "document",  # 文档类型embedding
        # "normalize": True  # 归一化后，点积 = 余弦相似度
    }
)

embedding = response.output['embeddings'][0]['embedding']

# 归一化后的向量
normalized = embedding / np.linalg.norm(embedding)

# 结论：
# - 通义千问默认输出归一化向量
# - 此时点积计算效率更高，效果等同于余弦相似度