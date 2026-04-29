from datetime import datetime
import os
import asyncio
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
import dashscope
from dashscope import Generation
import json

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")


# ==================== 状态机核心 ====================

class DialogState(Enum):
    """对话状态"""
    IDLE = "idle"
    GREETING = "greeting"
    INTENT_PARSING = "intent_parsing"
    SLOT_FILLING = "slot_filling"
    EXECUTING = "executing"
    CONFIRMING = "confirming"
    RESPONDING = "responding"
    CLOSING = "closing"
    ERROR = "error"


class DialogEvent(Enum):
    """对话事件"""
    USER_MESSAGE = "user_message"
    INTENT_DETECTED = "intent_detected"
    SLOTS_FILLED = "slots_filled"
    EXECUTION_COMPLETE = "execution_complete"
    USER_CONFIRM = "user_confirm"
    USER_REJECT = "user_reject"
    EXECUTION_FAILED = "execution_failed"
    TIMEOUT = "timeout"
    RESET = "reset"


@dataclass
class DialogContext:
    """对话上下文"""
    user_id: str
    session_id: str
    current_intent: Optional[str] = None
    slots: Dict[str, Any] = None
    history: List[Dict] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.slots is None:
            self.slots = {}
        if self.history is None:
            self.history = []


class MultiTurnDialogStateMachine:
    """
    多轮对话状态机
    
    完整实现一个智能作业批改的对话系统
    """
    
    # 状态转换规则
    TRANSITIONS = {
        DialogState.IDLE: {
            DialogEvent.USER_MESSAGE: DialogState.GREETING
        },
        DialogState.GREETING: {
            DialogEvent.INTENT_DETECTED: DialogState.INTENT_PARSING
        },
        DialogState.INTENT_PARSING: {
            DialogEvent.INTENT_DETECTED: DialogState.SLOT_FILLING,
            DialogEvent.EXECUTION_FAILED: DialogState.ERROR
        },
        DialogState.SLOT_FILLING: {
            DialogEvent.SLOTS_FILLED: DialogState.EXECUTING,
            DialogEvent.EXECUTION_FAILED: DialogState.ERROR
        },
        DialogState.EXECUTING: {
            DialogEvent.EXECUTION_COMPLETE: DialogState.CONFIRMING,
            DialogEvent.EXECUTION_FAILED: DialogState.ERROR
        },
        DialogState.CONFIRMING: {
            DialogEvent.USER_CONFIRM: DialogState.RESPONDING,
            DialogEvent.USER_REJECT: DialogState.SLOT_FILLING
        },
        DialogState.RESPONDING: {
            DialogEvent.EXECUTION_COMPLETE: DialogState.CLOSING
        },
        DialogState.CLOSING: {
            DialogEvent.USER_MESSAGE: DialogState.GREETING,
            DialogEvent.RESET: DialogState.IDLE
        },
        DialogState.ERROR: {
            DialogEvent.RESET: DialogState.IDLE
        }
    }
    
    def __init__(self, context: DialogContext):
        self.context = context
        self.current_state = DialogState.IDLE
        self.transition_history: List[tuple] = []
    
    def can_transition(self, event: DialogEvent) -> bool:
        """检查是否可以转换"""
        allowed_events = self.TRANSITIONS.get(self.current_state, {})
        return event in allowed_events
    
    def transition(self, event: DialogEvent) -> Optional[DialogState]:
        """执行状态转换"""
        if not self.can_transition(event):
            print(f"警告：状态 {self.current_state.value} 不支持事件 {event.value}")
            return None
        
        old_state = self.current_state
        new_state = self.TRANSITIONS[self.current_state][event]
        
        self.current_state = new_state
        self.transition_history.append((old_state, event, new_state))
        
        print(f"状态转换: {old_state.value} → {event.value} → {new_state.value}")
        return new_state
    
    def get_required_slots(self, intent: str) -> List[str]:
        """获取意图所需的槽位"""
        slot_templates = {
            "submit_homework": ["content", "subject", "grade"],
            "query_result": ["task_id"],
            "get_help": ["help_type"]
        }
        return slot_templates.get(intent, [])
    
    def is_slots_filled(self, intent: str) -> bool:
        """检查槽位是否已填充"""
        required = self.get_required_slots(intent)
        return all(slot in self.context.slots for slot in required)


