from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

class CommunicationStyle(Enum):
    """沟通风格偏好"""
    FORMAL = "formal"           # 正式
    CASUAL = "casual"            # 随意
    TECHNICAL = "technical"      # 技术性
    EDUCATIONAL = "educational"  # 教育性

class ResponseLength(Enum):
    """响应长度偏好"""
    BRIEF = "brief"              # 简短
    MODERATE = "moderate"        # 中等
    DETAILED = "detailed"        # 详细

@dataclass
class UserPreference:
    """
    用户偏好数据模型
    
    存储用户的所有偏好信息，支持持久化
    """
    user_id: str
    
    # 对话风格
    communication_style: CommunicationStyle = CommunicationStyle.EDUCATIONAL
    response_length: ResponseLength = ResponseLength.MODERATE
    
    # 专业领域（可能多个）
    expertise_domains: list[str] = field(default_factory=list)
    
    # 交互偏好
    prefers_emoji: bool = True
    prefers_code_blocks: bool = True
    prefers_explanations: bool = True
    
    # 学习统计
    total_sessions: int = 0
    total_messages: int = 0
    avg_session_length: float = 0.0
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    # 冷启动标志
    is_cold_start: bool = True
    interaction_count: int = 0  # 用于判断冷启动是否结束

@dataclass
class PreferenceUpdate:
    """偏好更新记录"""
    timestamp: datetime
    field_name: str
    old_value: any
    new_value: any
    confidence: float  # 更新置信度
    
import re
from collections import Counter
from typing import Optional

class PreferenceExtractor:
    """
    用户偏好提取器
    
    从对话历史中分析并提取用户偏好
    
    对应Harness组件：上下文架构组件（Context Architecture）
    用户偏好是上下文的重要组成部分
    """
    
    # 风格关键词映射
    STYLE_KEYWORDS = {
        CommunicationStyle.FORMAL: [
            "请", "麻烦", "感谢", "尊敬", "严谨", "准确"
        ],
        CommunicationStyle.CASUAL: [
            "嘿", "哈", "行", "OK", "随便", "搞定"
        ],
        CommunicationStyle.TECHNICAL: [
            "API", "SDK", "架构", "实现", "算法", "优化"
        ],
        CommunicationStyle.EDUCATIONAL: [
            "为什么", "如何", "学习", "理解", "讲解", "例子"
        ]
    }
    
    def __init__(self, min_confidence: float = 0.6):
        """
        Args:
            min_confidence: 最低置信度阈值
        """
        self.min_confidence = min_confidence
    
    def extract_from_messages(self, messages: list[dict]) -> dict:
        """
        从消息历史中提取偏好
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            
        Returns:
            提取的偏好信息
        """
        user_messages = [m["content"] for m in messages if m.get("role") == "user"]
        
        if not user_messages:
            return {}
        
        return {
            "communication_style": self._detect_style(user_messages),
            "response_length": self._detect_length_preference(user_messages),
            "expertise_domains": self._detect_domains(user_messages),
            "emoji_usage": self._detect_emoji_preference(user_messages),
            "code_preference": self._detect_code_preference(user_messages)
        }
    
    def _detect_style(self, messages: list[str]) -> tuple[CommunicationStyle, float]:
        """检测沟通风格"""
        style_scores = {style: 0 for style in CommunicationStyle}
        
        for msg in messages:
            msg_lower = msg.lower()
            for style, keywords in self.STYLE_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in msg_lower:
                        style_scores[style] += 1
        
        if not style_scores or max(style_scores.values()) == 0:
            return CommunicationStyle.EDUCATIONAL, 0.5
        
        # 归一化
        total = sum(style_scores.values())
        best_style = max(style_scores, key=style_scores.get)
        confidence = style_scores[best_style] / total if total > 0 else 0.5
        
        return best_style, max(confidence, self.min_confidence)
    
    def _detect_length_preference(self, messages: list[str]) -> ResponseLength:
        """检测响应长度偏好"""
        avg_length = sum(len(m) for m in messages) / len(messages) if messages else 0
        
        if avg_length < 50:
            return ResponseLength.BRIEF
        elif avg_length < 200:
            return ResponseLength.MODERATE
        else:
            return ResponseLength.DETAILED
    
    def _detect_domains(self, messages: list[str]) -> list[str]:
        """检测专业领域"""
        domain_keywords = {
            "iOS开发": ["ios", "swift", "xcode", "uikit", "swiftui", "core ml"],
            "Python": ["python", "pip", "django", "flask", "pandas"],
            "机器学习": ["ml", "machine learning", "tensorflow", "pytorch", "模型训练"],
            "Web开发": ["html", "css", "javascript", "react", "vue", "前端"],
            "后端": ["api", "backend", "数据库", "server", "微服务"]
        }
        
        domains = []
        all_text = " ".join(messages).lower()
        
        for domain, keywords in domain_keywords.items():
            if any(kw in all_text for kw in keywords):
                domains.append(domain)
        
        return domains
    
    def _detect_emoji_preference(self, messages: list[str]) -> bool:
        """检测emoji使用偏好"""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "]+", flags=re.UNICODE
        )
        
        messages_with_emoji = sum(1 for m in messages if emoji_pattern.search(m))
        return messages_with_emoji / len(messages) > 0.3 if messages else False
    
    def _detect_code_preference(self, messages: list[str]) -> bool:
        """检测代码块偏好"""
        code_block_count = sum(1 for m in messages if "```" in m or "`" in m)
        return code_block_count / len(messages) > 0.2 if messages else False