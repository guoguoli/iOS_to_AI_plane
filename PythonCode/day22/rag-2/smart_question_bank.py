# 智能题库检索系统核心实现
class SmartQuestionBank:
    """智能题库系统"""
    
    def __init__(self):
        self.collection = None
        self.llm_api = None
    
    def initialize(self, chroma_client):
        """初始化系统"""
        self.collection = chroma_client.get_collection("question_bank")
    
    def add_question(
        self,
        question_text: str,
        subject: str,
        topic: str,
        difficulty: str,
        answer: str,
        explanation: str
    ):
        """添加题目到知识库"""
        
        metadata = {
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "type": "question"
        }
        
        # 文档内容：题目 + 答案 + 解析
        content = f"""题目：{question_text}

答案：{answer}

解析：{explanation}"""
        
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[f"q_{hash(question_text)}"]
        )
    
    def search_similar_questions(
        self,
        query: str,
        subject: str = None,
        difficulty: str = None,
        top_k: int = 5
    ) -> list[dict]:
        """检索相似题目"""
        
        # 构建过滤条件
        where_filter = {}
        if subject:
            where_filter["subject"] = subject
        if difficulty:
            where_filter["difficulty"] = difficulty
        
        # 执行检索
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter if where_filter else None
        )
        
        return [
            {
                "question": self._extract_question(doc),
                "answer": self._extract_answer(doc),
                "explanation": self._extract_explanation(doc),
                "score": 1 - dist,  # 距离转相似度
                "metadata": meta
            }
            for doc, dist, meta in zip(
                results['documents'][0],
                results['distances'][0],
                results['metadatas'][0]
            )
        ]
    
    def generate_explanation(
        self,
        question: str,
        similar_questions: list[dict]
    ) -> str:
        """生成题目解析（使用RAG）"""
        
        # 构建上下文
        context = "\n\n".join([
            f"【参考题目{i+1}】\n{q['question']}\n答案：{q['answer']}"
            for i, q in enumerate(similar_questions[:3])
        ])
        
        prompt = f"""根据以下相似题目的解题思路，
帮助学生理解这道题目的解法。

【目标题目】
{question}

【参考题目】
{context}

请提供：
1. 解题思路
2. 关键步骤
3. 知识点总结"""
        
        response = self.llm_api.call(prompt)
        return response