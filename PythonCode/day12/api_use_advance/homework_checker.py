# homework_checker.py
"""
作业批改助手 - 核心服务
"""

import json
import os
import base64
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
import sqlite3

from dashscope import Generation
from qwen_vl_utils import process_vlm_image

# ============================================================
# 数据模型
# ============================================================

@dataclass
class HomeworkRecord:
    """作业记录"""
    id: Optional[int] = None
    student_name: str = ""
    subject: str = ""  # math, english, chinese
    grade: str = ""
    image_path: str = ""
    result: str = ""  # correct, wrong, partial
    score: int = 0  # 0-100
    feedback: str = ""
    wrong_topics: str = ""  # JSON格式的错题列表
    created_at: str = ""

@dataclass
class CorrectionResult:
    """批改结果"""
    is_correct: bool
    score: int
    feedback: str
    explanation: str
    related_knowledge: List[str]

# ============================================================
# 通义千问API调用
# ============================================================

class QwenVLService:
    """通义千问视觉语言模型服务"""
    
    def __init__(self):
        self.model = "qwen-vl-plus"
    
    def analyze_homework_image(self, image_path: str, subject: str) -> Dict:
        """
        分析作业图片
        
        Args:
            image_path: 图片路径
            subject: 科目 (math, english)
        
        Returns:
            分析结果字典
        """
        
        # 构建提示词
        prompt = self._build_prompt(subject)
        
        # 调用视觉模型
        # 注意：实际使用需要安装 qwen-vl-utils
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"image": image_path},
                        {"text": prompt}
                    ]
                }
            ]
            
            response = Generation.call(
                model=self.model,
                messages=messages,
                temperature=0.1  # 低随机性，保证准确性
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "result": response.output.choices[0].message.content
                }
            else:
                return {
                    "success": False,
                    "error": f"{response.code} - {response.message}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_prompt(self, subject: str) -> str:
        """构建分析提示词"""
        
        prompts = {
            "math": """你是一位资深数学老师，请仔细分析这张数学作业图片：
1. 识别作业中的所有题目和学生的作答
2. 判断每题的对错
3. 对于错题，给出正确的解题思路
4. 总结学生的薄弱知识点
5. 给出总体评分（0-100分）

请用JSON格式返回结果：
{
    "total_score": 总分,
    "questions": [
        {
            "number": 题号,
            "student_answer": 学生答案,
            "correct_answer": 正确答案,
            "is_correct": true/false,
            "explanation": 解释（仅错题）
        }
    ],
    "weak_topics": ["薄弱知识点列表"],
    "feedback": "总体评语"
}""",
            
            "english": """你是一位资深英语老师，请仔细分析这张英语作业图片：
1. 识别作业类型（选择题、填空题、作文等）
2. 检查语法错误
3. 给出修改建议
4. 评估整体水平

请用JSON格式返回结果：
{
    "total_score": 总分,
    "grammar_errors": ["语法错误列表"],
    "suggestions": ["修改建议"],
    "overall_level": "水平评估",
    "feedback": "总体评语"
}"""
        }
        
        return prompts.get(subject, prompts["math"])

class HomeworkChecker:
    """作业批改服务"""
    
    def __init__(self, db_path: str = "homework.db"):
        self.db_path = db_path
        self.vl_service = QwenVLService()
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS homework_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                subject TEXT NOT NULL,
                grade TEXT,
                image_path TEXT,
                result TEXT,
                score INTEGER,
                feedback TEXT,
                wrong_topics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def check_homework(
        self,
        image_path: str,
        student_name: str,
        subject: str,
        grade: str = "unknown"
    ) -> CorrectionResult:
        """
        批改作业
        
        Args:
            image_path: 作业图片路径
            student_name: 学生姓名
            subject: 科目
            grade: 年级
        
        Returns:
            批改结果
        """
        
        # 调用视觉模型分析
        analysis = self.vl_service.analyze_homework_image(image_path, subject)
        
        if not analysis["success"]:
            return CorrectionResult(
                is_correct=False,
                score=0,
                feedback=f"分析失败: {analysis['error']}",
                explanation="",
                related_knowledge=[]
            )
        
        # 解析分析结果
        try:
            result_text = analysis["result"]
            # 尝试提取JSON（可能包含在markdown代码块中）
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                json_str = result_text.split("```")[1].split("```")[0]
            else:
                json_str = result_text
            
            result_data = json.loads(json_str)
            
            # 保存记录
            self._save_record(
                student_name=student_name,
                subject=subject,
                grade=grade,
                image_path=image_path,
                score=result_data.get("total_score", 0),
                feedback=result_data.get("feedback", ""),
                wrong_topics=json.dumps(result_data.get("weak_topics", []))
            )
            
            return CorrectionResult(
                is_correct=result_data.get("total_score", 0) >= 60,
                score=result_data.get("total_score", 0),
                feedback=result_data.get("feedback", ""),
                explanation=self._generate_explanation(result_data),
                related_knowledge=result_data.get("weak_topics", [])
            )
            
        except json.JSONDecodeError as e:
            return CorrectionResult(
                is_correct=False,
                score=0,
                feedback=f"结果解析失败: {str(e)}",
                explanation=analysis["result"],
                related_knowledge=[]
            )
    
    def _generate_explanation(self, result_data: Dict) -> str:
        """生成讲解内容"""
        explanations = []
        
        for q in result_data.get("questions", []):
            if not q.get("is_correct"):
                explanations.append(
                    f"第{q.get('number')}题: {q.get('explanation', '请复习相关知识点')}"
                )
        
        return "\n".join(explanations) if explanations else "所有题目都正确，继续保持！"
    
    def _save_record(
        self,
        student_name: str,
        subject: str,
        grade: str,
        image_path: str,
        score: int,
        feedback: str,
        wrong_topics: str
    ):
        """保存作业记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO homework_records 
            (student_name, subject, grade, image_path, score, feedback, wrong_topics)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_name, subject, grade, image_path, score, feedback, wrong_topics))
        
        conn.commit()
        conn.close()
    
    def get_student_report(self, student_name: str) -> Dict:
        """获取学生学习报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT subject, score, wrong_topics, created_at
            FROM homework_records
            WHERE student_name = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (student_name,))
        
        records = cursor.fetchall()
        conn.close()
        
        if not records:
            return {"message": "暂无作业记录"}
        
        # 统计薄弱知识点
        all_weak_topics = []
        total_score = 0
        
        for record in records:
            if record[2]:  # wrong_topics
                topics = json.loads(record[2])
                all_weak_topics.extend(topics)
            total_score += record[1]
        
        # 找出最常见的薄弱点
        topic_counts = {}
        for topic in all_weak_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        top_weak_topics = sorted(
            topic_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "student_name": student_name,
            "total_assignments": len(records),
            "average_score": total_score // len(records),
            "top_weak_topics": [{"topic": t, "count": c} for t, c in top_weak_topics],
            "recent_records": [
                {
                    "subject": r[0],
                    "score": r[1],
                    "date": r[3]
                }
                for r in records[:5]
            ]
        }

# ============================================================
# API端点（FastAPI）
# ============================================================


from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import shutil

app = FastAPI(title="作业批改助手API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

checker = HomeworkChecker()

@app.post("/api/check")
async def check_homework(
    file: UploadFile = File(...),
    student_name: str = Form(...),
    subject: str = Form(...),
    grade: str = Form("unknown")
):
    # 保存上传的图片
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{datetime.now().timestamp()}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 批改作业
    result = checker.check_homework(
        image_path=file_path,
        student_name=student_name,
        subject=subject,
        grade=grade
    )
    
    return {
        "success": result.is_correct,
        "score": result.score,
        "feedback": result.feedback,
        "explanation": result.explanation,
        "related_knowledge": result.related_knowledge
    }

@app.get("/api/report/{student_name}")
async def get_report(student_name: str):
    return checker.get_student_report(student_name)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


print("✅ 作业批改助手核心模块已定义")