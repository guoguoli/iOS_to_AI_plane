"""
对比学习微调

为什么需要微调？
1. 通用模型在特定领域表现不佳
2. 教育科技、医疗健康等专业术语理解不准确
3. 成都本地化内容（方言、地名）需要适配

对比学习（Contrastive Learning）:
- 正样本对: 相似的文本（如"求导"和"求导公式"）
- 负样本对: 不相似的文本（如"求导"和"线性代数"）
- 目标: 拉近正样本距离，推远负样本距离

类比iOS开发:
- 迁移学习: 用通用模型 → 微调适配
- 就像用Core ML预训练模型 → 自定义数据训练
"""

class EmbeddingFineTuner:
    """Embedding微调器（概念实现）"""
    
    @staticmethod
    def prepare_training_data(domain: str = "education"):
        """
        准备训练数据
        
        Args:
            domain: 领域（education/medical/general）
        
        Returns:
            训练数据
        """
        # 模拟教育领域训练数据
        if domain == "education":
            return [
                {
                    "positive_pairs": [
                        ("二次函数求导", "如何求二次函数的导数"),
                        ("导数公式", "f'(x) = 2ax + b"),
                        ("函数的极值", "求函数最大值和最小值")
                    ],
                    "negative_pairs": [
                        ("二次函数求导", "线性代数基础"),
                        ("导数公式", "矩阵乘法"),
                        ("函数的极值", "概率分布")
                    ]
                }
            ]
        elif domain == "medical":
            return {
                "positive_pairs": [
                    ("高血压症状", "血压升高的表现"),
                    ("糖尿病治疗", "如何控制血糖"),
                    ("感冒预防", "如何避免感冒")
                ],
                "negative_pairs": [
                    ("高血压症状", "骨折治疗"),
                    ("糖尿病治疗", "眼科疾病"),
                    ("感冒预防", "皮肤护理")
                ]
            }
    
    @staticmethod
    def fine_tuning_pipeline():
        """
        微调流程
        
        注意: 实际微调需要大量数据和GPU资源
        这里仅展示流程概念
        """
        print("""
Embedding微调流程

1. 数据准备
   └─ 收集领域数据
   └─ 构建正负样本对

2. 模型选择
   ├─ 通用模型: BGE-base-zh / M3E-base
   └─ 本地部署（需要GPU）

3. 对比学习训练
   └─ 加载预训练权重
   └─ 训练对比学习损失函数（InfoNCE Loss）
   └─ 调整学习率和epoch

4. 评估与部署
   ├─ 在测试集上评估
   ├─ 对比通用模型效果
   └─ 部署到生产环境

成本估算（以BGE-base-zh为例）:
- 训练数据: 1万对正负样本
- 训练时间: RTX 3090上约2小时
- 效果提升: 领域内检索准确率提升10-20%

成都教育科技公司建议:
- 初期: 使用通用模型（通义千问/BGE）
- 中期: 如果检索质量不满足，考虑微调
- 微调优先级: 数学 > 物理 > 语文 > 英语
""")
        
"""
稠密向量 vs 稀疏向量

稠密向量（Dense Vector）:
- 来源于: Embedding模型（如text-embedding-v3）
- 特点: 所有维度都有值
- 优势: 语义理解能力强
- 劣势: 对精确匹配不敏感

稀疏向量（Sparse Vector）:
- 来源于: BM25、TF-IDF
- 特点: 大部分维度为0，只有关键词对应的维度有值
- 优势: 精确匹配专业术语
- 劣势: 语义理解能力弱

混合检索:
- 稠密向量 + 稀疏向量
- 互补优势: 语义 + 精确匹配

类比iOS开发:
- 稠密向量 = 全文搜索（语义理解）
- 稀疏向量 = 精确匹配（字段过滤）
- 混合检索 = CoreData + Spotlight搜索
"""

class HybridEmbeddingSearch:
    """混合Embedding搜索（稠密+稀疏）"""
    
    def __init__(self, dense_model):
        """
        初始化
        
        Args:
            dense_model: 稠密向量模型（如通义千问）
        """
        self.dense_model = dense_model
    
    def dense_search(
        self,
        query: str,
        documents: list[str],
        top_k: int = 5
    ) -> list[dict]:
        """
        稠密向量搜索
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回Top-K
        
        Returns:
            搜索结果
        """
        # 获取查询向量
        query_vec = self.dense_model.embed_query(query)
        
        # 获取文档向量
        doc_vectors = self.dense_model.embed_batch(
            documents, text_type="document"
        )
        
        # 计算相似度
        similarities = [
            cosine_similarity(query_vec, doc_vec)
            for doc_vec in doc_vectors
        ]
        
        # 排序
        ranked = sorted(
            zip(documents, similarities),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {"document": doc, "score": score, "type": "dense"}
            for doc, score in ranked[:top_k]
        ]
    
    def sparse_search(
        self,
        query: str,
        documents: list[str],
        top_k: int = 5
    ) -> list[dict]:
        """
        稀疏向量搜索（简化BM25）
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回Top-K
        
        Returns:
            搜索结果
        """
        import jieba
        
        # 简化BM25：关键词匹配计数
        query_words = set(jieba.cut(query))
        
        scores = []
        for doc in documents:
            doc_words = set(jieba.cut(doc))
            
            # 精确匹配计数
            match_count = len(query_words & doc_words)
            score = match_count / len(query_words) if query_words else 0
            
            scores.append(score)
        
        # 排序
        ranked = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {"document": doc, "score": score, "type": "sparse"}
            for doc, score in ranked[:top_k]
        ]
    
    def hybrid_search(
        self,
        query: str,
        documents: list[str],
        top_k: int = 5,
        alpha: float = 0.7
    ) -> list[dict]:
        """
        混合检索（稠密 + 稀疏）
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回Top-K
            alpha: 稠密向量权重（0-1）
        
        Returns:
            混合搜索结果
        """
        # 分别执行两种检索
        dense_results = self.dense_search(query, documents, top_k * 2)
        sparse_results = self.sparse_search(query, documents, top_k * 2)
        
        # 合并分数
        combined_scores = {}
        
        for result in dense_results:
            doc = result["document"]
            combined_scores[doc] = combined_scores.get(doc, 0) + result["score"] * alpha
        
        for result in sparse_results:
            doc = result["document"]
            combined_scores[doc] = combined_scores.get(doc, 0) + result["score"] * (1 - alpha)
        
        # 排序
        ranked = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {
                "document": doc,
                "score": score,
                "type": "hybrid",
                "alpha": alpha
            }
            for doc, score in ranked[:top_k]
        ]

