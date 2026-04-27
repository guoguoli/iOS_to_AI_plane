import os
from typing import Dict, Callable, Any, Optional, List
from enum import Enum
import dashscope
from dashscope import Generation
from dotenv import load_dotenv

load_dotenv()

# 系统函数来源：通义千问API库
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")


class TaskState(Enum):
    """任务状态枚举
    
    iOS类比：类似Swift的enum
    """
    RECEIVED = "received"          # 已接收
    PARSING = "parsing"            # 解析中
    GRADING = "grading"            # 批改中
    REVIEWING = "reviewing"        # 审核中
    COMPLETED = "completed"        # 已完成
    FAILED = "failed"              # 失败


class GradingStateMachine:
    """
    作业批改状态机
    
    iOS类比：
    - 类似Combine的Operator链
    - 类似Coordinator的导航流程管理
    - 类似Redux的状态管理
    """
    
    def __init__(self):
        self.current_state = TaskState.RECEIVED
        self.state_history: List[TaskState] = []
        self.context: Dict[str, Any] = {}
        self.error: Optional[Exception] = None
        
        # 状态转换表
        self.transition_table = {
            TaskState.RECEIVED: {
                'start': self._on_start,
                'reject': self._on_reject
            },
            TaskState.PARSING: {
                'success': self._on_parse_success,
                'error': self._on_error
            },
            TaskState.GRADING: {
                'success': self._on_grading_success,
                'retry': self._on_retry,
                'error': self._on_error
            },
            TaskState.REVIEWING: {
                'approve': self._on_complete,
                'reject': self._on_reject
            },
            TaskState.COMPLETED: {},
            TaskState.FAILED: {
                'retry': self._on_start
            }
        }
    
    def transition(self, event: str, **kwargs) -> bool:
        """
        执行状态转换
        
        Args:
            event: 触发事件
            **kwargs: 传递给转换处理器的参数
        
        Returns:
            是否转换成功
        
        iOS类比：类似NotificationCenter.post(name:object:)
        """
        print(f"当前状态: {self.current_state.value}, 触发事件: {event}")
        
        # 记录历史
        self.state_history.append(self.current_state)
        
        # 获取当前状态的转换处理器
        transitions = self.transition_table.get(self.current_state, {})
        handler = transitions.get(event)
        
        if not handler:
            print(f"警告：状态 {self.current_state.value} 不支持事件 {event}")
            return False
        
        try:
            # 执行转换
            self.context.update(kwargs)
            new_state = handler(**kwargs)
            
            if new_state:
                self.current_state = new_state
                print(f"状态转换: {self.state_history[-1].value} -> {self.current_state.value}")
                return True
            
            return False
        except Exception as e:
            self.error = e
            print(f"状态转换失败: {e}")
            self.current_state = TaskState.FAILED
            return False
    
    # ==================== 状态转换处理器 ====================
    
    def _on_start(self, **kwargs) -> TaskState:
        """开始处理任务"""
        task_content = kwargs.get('task_content')
        
        # 验证任务内容
        if not task_content:
            raise ValueError("任务内容为空")
        
        # 进入解析状态
        return TaskState.PARSING
    
    def _on_reject(self, **kwargs) -> TaskState:
        """拒绝任务"""
        return TaskState.FAILED
    
    def _on_parse_success(self, **kwargs) -> TaskState:
        """解析成功"""
        parsed_data = kwargs.get('parsed_data')
        self.context['parsed_data'] = parsed_data
        return TaskState.GRADING
    
    def _on_error(self, **kwargs) -> TaskState:
        """处理错误"""
        error = kwargs.get('error', Exception("未知错误"))
        self.error = error
        return TaskState.FAILED
    
    def _on_grading_success(self, **kwargs) -> TaskState:
        """批改成功"""
        result = kwargs.get('result')
        self.context['result'] = result
        
        # 如果置信度高，直接完成
        confidence = result.get('confidence', 0)
        if confidence >= 0.9:
            return TaskState.COMPLETED
        else:
            # 否则进入审核状态
            return TaskState.REVIEWING
    
    def _on_retry(self, **kwargs) -> TaskState:
        """重试批改"""
        retry_count = self.context.get('retry_count', 0)
        if retry_count >= 3:
            raise Exception("重试次数超限")
        
        self.context['retry_count'] = retry_count + 1
        return TaskState.GRADING
    
    def _on_complete(self, **kwargs) -> TaskState:
        """完成任务"""
        return TaskState.COMPLETED
    
    # ==================== 辅助方法 ====================
    
    def get_current_state(self) -> TaskState:
        """获取当前状态"""
        return self.current_state
    
    def get_state_history(self) -> List[TaskState]:
        """获取状态历史"""
        return self.state_history
    
    def get_context(self) -> Dict[str, Any]:
        """获取上下文"""
        return self.context