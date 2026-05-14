"""
文本预处理的重要性

为什么需要预处理？
1. 去除噪声（特殊字符、HTML标签）
2. 规范化文本（繁简转换、大小写统一）
3. 分句处理（长文本分块）
4. 保留关键信息（不丢失语义）

类比iOS开发:
- 原始数据 → 数据清洗 → 模型训练
- 就像用户输入 → 表单验证 → 保存到数据库
"""

import re
import unicodedata
from typing import list

class TextPreprocessor:
    """文本预处理器"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        清洗文本
        
        Args:
            text: 原始文本
        
        Returns:
            清洗后的文本
        """
        # 1. 去除HTML标签
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 2. 去除特殊字符（保留中文、英文、数字、标点）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s，。！？、；：""''（）《》【】]', ' ', text)
        
        # 3. 去除多余空格
        text = re.sub(r'\s+', ' ', text)
        
        # 4. 去除首尾空格
        text = text.strip()
        
        return text
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        规范化文本
        
        Args:
            text: 原始文本
        
        Returns:
            规范化后的文本
        """
        # 1. Unicode规范化
        text = unicodedata.normalize('NFKC', text)
        
        # 2. 全角转半角
        text = text.replace('（', '(').replace('）', ')')
        text = text.replace('，', ',').replace('。', '.')
        text = text.replace('：', ':').replace('；', ';')
        
        # 3. 英文转小写
        text = text.lower()
        
        return text
    
    @staticmethod
    def split_sentences(text: str) -> list[str]:
        """
        分句
        
        Args:
            text: 输入文本
        
        Returns:
            句子列表
        """
        # 中文分句标点
        delimiters = ['。', '！', '？', '；', '！\n', '？\n', '。\n']
        
        sentences = [text]
        for delimiter in delimiters:
            new_sentences = []
            for sent in sentences:
                new_sentences.extend(sent.split(delimiter))
            sentences = new_sentences
        
        # 过滤空句
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> list[str]:
        """
        文本分块
        
        Args:
            text: 输入文本
            chunk_size: 每块最大字符数
            overlap: 块间重叠字符数
        
        Returns:
            文本块列表
        """
        chunks = []
        
        start = 0
        while start < len(text):
            end = start + chunk_size
            
            # 如果不等于总长度，尝试在句号处分块
            if end < len(text):
                last_period = text.rfind('。', start, end)
                if last_period > start + chunk_size * 0.5:
                    end = last_period + 1
            
            chunks.append(text[start:end].strip())
            start = end - overlap
        
        return chunks
    
    @staticmethod
    def preprocess_pipeline(
        text: str,
        clean: bool = True,
        normalize: bool = True,
        chunk: bool = False,
        chunk_size: int = 500
    ) -> list[str] | str:
        """
        完整的预处理管道
        
        Args:
            text: 原始文本
            clean: 是否清洗
            normalize: 是否规范化
            chunk: 是否分块
            chunk_size: 分块大小
        
        Returns:
            处理后的文本或文本块列表
        """
        if clean:
            text = TextPreprocessor.clean_text(text)
        
        if normalize:
            text = TextPreprocessor.normalize_text(text)
        
        if chunk:
            return TextPreprocessor.chunk_text(text, chunk_size)
        
        return text

# 使用示例
def preprocessing_demo():
    """文本预处理示例"""
    
    # 原始文本（模拟从网页抓取）
    raw_text = """
    <p>二次函数求导是微积分的基础知识点。</p>
    <p>对于函数 f(x) = ax² + bx + c，其导数为 f'(x) = 2ax + b。</p>
    <p>这个公式在高考数学中经常出现！</p>
    """
    
    preprocessor = TextPreprocessor()
    
    # 1. 清洗
    cleaned = preprocessor.clean_text(raw_text)
    print("清洗后:", cleaned)
    
    # 2. 分句
    sentences = preprocessor.split_sentences(cleaned)
    print("分句:", sentences)
    
    # 3. 分块
    chunks = preprocessor.chunk_text(cleaned, chunk_size=100)
    print(f"分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"块{i+1}: {chunk[:50]}...")
        
"""
批量Embedding调用策略

挑战:
1. API限流（通义千问有QPS限制）
2. 成本优化（按token计费）
3. 错误重试（网络不稳定）
4. 缓存机制（避免重复调用）

