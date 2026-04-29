"""
成都教育科技 - 作业批改多轮对话系统

功能：
1. 多轮对话上下文管理
2. 学生薄弱点追踪
3. 作业批改与讲解
"""

import os
import json
from datetime import datetime
from typing import Optional
from dashscope import Generation
from dotenv import load_dotenv

load_dotenv()


class StudentProfile:
    """学生画像 - 记录学习特征"""
    
    def __init__(self, student_id: str):
        self.student_id = student_id
        self.weak_topics: list[str] = []       # 薄弱知识点
        self.error_patterns: list[str] = []      # 错误模式
        self.conversation_count = 0              # 对话轮次
    
    def add_weak_topic(self, topic: str):
        """记录薄弱知识点"""
        if topic not in self.weak_topics:
            self.weak_topics.append(topic)
    
    def to_context_string(self) -> str:
        """转换为上下文字符串"""
        if not self.weak_topics:
            return ""
        
        return f"""学生背景信息：
- 已识别薄弱知识点：{', '.join(self.weak_topics)}
- 需要特别关注这些知识点的讲解
"""


class HomeworkGradingSession:
    """
    作业批改会话管理器
    
    核心功能：
    1. 多轮对话上下文
    2. 学生画像更新
    3. 作业批改
    """
    
    def __init__(self, student_id: str, api_key: Optional[str] = None):
        self.student_id = student_id
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        
        # 学生画像
        self.profile = StudentProfile(student_id)
        
        # 对话历史（消息列表）
        self.messages: list[dict] = [
            {
                "role": "system",
                "content": """你是一位经验丰富的数学老师，专门帮助学生理解和掌握数学知识。

你的教学风格：
1. 耐心细致，用通俗易懂的语言解释概念
2. 喜欢用具体例子帮助理解抽象概念
3. 善于发现学生的理解误区并及时纠正
4. 会根据学生的反馈调整讲解方式

当学生提问时：
1. 先确认学生具体哪里不明白
2. 提供清晰易懂的解释
3. 给出类似的练习题帮助巩固
4. 适时总结关键知识点

如果发现学生有知识薄弱点，记录下来以便后续复习。"""
            }
        ]
        
        # 作业记录
        self.homework_history: list[dict] = []
    
    def _build_context(self, current_question: str) -> str:
        """构建包含学生画像的上下文"""
        profile_context = self.profile.to_context_string()
        
        if profile_context:
            return f"""{profile_context}

当前学生提问：{current_question}
"""
        return f"当前学生提问：{current_question}"
    
    def chat(self, user_message: str) -> str:
        """
        处理学生提问
        
        Args:
            user_message: 学生的问题
            
        Returns:
            AI回复
        """
        # 添加用户消息
        self.messages.append({"role": "user", "content": user_message})
        
        # 构建增强上下文（注入学生画像）
        context_prompt = self._build_context(user_message)
        
        # 如果有学生画像，插入到系统消息后
        if context_prompt:
            enhanced_messages = (
                self.messages[:-1] +
                [{"role": "system", "content": context_prompt}] +
                [self.messages[-1]]
            )
        else:
            enhanced_messages = self.messages
        
        # 调用API
        response = Generation.call(
            model="qwen-plus",
            messages=enhanced_messages,
            result_format="message",
            api_key=self.api_key
        )
        
        if response.status_code != 200:
            raise Exception(f"API调用失败: {response.message}")
        
        assistant_message = response.output.choices[0].message.content
        
        # 保存回复
        self.messages.append({"role": "assistant", "content": assistant_message})
        
        # 更新学生画像（检测薄弱点）
        self._detect_weak_topics(user_message, assistant_message)
        
        return assistant_message
    
    def _detect_weak_topics(self, question: str, answer: str):
        """检测并记录薄弱知识点"""
        # 简化实现：关键词匹配
        math_topics = {
            "函数": ["函数", "f(x)", "y=", "定义域", "值域"],
            "几何": ["三角形", "四边形", "圆形", "面积", "周长", "勾股"],
            "代数": ["方程", "解", "未知数", "系数"],
            "概率": ["概率", "可能性", "随机", "统计"]
        }
        
        for topic, keywords in math_topics.items():
            if any(kw in question for kw in keywords):
                # 如果AI回复中包含"需要加强"、"薄弱"等提示词
                if any(phrase in answer for phrase in ["需要加强", "薄弱", "建议复习", "多练习"]):
                    self.profile.add_weak_topic(topic)
    
    def grade_homework(self, question: str, student_answer: str, correct_answer: str) -> dict:
        """
        批改作业
        
        Args:
            question: 题目
            student_answer: 学生答案
            correct_answer: 正确答案
            
        Returns:
            批改结果
        """
        # 构建批改prompt
        grading_prompt = f"""请批改以下数学作业：

题目：{question}
学生答案：{student_answer}
正确答案：{correct_answer}

请从以下维度进行评分并给出反馈：
1. 最终结果是否正确
2. 解题思路是否清晰
3. 计算过程是否规范
4. 是否有其他值得注意的问题

请用JSON格式返回：
{{
    "score": 分数(0-100),
    "is_correct": 是否正确,
    "feedback": 具体反馈,
    "suggestion": 改进建议
}}
"""
        
        response = Generation.call(
            model="qwen-turbo",
            messages=[{"role": "user", "content": grading_prompt}],
            result_format="message",
            api_key=self.api_key
        )
        
        result = json.loads(response.output.choices[0].message.content)
        
        # 记录到历史
        self.homework_history.append({
            "question": question,
            "student_answer": student_answer,
            "correct_answer": correct_answer,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
    
    def get_summary(self) -> dict:
        """获取会话总结"""
        return {
            "student_id": self.student_id,
            "conversation_count": len(self.messages) // 2,
            "weak_topics": self.profile.weak_topics,
            "homework_count": len(self.homework_history),
            "recent_homework": self.homework_history[-3:] if self.homework_history else []
        }


def demo_chengdu_edtech():
    """演示成都教育科技作业批改系统"""
    
    print("=" * 60)
    print("成都教育科技 - AI作业批改助手演示")
    print("=" * 60)
    
    # 创建会话
    session = HomeworkGradingSession(
        student_id="student_20240315_001",
        api_key=os.environ.get("DASHSCOPE_API_KEY")
    )
    
    # 第一轮：学生提问
    print("\n【学生提问1】请问一元二次方程的求根公式是什么？")
    response1 = session.chat("请问一元二次方程的求根公式是什么？")
    print(f"\n【AI回复】{response1}")
    
    # 第二轮：继续追问
    print("\n【学生提问2】能给我出道题练练吗？")
    response2 = session.chat("能给我出道题练练吗？")
    print(f"\n【AI回复】{response2}")
    
    # 第三轮：提交作业
    print("\n【学生提问3】我算了下，答案是x=3或x=-1，对吗？")
    response3 = session.chat("我算了下，答案是x=3或x=-1，对吗？")
    print(f"\n【AI回复】{response3}")
    
    # 批改作业示例
    print("\n" + "-" * 40)
    print("【作业批改】")
    result = session.grade_homework(
        question="求解 x² - 2x - 3 = 0",
        student_answer="x = 3 或 x = -1",
        correct_answer="x = 3 或 x = -1"
    )
    print(f"得分：{result['score']}分")
    print(f"正确：{result['is_correct']}")
    print(f"反馈：{result['feedback']}")
    print(f"建议：{result['suggestion']}")
    
    # 获取会话总结
    print("\n" + "-" * 40)
    print("【会话总结】")
    summary = session.get_summary()
    print(f"学生ID：{summary['student_id']}")
    print(f"对话轮次：{summary['conversation_count']}")
    print(f"薄弱知识点：{summary['weak_topics']}")
    print(f"作业数量：{summary['homework_count']}")
    
    return session


if __name__ == "__main__":
    # 需要设置环境变量
    # export DASHSCOPE_API_KEY="your-api-key"
    demo_chengdu_edtech()