# 使用示例
def hybrid_search_demo():
    """混合检索示例"""
    
    embedder = QwenEmbedding()
    searcher = HybridEmbeddingSearch(embedder)
    
    # 测试数据
    documents = [
        "二次函数f(x) = ax² + bx + c的导数是f'(x) = 2ax + b",
        "函数的导数表示函数在某点的瞬时变化率",
        "线性代数是数学的重要分支，包括矩阵和向量",
        "矩阵的乘法不满足交换律，即AB ≠ BA",
        "微积分是研究函数的极限、导数和积分的学科"
    ]
    
    query = "如何求导"
    
    # 1. 稠密向量搜索
    print("=== 稠密向量搜索 ===")
    dense_results = searcher.dense_search(query, documents)
    for result in dense_results:
        print(f"{result['document'][:50]}... (分数: {result['score']:.4f})")
    
    # 2. 稀疏向量搜索
    print("\n=== 稀疏向量搜索 ===")
    sparse_results = searcher.sparse_search(query, documents)
    for result in sparse_results:
        print(f"{result['document'][:50]}... (分数: {result['score']:.4f})")
    
    # 3. 混合检索
    print("\n=== 混合检索 ===")
    hybrid_results = searcher.hybrid_search(query, documents, alpha=0.7)
    for result in hybrid_results:
        print(f"{result['document'][:50]}... (分数: {result['score']:.4f})")
        
"""
多模态Embedding

CLIP（Contrastive Language-Image Pre-training）
- OpenAI提出
- 将图像和文本映射到同一向量空间
- 实现图文检索

通义千问VL（Vision-Language）Embedding
- 阿里达摩院
- 支持中文图文对齐
- 更适合中国场景

应用场景:
1. 图文检索（用文本搜索图片）
2. 图像描述生成
3. 视觉问答
4. 多模态RAG（文档中包含图片）

类比iOS开发:
- 单模态 = UILabel（文本）
- 多模态 = UIImageView + UILabel（图文结合）
"""

class MultimodalEmbedding:
    """多模态Embedding（概念实现）"""
    
    @staticmethod
    def explain_clip():
        """解释CLIP原理"""
        print("""
CLIP（Contrastive Language-Image Pre-training）原理

核心思想:
- 将图像和文本映射到同一向量空间
- 图像编码器: Vision Transformer (ViT)
- 文本编码器: Transformer（类似BERT）
- 对比学习: 拉近图文对，推远不匹配对

应用示例:
1. 文本搜图
   输入: "一只猫在睡觉"
   输出: 最匹配的图片

2. 图文匹配
   输入: 图片 + 文本
   输出: 是否匹配

3. 零样本分类
   输入: 图片 + 类别列表（"猫", "狗", "鸟"）
   输出: 图片属于哪个类别

成都教育科技应用:
- 教材插图检索: 用题目搜索对应插图
- 手写体识别: 将手写公式转换为图像再识别
- 实验视频标注: 自动生成实验视频的文字描述
""")
    
    @staticmethod
    def multimodal_rag_pipeline():
        """多模态RAG流程"""
        print("""
多模态RAG流程

传统RAG（文本）:
用户问题 → 文本检索 → 文档 → LLM生成

多模态RAG（图文）:
用户问题 → 
  ├─ 文本检索 → 文档片段 → LLM生成
  └─ 图像检索 → 图片/图表 → VLM（视觉语言模型）生成

示例:
用户问题: "二次函数的图像是什么形状？"
├─ 文本检索: "二次函数的图像是抛物线"
└─ 图像检索: 二次函数图像的图片
↓
最终回答: 包含文字说明 + 图片

技术栈推荐:
1. 通义千问text-embedding-v3（文本Embedding）
2. 通义千问VL（多模态理解）
3. Chroma（向量数据库，存储文本和图像向量）
4. qwen-vl-max（视觉语言模型，理解图片）
""")