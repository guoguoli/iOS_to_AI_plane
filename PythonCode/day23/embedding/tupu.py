"""
成都教育科技场景：教材知识图谱

应用目标:
1. 提取教材中的知识点（概念、公式、定理）
2. 计算知识点之间的语义关联
3. 构建知识图谱（节点：知识点，边：关联关系）
4. 可视化展示知识结构

技术方案:
- 知识点提取: LLM + 正则表达式
- 关联发现: Embedding相似度计算
- 知识图谱存储: Neo4j / NetworkX
- 可视化: D3.js / Graphviz
"""

import networkx as nx
from typing import list, dict

class KnowledgeGraphBuilder:
    """知识图谱构建器"""
    
    def __init__(self, embedder):
        """
        初始化
        
        Args:
            embedder: Embedding模型
        """
        self.embedder = embedder
        self.graph = nx.Graph()
        self.knowledge_points = []  # 知识点列表
        self.embeddings = []  # 知识点向量
    
    def extract_knowledge_points(self, text: str) -> list[str]:
        """
        提取知识点
        
        Args:
            text: 教材文本
        
        Returns:
            知识点列表
        """
        # 简化实现：用正则表达式提取关键短语
        # 实际生产中需要LLM辅助提取
        
        knowledge_points = []
        
        # 提取"定义"、"定理"、"公式"
        import re
        
        # 公式模式
        formula_pattern = r'[fF]\([^)]+\)\s*='
        formulas = re.findall(formula_pattern, text)
        knowledge_points.extend(formulas)
        
        # 定理模式
        theorem_pattern = r'[定定]理：?([^。]{2,10})'
        theorems = re.findall(theorem_pattern, text)
        knowledge_points.extend(theorems)
        
        # 概念模式
        concept_pattern = r'([a-zA-Z]+)是([^。]{10,30})'
        concepts = re.findall(concept_pattern, text)
        for concept in concepts:
            knowledge_points.append(concept[0] + ": " + concept[1][:20])
        
        return list(set(knowledge_points))
    
    def discover_relations(self, threshold: float = 0.7) -> list[dict]:
        """
        发现知识点关联
        
        Args:
            threshold: 相似度阈值
        
        Returns:
            关联关系列表
        """
        relations = []
        
        # 计算所有知识点之间的相似度
        for i in range(len(self.knowledge_points)):
            for j in range(i + 1, len(self.knowledge_points)):
                similarity = cosine_similarity(
                    self.embeddings[i],
                    self.embeddings[j]
                )
                
                if similarity >= threshold:
                    relations.append({
                        "source": self.knowledge_points[i],
                        "target": self.knowledge_points[j],
                        "weight": similarity
                    })
        
        return relations
    
    def build_graph(
        self,
        knowledge_points: list[str],
        relations: list[dict]
    ) -> nx.Graph:
        """
        构建知识图谱
        
        Args:
            knowledge_points: 知识点列表
            relations: 关联关系列表
        
        Returns:
            NetworkX图对象
        """
        # 添加节点
        for kp in knowledge_points:
            self.graph.add_node(kp[:30], name=kp)
        
        # 添加边
        for rel in relations:
            self.graph.add_edge(
                rel["source"][:30],
                rel["target"][:30],
                weight=rel["weight"]
            )
        
        return self.graph
    
    def export_graph_data(self) -> dict:
        """
        导出图谱数据（用于可视化）
        
        Returns:
            JSON格式的图谱数据
        """
        nodes = [
            {
                "id": node,
                "label": node,
                "degree": self.graph.degree(node)
            }
            for node in self.graph.nodes()
        ]
        
        edges = [
            {
                "source": edge[0],
                "target": edge[1],
                "weight": edge[2]["weight"]
            }
            for edge in self.graph.edges(data=True)
        ]
        
        return {
            "nodes": nodes,
            "edges": edges
        }

