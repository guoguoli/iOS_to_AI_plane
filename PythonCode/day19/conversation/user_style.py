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