类比iOS开发:
- 批量请求API → 限流控制 → 错误重试 → 缓存存储
- 就像批量加载图片 → 下载队列 → 失败重试 → 内存缓存
"""

import time
import hashlib
from typing import dict
from functools import lru_cache

class BatchEmbedder:
    """批量Embedding处理器"""
    
    def __init__(
        self,
        api_key: str,
        batch_size: int = 25,
        max_retries: int = 3,
        rate_limit: int = 10
    ):
        """
        初始化
        
        Args:
            api_key: API密钥
            batch_size: 批量大小（通义千问最多25）
            max_retries: 最大重试次数
            rate_limit: 限流（QPS）
        """
        self.api_key = api_key
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.rate_limit = rate_limit
        self.last_call_time = 0
        
        dashscope.api_key = self.api_key
    
    def _rate_limit_sleep(self):
        """限流等待"""
        current_time = time.time()
        elapsed = current_time - self.last_call_time
        
        min_interval = 1.0 / self.rate_limit
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_call_time = time.time()
    
    def embed_with_retry(
        self,
        texts: list[str],
        text_type: str = "document"
    ) -> list[list[float]]:
        """
        带重试的批量Embedding
        
        Args:
            texts: 文本列表
            text_type: 文本类型
        
        Returns:
            向量列表
        """
        for attempt in range(self.max_retries):
            try:
                self._rate_limit_sleep()
                
                response = TextEmbedding.call(
                    model=TextEmbedding.models.text_embedding_v3,
                    input=texts,
                    parameters={"text_type": text_type}
                )
                
                if response.status_code == 200:
                    return [item['embedding'] for item in response.output['embeddings']]
                else:
                    raise ValueError(f"API返回错误: {response.message}")
            
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Embedding失败（重试{self.max_retries}次后）: {e}")
                
                # 指数退避
                sleep_time = 2 ** attempt
                print(f"请求失败，{sleep_time}秒后重试（{attempt+1}/{self.max_retries}）")
                time.sleep(sleep_time)
    
    def embed_large_batch(
        self,
        texts: list[str],
        text_type: str = "document",
        show_progress: bool = True
    ) -> list[list[float]]:
        """
        超大批量Embedding
        
        Args:
            texts: 文本列表（数量不限）
            text_type: 文本类型
            show_progress: 是否显示进度
        
        Returns:
            向量列表
        """
        all_embeddings = []
        total = len(texts)
        
        for i in range(0, total, self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_embeddings = self.embed_with_retry(batch_texts, text_type)
            all_embeddings.extend(batch_embeddings)
            
            if show_progress:
                print(f"进度: {min(i + self.batch_size, total)}/{total}")
        
        return all_embeddings

# 缓存机制
class CachedEmbedder:
    """带缓存的Embedder"""
    
    def __init__(self, cache_file: str = "./embedding_cache.json"):
        """
        初始化
        
        Args:
            cache_file: 缓存文件路径
        """
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.embedder = BatchEmbedder(
            api_key=os.getenv("DASHSCOPE_API_KEY")
        )
    
    def _load_cache(self) -> dict:
        """加载缓存"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                import json
                return json.load(f)
        return {}
    
    def _save_cache(self):
        """保存缓存"""
        import json
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def _get_cache_key(self, text: str, text_type: str = "document") -> str:
        """生成缓存键"""
        content = f"{text_type}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def embed(
        self,
        text: str,
        text_type: str = "document",
        use_cache: bool = True
    ) -> list[float]:
        """
        带缓存的Embedding
        
        Args:
            text: 输入文本
            text_type: 文本类型
            use_cache: 是否使用缓存
        
        Returns:
            向量
        """
        # 1. 检查缓存
        if use_cache:
            cache_key = self._get_cache_key(text, text_type)
            if cache_key in self.cache:
                return self.cache[cache_key]
        
        # 2. 调用API
        embedding = self.embedder.embed_with_retry([text], text_type)[0]
        
        # 3. 写入缓存
        if use_cache:
            self.cache[cache_key] = embedding
            self._save_cache()
        
        return embedding
    
    def embed_batch(
        self,
        texts: list[str],
        text_type: str = "document",
        use_cache: bool = True
    ) -> list[list[float]]:
        """
        批量Embedding（带缓存）
        
        Args:
            texts: 文本列表
            text_type: 文本类型
            use_cache: 是否使用缓存
        
        Returns:
            向量列表
        """
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # 1. 检查缓存
        for idx, text in enumerate(texts):
            cache_key = self._get_cache_key(text, text_type)
            if use_cache and cache_key in self.cache:
                embeddings.append((idx, self.cache[cache_key]))
            else:
                uncached_texts.append(text)
                uncached_indices.append(idx)
        
        # 2. 调用API获取未缓存的向量
        if uncached_texts:
            new_embeddings = self.embedder.embed_with_retry(
                uncached_texts, text_type
            )
            
            # 3. 写入缓存
            for text, emb in zip(uncached_texts, new_embeddings):
                cache_key = self._get_cache_key(text, text_type)
                self.cache[cache_key] = emb
            
            self._save_cache()
            
            # 4. 合并结果
            embeddings.extend(zip(uncached_indices, new_embeddings))
        
        # 5. 按原始顺序排序
        embeddings.sort(key=lambda x: x[0])
        return [emb for _, emb in embeddings]

