"""
会话生命周期状态机实现
使用枚举定义状态，状态转换规则清晰
"""

from enum import Enum, auto
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Callable
import uuid

class SessionState(Enum):
    """会话状态枚举 - 完整生命周期状态"""
    CREATED = auto()      # 创建
    ACTIVE = auto()       # 活跃
    IDLE = auto()         # 空闲
    ARCHIVED = auto()     # 归档
    RECOVER = auto()      # 恢复中
    TERMINATED = auto()   # 终止

@dataclass
class Session:
    """会话数据模型"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: SessionState = SessionState.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    last_active_at: datetime = field(default_factory=datetime.now)
    archived_at: Optional[datetime] = None
    user_id: str = ""
    message_count: int = 0
    
    # 配置参数
    idle_timeout_minutes: int = 30      # 空闲超时（分钟）
    archive_days: int = 30               # 归档天数
    
    # 状态变更回调
    on_state_change: Optional[Callable] = None

class SessionLifecycleManager:
    """
    会话生命周期管理器
    
    核心职责：
    1. 管理会话状态转换
    2. 处理超时逻辑
    3. 触发状态变更事件
    
    对应Harness组件：状态管理组件（State Management）
    """
    
    def __init__(self):
        # 存储所有会话
        self.sessions: dict[str, Session] = {}
        
        # 定义合法的状态转换
        self.valid_transitions: dict[SessionState, list[SessionState]] = {
            SessionState.CREATED: [SessionState.ACTIVE, SessionState.TERMINATED],
            SessionState.ACTIVE: [SessionState.IDLE, SessionState.ARCHIVED, SessionState.TERMINATED],
            SessionState.IDLE: [SessionState.ACTIVE, SessionState.ARCHIVED, SessionState.TERMINATED],
            SessionState.ARCHIVED: [SessionState.RECOVER, SessionState.TERMINATED],
            SessionState.RECOVER: [SessionState.ACTIVE, SessionState.ARCHIVED, SessionState.TERMINATED],
            SessionState.TERMINATED: [],  # 终止后不可转换
        }
        
        # 状态转换日志
        self.transition_log: list[tuple[str, SessionState, SessionState]] = []
    
    def create_session(self, user_id: str) -> Session:
        """创建新会话"""
        session = Session(user_id=user_id)
        self.sessions[session.session_id] = session
        self._log_transition(session.session_id, None, SessionState.CREATED)
        return session
    
    def transition_to(self, session_id: str, new_state: SessionState) -> bool:
        """
        执行状态转换
        
        Args:
            session_id: 会话ID
            new_state: 目标状态
            
        Returns:
            转换是否成功
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        # 验证转换合法性
        valid_next_states = self.valid_transitions.get(session.state, [])
        if new_state not in valid_next_states:
            print(f"❌ 非法状态转换: {session.state.name} -> {new_state.name}")
            return False
        
        old_state = session.state
        session.state = new_state
        session.last_active_at = datetime.now()
        
        # 特殊状态处理
        if new_state == SessionState.ARCHIVED:
            session.archived_at = datetime.now()
        
        self._log_transition(session_id, old_state, new_state)
        
        # 触发回调
        if session.on_state_change:
            session.on_state_change(session, old_state, new_state)
        
        return True
    
    def user_message(self, session_id: str) -> bool:
        """用户发送消息 -> 激活会话"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session.message_count += 1
        session.last_active_at = datetime.now()
        
        # 从任何状态回到ACTIVE（除了TERMINATED和ARCHIVED）
        if session.state in [SessionState.IDLE, SessionState.CREATED]:
            return self.transition_to(session_id, SessionState.ACTIVE)
        
        return True
    
    def check_idle_timeout(self, session_id: str) -> bool:
        """
        检查并处理空闲超时
        
        Returns:
            是否触发了状态转换
        """
        session = self.sessions.get(session_id)
        if not session or session.state == SessionState.TERMINATED:
            return False
        
        now = datetime.now()
        idle_minutes = (now - session.last_active_at).total_seconds() / 60
        
        if idle_minutes >= session.idle_timeout_minutes:
            if session.state == SessionState.ACTIVE:
                return self.transition_to(session_id, SessionState.IDLE)
        
        return False
    
    def check_archive_eligibility(self, session_id: str) -> bool:
        """检查是否应该归档"""
        session = self.sessions.get(session_id)
        if not session or session.state == SessionState.TERMINATED:
            return False
        
        days_since_active = (datetime.now() - session.last_active_at).days
        
        if days_since_active >= session.archive_days:
            return self.transition_to(session_id, SessionState.ARCHIVED)
        
        return False
    
    def recover_session(self, session_id: str) -> bool:
        """恢复归档的会话"""
        session = self.sessions.get(session_id)
        if not session or session.state != SessionState.ARCHIVED:
            return False
        
        return self.transition_to(session_id, SessionState.RECOVER)
    
    def terminate_session(self, session_id: str) -> bool:
        """终止会话"""
        return self.transition_to(session_id, SessionState.TERMINATED)
    
    def _log_transition(self, session_id: str, from_state: Optional[SessionState], to_state: SessionState):
        """记录状态转换日志"""
        self.transition_log.append((session_id, from_state, to_state))
    
    def get_session_info(self, session_id: str) -> dict:
        """获取会话信息"""
        session = self.sessions.get(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session.session_id,
            "state": session.state.name,
            "created_at": session.created_at.isoformat(),
            "last_active_at": session.last_active_at.isoformat(),
            "message_count": session.message_count,
            "user_id": session.user_id
        }