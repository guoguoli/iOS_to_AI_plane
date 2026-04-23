import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dashscope import Generation
from dotenv import load_dotenv
import dashscope

load_dotenv()
 
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

class ConversationManager:
    """多轮对话管理器"""
    
    def __init__(self, session_id: str, max_tokens: int = 6000):
        """
        初始化对话管理器
        
        Args:
            session_id: 会话唯一标识（类似iOS的Thread ID）
            max_tokens: 最大上下文token数
        """
        self.session_id = session_id
        self.max_tokens = max_tokens
        self.conversation_file = f"conversations/{session_id}.json"
        
        # 确保目录存在
        os.makedirs("conversations", exist_ok=True)
        
        # 加载或初始化对话历史
        self.messages = self._load_history()
    
    def _load_history(self) -> List[Dict]:
        """加载对话历史"""
        if os.path.exists(self.conversation_file):
            with open(self.conversation_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_history(self):
        """保存对话历史到文件"""
        with open(self.conversation_file, 'w', encoding='utf-8') as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2)
    
    def add_message(self, role: str, content: str):
        """
        添加消息到对话历史
        
        Args:
            role: 'user' 或 'assistant'
            content: 消息内容
        """
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        self._save_history()
    
    def estimate_tokens(self) -> int:
        """
        估算当前上下文token数
        
        粗略估算：中文约2字符/token，英文约4字符/token
        实际API会根据具体分词计算
        """
        total_chars = sum(len(msg['content']) for msg in self.messages)
        # 粗略估算
        return total_chars // 3
    
    def trim_context(self, keep_last_n: int = 10):
        """
        修剪过长的上下文
        
        Args:
            keep_last_n: 保留最近N轮对话
        """
        if len(self.messages) > keep_last_n * 2:  # 每轮2条消息
            self.messages = self.messages[-keep_last_n * 2:]
            self._save_history()
    
    def chat(self, user_input: str) -> str:
        """发送消息并获取回复"""
        
        # 添加用户消息
        self.add_message('user', user_input)
        
        # 检查上下文长度
        current_tokens = self.estimate_tokens()
        if current_tokens > self.max_tokens:
            print(f"⚠️ 上下文过长({current_tokens} tokens)，自动修剪...")
            self.trim_context(keep_last_n=5)
        
        # 调用API
        response = Generation.call(
            model='qwen-turbo',
            messages=self.messages,
            result_format='message',
            stream=False  # 多轮对话可选择非流式
        )
        
        if response.status_code == 200:
            assistant_message = response.output.choices[0].message.content
            self.add_message('assistant', assistant_message)
            return assistant_message
        else:
            raise Exception(f"API调用失败: {response.code} - {response.message}")
    
    def get_summary(self) -> Dict:
        """获取对话摘要"""
        return {
            'session_id': self.session_id,
            'message_count': len(self.messages),
            'estimated_tokens': self.estimate_tokens(),
            'created_at': self.messages[0]['timestamp'] if self.messages else None,
            'last_message': self.messages[-1] if self.messages else None
        }

# 使用示例
if __name__ == "__main__":
    # 创建或恢复对话
    chat = ConversationManager(session_id="user_001_session_001")
    
    # 多轮对话
    chat.chat("我想学习Python")
    chat.chat("它和Swift有什么区别？")
    chat.chat("那Objective-C呢？")
    
    # 查看摘要
    # print(chat.get_summary())
    print(json.dumps(chat.get_summary(), ensure_ascii=False, indent=4, sort_keys=False))