# 使用示例
def batch_embedding_demo():
    """批量Embedding示例"""
    
    # 初始化带缓存的Embedder
    embedder = CachedEmbedder(cache_file="./cache/embedding_cache.json")
    
    # 准备大量文本
    documents = [
        "二次函数求导公式是f'(x) = 2ax + b",
        "导数表示函数在某点的瞬时变化率",
        "微积分包括微分和积分两部分",
        "连续函数一定可导，但可导函数不一定连续",
        # ... 可以有更多文档
    ] * 10  # 模拟50个文档
    
    # 批量Embedding
    embeddings = embedder.embed_batch(documents, text_type="document")
    
    print(f"成功生成 {len(embeddings)} 个向量")
    print(f"每个向量维度: {len(embeddings[0])}")  # 1536
    
    """
向量维度的影响

高维向量的优缺点:
优点:
- 信息保留更完整
- 表达能力更强

缺点:
- 存储空间大
- 检索速度慢
- 维度灾难（高维空间中距离度量失效）

降维策略:
1. PCA（主成分分析）
2. Matryoshka Representation Learning（俄罗斯套娃式）
3. 产品化剪枝
"""

from sklearn.decomposition import PCA
import numpy as np

class DimensionReducer:
    """向量维度降维器"""
    
    @staticmethod
    def pca_reduce(
        embeddings: list[list[float]],
        target_dim: int = 512
    ) -> list[list[float]]:
        """
        PCA降维
        
        Args:
            embeddings: 原始向量列表
            target_dim: 目标维度
        
        Returns:
            降维后的向量列表
        """
        # 转换为numpy数组
        embeddings_array = np.array(embeddings)
        
        # PCA降维
        pca = PCA(n_components=target_dim)
        reduced = pca.fit_transform(embeddings_array)
        
        # 转换回列表
        return reduced.tolist()
    
    @staticmethod
    def variance_analysis(embeddings: list[list[float]]) -> dict:
        """
        方差分析（判断降维损失）
        
        Args:
            embeddings: 原始向量列表
        
        Returns:
            方差分析结果
        """
        embeddings_array = np.array(embeddings)
        
        # 逐级降维测试
        dims = [1536, 1024, 768, 512, 256, 128]
        results = {}
        
        for dim in dims:
            if dim >= len(embeddings):
                continue
            
            pca = PCA(n_components=dim)
            reduced = pca.fit_transform(embeddings_array)
            explained_variance = sum(pca.explained_variance_ratio_)
            
            results[dim] = {
                "explained_variance": explained_variance,
                "loss": 1 - explained_variance
            }
        
        return results

# Matryoshka Embedding（俄罗斯套娃式）
"""
Matryoshka Representation Learning (MRL)

核心思想:
- 在一次embedding中同时生成多个维度的向量
- 不同场景选择不同维度
- 优点: 一次调用，多维度可用

目前通义千问不支持，但未来可能集成
"""

def dimension_selection_guide():
    """维度选择指南"""
    
    print("""
向量维度选择指南

┌─────────────┬──────────┬─────────┬─────────┐
│ 维度        │ 存储空间 │ 检索速度 │ 信息保留 │
├─────────────┼──────────┼─────────┼─────────┤
│ 1536（原）  │ 大       │ 慢       │ 100%    │
│ 1024        │ 中       │ 中       │ 95%+    │
│ 768         │ 中       │ 快       │ 90%+    │
│ 512         │ 小       │ 很快     │ 85%+    │
│ 256         │ 很小     │ 极快     │ 75%+    │
└─────────────┴──────────┴─────────┴─────────┘

选型建议:

1. 1536维（通义千问默认）
   - 场景: 追求最高质量
   - 成本: 存储和检索成本高
   - 推荐: 初期开发、小规模数据

2. 768维（BGE-base）
   - 场景: 平衡性能与成本
   - 成本: 中等
   - 推荐: 中等规模、实时性要求高

3. 512维（BGE-small / PCA降维）
   - 场景: 边缘设备、移动端
   - 成本: 低
   - 推荐: iOS端部署、大规模数据

成都教育科技公司建议:
- 知识库 < 10万条: 1536维（质量优先）
- 知识库 10万-100万条: 768维（平衡）
- 知识库 > 100万条: 512维（成本优先）
""")
    