# 使用示例
def education_knowledge_graph_demo():
    """教育知识图谱构建示例"""
    
    embedder = QwenEmbedding()
    builder = KnowledgeGraphBuilder(embedder)
    
    # 模拟教材内容
    textbook_content = """
    二次函数是高中数学的重点内容。二次函数的一般式是f(x) = ax² + bx + c。
    定理：二次函数的图像是抛物线。抛物线的开口方向由a决定，a>0时向上，a<0时向下。
    定理：抛物线的对称轴是直线x = -b/2a。顶点坐标是(-b/2a, (4ac-b²)/4a)。
    公式：二次函数的导数是f'(x) = 2ax + b。
    导数表示函数在某点的瞬时变化率。
    定理：导数为0的点可能是函数的极值点。
    """
    
    # 1. 提取知识点
    knowledge_points = builder.extract_knowledge_points(textbook_content)
    print(f"提取到 {len(knowledge_points)} 个知识点:")
    for kp in knowledge_points:
        print(f"  - {kp}")
    
    builder.knowledge_points = knowledge_points
    
    # 2. 生成Embedding
    builder.embeddings = embedder.embed_batch(knowledge_points)
    
    # 3. 发现关联
    relations = builder.discover_relations(threshold=0.6)
    print(f"\n发现 {len(relations)} 个关联关系:")
    for rel in relations[:5]:
        print(f"  - {rel['source']} ↔ {rel['target']} (相似度: {rel['weight']:.4f})")
    
    # 4. 构建图谱
    graph = builder.build_graph(knowledge_points, relations)
    
    # 5. 导出数据
    graph_data = builder.export_graph_data()
    
    # 保存为JSON文件（用于前端可视化）
    import json
    with open('./outputs/knowledge_graph.json', 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n知识图谱已保存到 knowledge_graph.json")
    print(f"节点数: {len(graph_data['nodes'])}, 边数: {len(graph_data['edges'])}")
    """
成都医疗健康场景：病历语义索引

应用目标:
1. 构建病历知识库（诊断、症状、治疗方案）
2. 支持自然语言查询（如"高血压患者的饮食建议"）
3. 语义相似度搜索（找到相似的病例）
4. 辅助医生决策

技术方案:
- 专用医疗Embedding模型（BGE-M3医疗版）
- 结构化数据 + 非结构化文本混合
- 隐私保护（脱敏处理、本地部署）

挑战:
1. 专业术语多（ICD-10编码、药品名称）
2. 隐私要求高（患者信息保护）
3. 准确性要求高（医疗决策影响大）
"""

class MedicalRecordIndexer:
    """病历语义索引器"""
    
    def __init__(self, embedder):
        """
        初始化
        
        Args:
            embedder: Embedding模型（建议用BGE-M3医疗版）
        """
        self.embedder = embedder
        self.records = []
        self.embeddings = []
    
    def anonymize_record(self, record: str) -> str:
        """
        脱敏处理
        
        Args:
            record: 原始病历
        
        Returns:
            脱敏后的病历
        """
        import re
        
        # 1. 去除姓名
        anonymized = re.sub(r'患者[：:]\s*[^\s，。]{2,4}', '患者：XXX', record)
        
        # 2. 去除身份证号
        anonymized = re.sub(r'\d{17}[\dXx]', 'XXXXXXXXXXXXXXXXX', anonymized)
        
        # 3. 去除手机号
        anonymized = re.sub(r'1[3-9]\d{9}', 'XXXXXXXXXXX', anonymized)
        
        return anonymized
    
    def index_records(self, records: list[dict]):
        """
        索引病历
        
        Args:
            records: 病历列表
                每个病历包含: {"diagnosis": "...", "symptoms": "...", "treatment": "..."}
        """
        for record in records:
            # 合并多个字段
            text = f"""
            诊断：{record['diagnosis']}
            症状：{record['symptoms']}
            治疗方案：{record['treatment']}
            """
            
            # 脱敏
            anonymized = self.anonymize_record(text)
            
            # 存储原始记录（脱敏后）
            self.records.append({
                "diagnosis": record['diagnosis'],
                "symptoms": record['symptoms'],
                "treatment": record['treatment'],
                "text": anonymized
            })
        
        # 批量Embedding
        texts = [record['text'] for record in self.records]
        self.embeddings = self.embedder.embed_batch(texts)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict = None
    ) -> list[dict]:
        """
        语义搜索病历
        
        Args:
            query: 查询文本
            top_k: 返回Top-K
            filters: 过滤条件（如疾病类型）
        
        Returns:
            搜索结果
        """
        # 获取查询向量
        query_vec = self.embedder.embed_query(query)
        
        # 计算相似度
        similarities = [
            cosine_similarity(query_vec, doc_vec)
            for doc_vec in self.embeddings
        ]
        
        # 排序
        indexed_results = sorted(
            zip(self.records, similarities),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 过滤
        filtered_results = []
        for record, score in indexed_results:
            if filters:
                match = True
                for key, value in filters.items():
                    if record.get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            filtered_results.append({
                "record": record,
                "similarity": score
            })
        
        return filtered_results[:top_k]

# 使用示例
def medical_indexing_demo():
    """病历索引示例"""
    
    embedder = QwenEmbedding()
    indexer = MedicalRecordIndexer(embedder)
    
    # 模拟病历数据
    medical_records = [
        {
            "diagnosis": "原发性高血压",
            "symptoms": "头晕、头痛、心悸",
            "treatment": "降压药物治疗、低盐饮食、适量运动"
        },
        {
            "diagnosis": "2型糖尿病",
            "symptoms": "多饮、多尿、体重下降",
            "treatment": "降糖药、饮食控制、血糖监测"
        },
        {
            "diagnosis": "高血压",
            "symptoms": "眩晕、胸闷",
            "treatment": "钙通道阻滞剂、ACE抑制剂"
        },
        {
            "diagnosis": "冠心病",
            "symptoms": "胸痛、气短",
            "treatment": "抗血小板药物、硝酸酯类药物"
        }
    ]
    
    # 索引病历
    indexer.index_records(medical_records)
    print(f"成功索引 {len(indexer.records)} 条病历")
    
    # 语义搜索
    query = "高血压患者应该怎么控制血压？"
    results = indexer.search(query, top_k=3)
    
    print(f"\n查询: {query}")
    print("\n搜索结果:")
    for i, result in enumerate(results, 1):
        print(f"\n结果 {i}:")
        print(f"  相似度: {result['similarity']:.4f}")
        print(f"  诊断: {result['record']['diagnosis']}")
        print(f"  症状: {result['record']['symptoms']}")
        print(f"  治疗: {result['record']['treatment']}")