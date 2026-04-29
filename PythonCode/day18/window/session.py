"""
会话管理器基础实现
使用dashscope通义千问API

功能特性：
- 消息历史管理
- 上下文窗口控制
- 自动摘要
"""

import os
import json
import uuid
import sqlite3
from datetime import datetime
from typing import Optional
from dashscope import Generation

from dotenv import load_dotenv

load_dotenv()


class ConversationManager:
    """
    会话管理器 - 管理多轮对话的上下文
    
    核心职责：
    1. 消息的添加、查询、删除
    2. 上下文窗口管理
    3. 会话持久化
    """
    
    def __init__(
        self,
        db_path: str = "conversations.db",
        max_context_messages: int = 20,
        enable_summary: bool = True,
        summary_threshold: int = 15
    ):
        """
        初始化会话管理器
        
        Args:
            db_path: SQLite数据库路径
            max_context_messages: 最大保留消息数
            enable_summary: 是否启用自动摘要
            summary_threshold: 触发摘要的消息数阈值
        """
        self.db_path = db_path
        self.max_context_messages = max_context_messages
        self.enable_summary = enable_summary
        self.summary_threshold = summary_threshold
        
        # 内存缓存：活跃会话的上下文
        self._active_contexts: dict[str, dict] = {}
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                summary TEXT,
                metadata TEXT
            )
        """)
        
        # 消息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_session(self, system_prompt: str = "你是一个有帮助的AI助手") -> str:
        """
        创建新会话
        
        Args:
            system_prompt: 系统提示词
            
        Returns:
            session_id: 新会话的唯一标识
        """
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # 保存到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (id, created_at, updated_at, metadata) VALUES (?, ?, ?, ?)",
            (session_id, now, now, json.dumps({"system_prompt": system_prompt}))
        )
        conn.commit()
        conn.close()
        
        # 初始化内存上下文
        self._active_contexts[session_id] = {
            "messages": [{"role": "system", "content": system_prompt}],
            "message_count": 0
        }
        
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str) -> str:
        """
        添加消息到会话
        
        Args:
            session_id: 会话ID
            role: 角色（user/assistant/system）
            content: 消息内容
            
        Returns:
            message_id: 消息ID
        """
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # 保存到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (id, conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
            (message_id, session_id, role, content, timestamp)
        )
        
        # 更新会话时间
        cursor.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (timestamp, session_id)
        )
        conn.commit()
        conn.close()
        
        # 更新内存上下文
        if session_id in self._active_contexts:
            self._active_contexts[session_id]["messages"].append({
                "role": role,
                "content": content
            })
            self._active_contexts[session_id]["message_count"] += 1
        
        return message_id
    
    def get_context(self, session_id: str) -> list[dict]:
        """
        获取会话上下文（带窗口管理）
        
        Args:
            session_id: 会话ID
            
        Returns:
            消息列表，可直接用于API调用
        """
        if session_id not in self._active_contexts:
            # 从数据库加载
            self._load_session_from_db(session_id)
        
        messages = self._active_contexts[session_id]["messages"]
        
        # 窗口管理：超过阈值时压缩
        if len(messages) > self.summary_threshold and self.enable_summary:
            # 实际项目中这里应该调用LLM生成摘要
            # 这里简化为滑动窗口
            messages = self._window_messages(messages)
            self._active_contexts[session_id]["messages"] = messages
        
        return messages
    
    def _window_messages(self, messages: list[dict]) -> list[dict]:
        """滑动窗口管理"""
        if len(messages) <= self.max_context_messages:
            return messages
        
        # 保留系统消息
        system_msgs = [m for m in messages if m["role"] == "system"]
        other_msgs = [m for m in messages if m["role"] != "system"]
        
        # 保留最近消息
        return system_msgs + other_msgs[-self.max_context_messages:]
    
    def _load_session_from_db(self, session_id: str):
        """从数据库加载会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取会话信息
        cursor.execute("SELECT metadata FROM conversations WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        
        if not row:
            raise ValueError(f"Session {session_id} not found")
        
        # 获取消息（按时间排序）
        cursor.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY timestamp",
            (session_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        # 构建上下文
        metadata = json.loads(row[0]) if row[0] else {}
        messages = [{"role": "system", "content": metadata.get("system_prompt", "")}] if metadata.get("system_prompt") else []
        messages += [{"role": r, "content": c} for r, c in rows]
        
        self._active_contexts[session_id] = {
            "messages": messages,
            "message_count": len(messages)
        }
    
    def chat(self, session_id: str, user_message: str, api_key: Optional[str] = None) -> str:
        """
        发送消息并获取AI响应
        
        Args:
            session_id: 会话ID
            user_message: 用户消息
            api_key: API密钥（如果未设置则从环境变量获取）
            
        Returns:
            assistant_response: AI的回复
        """
        if api_key is None:
            api_key = os.environ.get("DASHSCOPE_API_KEY")
        
        if not api_key:
            raise ValueError("需要提供DASHSCOPE_API_KEY")
        
        # 添加用户消息
        self.add_message(session_id, "user", user_message)
        
        # 获取当前上下文
        messages = self.get_context(session_id)
        
        # 调用API
        response = Generation.call(
            model="qwen-turbo",
            messages=messages,
            result_format="message",
            api_key=api_key
        )
        
        if response.status_code != 200:
            raise Exception(f"API调用失败: {response.message}")
        
        assistant_message = response.output.choices[0].message.content
        
        # 保存AI响应
        self.add_message(session_id, "assistant", assistant_message)
        
        return assistant_message


def demo():
    """演示会话管理器"""
    # 初始化（使用环境变量中的API Key）
    manager = ConversationManager(
        max_context_messages=10,
        enable_summary=True,
        summary_threshold=8
    )
    
    # 创建会话
    session_id = manager.create_session(
        system_prompt="你是一个专注于数学教育的AI老师，帮助学生学习代数和几何。"
    )
    print(f"创建会话: {session_id}")
    
    # 第一轮对话
    response = manager.chat(
        session_id,
        "什么是勾股定理？",
        api_key=os.environ.get("DASHSCOPE_API_KEY")
    )
    print(f"AI回复: {response}")
    
    # 第二轮对话（AI需要记住之前的上下文）
    response = manager.chat(
        session_id,
        "请给一个具体的例子",
        api_key=os.environ.get("DASHSCOPE_API_KEY")
    )
    print(f"AI回复: {response}")
    
    # 获取上下文信息
    context = manager.get_context(session_id)
    print(f"\n当前上下文包含 {len(context)} 条消息")
    
    return session_id


if __name__ == "__main__":
    # 注意：需要设置环境变量 DASHSCOPE_API_KEY
    # export DASHSCOPE_API_KEY="your-api-key"
    demo()