"""
向量化质量评估

如何评估Embedding质量？
1. 内部评估: 聚类质量、检索召回率
2. 外部评估: 下游任务性能（如RAG准确率）

评估指标:
1. 聚类质量: Silhouette Score、Davies-Bouldin Index
2. 检索召回率: Recall@K
3. 语义一致性: 相似句子的相似度
"""

from sklearn.metrics import silhouette_score
from sklearn.cluster import KMeans
import numpy as np

class EmbeddingQualityEvaluator:
    """Embedding质量评估器"""
    
    @staticmethod
    def clustering_quality(
        embeddings: list[list[float]],
        labels: list[int] = None
    ) -> dict:
        """
        聚类质量评估
        
        Args:
            embeddings: 向量列表
            labels: 真实标签（可选）
        
        Returns:
            评估结果
        """
        embeddings_array = np.array(embeddings)
        
        # 无监督聚类（K-means）
        n_clusters = min(10, len(embeddings) // 10)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        predicted_labels = kmeans.fit_predict(embeddings_array)
        
        # Silhouette Score（轮廓系数）
        # 取值范围: [-1, 1]
        # > 0.5: 聚类效果好
        # < 0.2: 聚类效果差
        silhouette = silhouette_score(
            embeddings_array,
            predicted_labels
        )
        
        return {
            "silhouette_score": float(silhouette),
            "num_clusters": n_clusters,
            "clustering_quality": "优秀" if silhouette > 0.5 else "良好" if silhouette > 0.2 else "较差"
        }
    
    @staticmethod
    def retrieval_recall(
        query_embeddings: list[list[float]],
        doc_embeddings: list[list[float]],
        relevant_doc_ids: list[list[int]],
        top_k: int = 10
    ) -> dict:
        """
        检索召回率评估
        
        Args:
            query_embeddings: 查询向量列表
            doc_embeddings: 文档向量列表
            relevant_doc_ids: 每个查询的相关文档ID列表
            top_k: 检索Top-K
        
        Returns:
            评估结果
        """
        recalls = []
        
        for query_emb, relevant_ids in zip(query_embeddings, relevant_doc_ids):
            # 计算查询与所有文档的相似度
            similarities = [
                cosine_similarity(query_emb, doc_emb)
                for doc_emb in doc_embeddings
            ]
            
            # 获取Top-K文档
            top_k_indices = np.argsort(similarities)[-top_k:][::-1]
            
            # 计算召回率
            retrieved_relevant = len(
                set(top_k_indices) & set(relevant_ids)
            )
            recall = retrieved_relevant / len(relevant_ids)
            recalls.append(recall)
        
        return {
            "mean_recall": float(np.mean(recalls)),
            "recall_at_k": top_k,
            "num_queries": len(query_embeddings)
        }
    
    @staticmethod
    def semantic_consistency(
        sentence_pairs: list[tuple[str, str]]
    ) -> dict:
        """
        语义一致性评估
        
        Args:
            sentence_pairs: 相似句子对列表
        
        Returns:
            评估结果
        """
        from dashscope import TextEmbedding
        
        similarities = []
        
        for sent1, sent2 in sentence_pairs:
            # 获取向量
            response = TextEmbedding.call(
                model=TextEmbedding.models.text_embedding_v3,
                input=[sent1, sent2]
            )
            
            embeddings = [
                item['embedding'] for item in response.output['embeddings']
            ]
            
            # 计算相似度
            sim = cosine_similarity(embeddings[0], embeddings[1])
            similarities.append(sim)
        
        return {
            "mean_similarity": float(np.mean(similarities)),
            "min_similarity": float(np.min(similarities)),
            "std_similarity": float(np.std(similarities)),
            "quality": "优秀" if np.mean(similarities) > 0.8 else "良好" if np.mean(similarities) > 0.6 else "较差"
        }

# 使用示例
def quality_evaluation_demo():
    """质量评估示例"""
    
    evaluator = EmbeddingQualityEvaluator()
    
    # 1. 生成一些测试向量
    texts = [
        "二次函数求导",
        "导数公式推导",
        "微积分基础",
        "函数的变化率",
        "高考数学重点",
        "线性代数",
        "矩阵运算",
        "向量空间",
        "概率统计",
        "正态分布"
    ]
    
    # 获取向量
    embedder = QwenEmbedding()
    embeddings = embedder.embed_batch(texts)
    
    # 2. 聚类质量评估
    clustering_result = evaluator.clustering_quality(embeddings)
    print(f"聚类质量: {clustering_result}")
    
    # 3. 语义一致性评估
    sentence_pairs = [
        ("如何求导", "求导的方法"),
        ("二次函数", "抛物线"),
        ("微积分", "高等数学")
    ]
    consistency_result = evaluator.semantic_consistency(sentence_pairs)
    print(f"语义一致性: {consistency_result}")