class DialogManager:
    """
    对话管理器
    
    协调状态机和AI模型
    """
    
    def __init__(self, user_id: str, session_id: str):
        self.context = DialogContext(user_id=user_id, session_id=session_id)
        self.state_machine = MultiTurnDialogStateMachine(self.context)
        self.ai_model = "qwen-plus"
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """处理用户消息"""
        # 添加到历史
        self.context.history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # 根据当前状态处理
        response_text = ""
        action = None
        
        if self.state_machine.current_state == DialogState.IDLE:
            self.state_machine.transition(DialogEvent.USER_MESSAGE)
            response_text = "您好！我是智能作业批改助手。请问有什么可以帮助您的？"
            self.state_machine.transition(DialogEvent.INTENT_DETECTED)
        
        elif self.state_machine.current_state == DialogState.INTENT_PARSING:
            intent, slots = await self._parse_intent(message)
            self.context.current_intent = intent
            self.context.slots.update(slots)
            
            if self.state_machine.is_slots_filled(intent):
                self.state_machine.transition(DialogEvent.SLOTS_FILLED)
                action = "execute_intent"
            else:
                missing = self._get_missing_slots(intent)
                response_text = self._generate_slot_prompt(intent, missing)
        
        elif self.state_machine.current_state == DialogState.SLOT_FILLING:
            # 提取槽位
            extracted = await self._extract_slots(message)
            self.context.slots.update(extracted)
            
            if self.state_machine.is_slots_filled(self.context.current_intent):
                self.state_machine.transition(DialogEvent.SLOTS_FILLED)
                action = "execute_intent"
            else:
                missing = self._get_missing_slots(self.context.current_intent)
                response_text = self._generate_slot_prompt(self.context.current_intent, missing)
        
        elif self.state_machine.current_state == DialogState.EXECUTING:
            response_text, action = await self._execute_intent()
        
        elif self.state_machine.current_state == DialogState.CONFIRMING:
            response_text = "操作已完成。请问还有其他需要帮助的吗？"
            self.state_machine.transition(DialogEvent.USER_CONFIRM)
        
        elif self.state_machine.current_state == DialogState.CLOSING:
            self.state_machine.transition(DialogEvent.USER_MESSAGE)
            response_text = "好的，再见！有需要随时找我。"
        
        elif self.state_machine.current_state == DialogState.ERROR:
            response_text = f"遇到了一些问题：{self.context.slots.get('error', '未知错误')}"
            response_text += "\n让我重新帮您。"
            self.state_machine.transition(DialogEvent.RESET)
        
        # 添加AI响应到历史
        self.context.history.append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "response": response_text,
            "action": action,
            "state": self.state_machine.current_state.value,
            "context": {
                "intent": self.context.current_intent,
                "slots": self.context.slots
            }
        }
    
    async def _parse_intent(self, message: str) -> tuple[str, Dict]:
        """解析用户意图"""
        prompt = f"""分析用户消息，识别意图并提取信息。

用户消息：{message}

可选意图：
1. submit_homework - 提交作业
2. query_result - 查询批改结果
3. get_help - 获取帮助
4. other - 其他

请以JSON格式返回：
{{"intent": "意图", "slots": {{"槽位": "值"}}}}"""

        try:
            response = Generation.call(
                model=self.ai_model,
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                messages=[
                    {"role": "system", "content": "你是一个意图分类助手"},
                    {"role": "user", "content": prompt}
                ],
                result_format='message'
            )
            
            if response.status_code == 200:
                result_text = response.output.choices[0].message.content
                # 简化解析
                if "submit_homework" in result_text:
                    return "submit_homework", {"content": message}
                elif "query_result" in result_text:
                    return "query_result", {}
                else:
                    return "get_help", {}
        
        except Exception as e:
            print(f"意图解析失败: {e}")
        
        return "other", {}
    
    async def _extract_slots(self, message: str) -> Dict:
        """提取槽位"""
        # 简化实现
        return {"content": message}
    
    def _get_missing_slots(self, intent: str) -> List[str]:
        """获取缺失的槽位"""
        required = self.state_machine.get_required_slots(intent)
        missing = [s for s in required if s not in self.context.slots]
        return missing
    
    def _generate_slot_prompt(self, intent: str, missing_slots: List[str]) -> str:
        """生成槽位填充提示"""
        prompts = {
            "submit_homework": {
                "subject": "请问这是哪个科目的作业？（数学/语文/英语/其他）",
                "grade": "请问是几年级的作业？",
                "content": "请提供作业内容"
            }
        }
        
        if missing_slots and intent in prompts:
            next_slot = missing_slots[0]
            return prompts[intent].get(next_slot, f"请提供{next_slot}")
        
        return "请提供更多信息"
    
    async def _execute_intent(self) -> tuple[str, str]:
        """执行意图"""
        intent = self.context.current_intent
        
        if intent == "submit_homework":
            self.state_machine.transition(DialogEvent.EXECUTION_COMPLETE)
            return f"作业已提交，正在批改中...\n内容长度：{len(self.context.slots.get('content', ''))}字符", "grading"
        
        elif intent == "query_result":
            self.state_machine.transition(DialogEvent.EXECUTION_COMPLETE)
            return "找到最近的批改结果：得分85分，详见报告。", "show_result"
        
        else:
            self.state_machine.transition(DialogEvent.EXECUTION_COMPLETE)
            return "已收到您的请求，正在处理中...", "process"


# ==================== 测试代码 ====================

async def test_dialog_manager():
    """测试对话管理器"""
    print("=" * 60)
    print("多轮对话状态机测试")
    print("=" * 60)
    
    manager = DialogManager(user_id="user_001", session_id="session_001")
    
    # 模拟对话流程
    messages = [
        "我想提交作业",
        "这是数学作业",
        "1+1=2"
    ]
    
    for msg in messages:
        print(f"\n用户: {msg}")
        result = await manager.process_message(msg)
        print(f"助手: {result['response']}")
        print(f"状态: {result['state']}")
        print(f"意图: {result['context'].get('intent')}")


if __name__ == "__main__":
    asyncio.run(test_dialog_manager())