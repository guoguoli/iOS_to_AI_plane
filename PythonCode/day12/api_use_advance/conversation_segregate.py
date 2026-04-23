from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import threading

@dataclass
class ConversationContext:
    """对话上下文"""
    messages: List[Dict[str, str]]
    variables: Dict[str, str]  # 自定义变量
    metadata: Dict[str, any]    # 元数据

class SessionManager:
    """
    会话管理器 - 实现会话隔离
    
    iOS类比：每个会话就像一个独立的 Scene（窗口场景）
    """
    
    def __init__(self):
        self._sessions: Dict[str, ConversationContext] = {}
        self._lock = threading.Lock()
    
    def create_session(self, session_id: str) -> ConversationContext:
        """创建新会话"""
        with self._lock:
            if session_id in self._sessions:
                return self._sessions[session_id]
            
            ctx = ConversationContext(
                messages=[],
                variables={},
                metadata={'created_at': datetime.now().isoformat()}
            )
            self._sessions[session_id] = ctx
            return ctx
    
    def get_session(self, session_id: str) -> Optional[ConversationContext]:
        """获取会话"""
        return self._sessions.get(session_id)
    
    def delete_session(self, session_id: str):
        """删除会话"""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
    
    def list_sessions(self) -> List[str]:
        """列出所有会话ID"""
        return list(self._sessions.keys())

# 使用示例
if __name__ == "__main__":
    manager = SessionManager()
    
    # 创建两个独立会话
    session_a = manager.create_session("alice_assistant")
    session_b = manager.create_session("bob_tutor")
    
    # 各会话独立记忆
    session_a.variables['name'] = "Alice"
    session_b.variables['name'] = "Bob"
    
    print(f"Alice的会话变量: {session_a.variables}")
    print(f"Bob的会话变量: {session_b.variables}")
    # 输出:
    # Alice的会话变量: {'name': 'Alice'}
    # Bob的会话变量: {'name': 'Bob'}