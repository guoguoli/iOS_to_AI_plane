from typing import Dict, Any, Callable, Optional, List
from enum import Enum
import os
import json
from datetime import datetime
import dashscope
from dashscope import Generation
from dotenv import load_dotenv

load_dotenv()

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")


class ConditionType(Enum):
    """条件类型"""
    AND = "and"           # 逻辑与
    OR = "or"             # 逻辑或
    NOT = "not"           # 逻辑非
    XOR = "xor"           # 异或


class GuardCondition:
    """
    守卫条件
    
    iOS类比：类似Combine的filter操作符
    用于在状态转换前进行条件检查
    """
    
    def __init__(self, name: str, check_fn: Callable[[Dict], bool], error_message: str = ""):
        """
        Args:
            name: 条件名称
            check_fn: 检查函数，接收上下文返回bool
            error_message: 条件不满足时的错误信息
        """
        self.name = name
        self.check_fn = check_fn
        self.error_message = error_message
    
    def evaluate(self, context: Dict[str, Any]) -> tuple[bool, str]:
        """评估条件是否满足"""
        try:
            result = self.check_fn(context)
            if result:
                return True, ""
            else:
                return False, self.error_message or f"条件 {self.name} 不满足"
        except Exception as e:
            return False, f"条件评估错误: {e}"


class ComplexTransition:
    """
    复杂状态转换
    
    支持多条件组合、守卫条件、转换前/后回调
    """
    
    def __init__(
        self,
        from_state: str,
        to_state: str,
        event: str,
        conditions: Optional[List[GuardCondition]] = None,
        condition_type: ConditionType = ConditionType.AND,
        pre_callback: Optional[Callable] = None,
        post_callback: Optional[Callable] = None
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.event = event
        self.conditions = conditions or []
        self.condition_type = condition_type
        self.pre_callback = pre_callback
        self.post_callback = post_callback
    
    def can_transition(self, context: Dict[str, Any]) -> tuple[bool, str]:
        """检查是否可以转换"""
        if not self.conditions:
            return True, ""
        
        results = []
        for condition in self.conditions:
            result, error = condition.evaluate(context)
            results.append(result)
        
        # 根据条件类型组合结果
        if self.condition_type == ConditionType.AND:
            can_pass = all(results)
        elif self.condition_type == ConditionType.OR:
            can_pass = any(results)
        elif self.condition_type == ConditionType.XOR:
            can_pass = sum(results) == 1
        else:
            can_pass = all(results)
        
        if can_pass:
            return True, ""
        
        failed_conditions = [
            c.name for c, r in zip(self.conditions, results) if not r
        ]
        return False, f"条件未满足: {', '.join(failed_conditions)}"

class ParallelState:
    """
    并行状态
    
    iOS类比：类似Swift的TaskGroup，允许并发执行
    """
    
    def __init__(self, states: List[str], context: Dict[str, Any]):
        self.states = set(states)
        self.context = context
        self.entered_at = datetime.now()
    
    def add_state(self, state: str):
        """添加活跃状态"""
        self.states.add(state)
    
    def remove_state(self, state: str):
        """移除状态"""
        self.states.discard(state)
    
    def is_active(self, state: str) -> bool:
        """检查状态是否活跃"""
        return state in self.states
    
    def get_active_states(self) -> List[str]:
        """获取所有活跃状态"""
        return list(self.states)


class ParallelStateMachine:
    """
    并行状态机
    
    允许任务同时处于多个状态
    """
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.parallel_state = ParallelState(["idle"], {})
        self.history: List[Dict] = []
        self.listeners: List[Callable] = []
    
    def transition(self, event: str, states_to_add: List[str] = None,
                   states_to_remove: List[str] = None, context: Dict = None) -> bool:
        """执行并行状态转换"""
        print(f"\n[并行状态机] 事件: {event}")
        print(f"  之前状态: {self.parallel_state.get_active_states()}")
        
        # 记录历史
        self.history.append({
            "event": event,
            "before": self.parallel_state.get_active_states(),
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        })
        
        # 执行状态变更
        if states_to_add:
            for state in states_to_add:
                self.parallel_state.add_state(state)
        
        if states_to_remove:
            for state in states_to_remove:
                self.parallel_state.remove_state(state)
        
        # 更新上下文
        if context:
            self.parallel_state.context.update(context)
        
        print(f"  之后状态: {self.parallel_state.get_active_states()}")
        
        # 通知监听器
        self._notify_listeners(event)
        
        return True
    
    def _notify_listeners(self, event: str):
        """通知所有监听器"""
        for listener in self.listeners:
            try:
                listener(self.task_id, event, self.parallel_state.get_active_states())
            except Exception as e:
                print(f"监听器通知失败: {e}")
    
    def add_listener(self, listener: Callable):
        """添加状态变化监听器"""
        self.listeners.append(listener)