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

import pickle
import sqlite3
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class PersistableState:
    """可持久化的状态数据"""
    task_id: str
    current_state: str
    active_states: List[str]
    context: Dict[str, Any]
    history: List[Dict]
    created_at: str
    updated_at: str
    version: int = 1


class StatePersistence:
    """
    状态持久化管理器
    
    iOS类比：类似UserDefaults存储应用状态
    支持SQLite持久化和内存缓存
    """
    
    def __init__(self, db_path: str = "state_machine.db"):
        self.db_path = db_path
        self._init_database()
        self._memory_cache: Dict[str, PersistableState] = {}
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_states (
                task_id TEXT PRIMARY KEY,
                state_data BLOB NOT NULL,
                version INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    
    def save(self, state: PersistableState) -> bool:
        """保存状态"""
        try:
            # 更新内存缓存
            self._memory_cache[state.task_id] = state
            
            # 序列化状态
            state_blob = pickle.dumps(asdict(state))
            
            # 保存到数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT OR REPLACE INTO task_states 
                (task_id, state_data, version, updated_at)
                VALUES (?, ?, ?, ?)
            """, (state.task_id, state_blob, state.version, now))
            
            conn.commit()
            conn.close()
            
            print(f"状态已保存: task_id={state.task_id}, version={state.version}")
            return True
        
        except Exception as e:
            print(f"状态保存失败: {e}")
            return False
    
    def load(self, task_id: str) -> Optional[PersistableState]:
        """加载状态"""
        # 先检查内存缓存
        if task_id in self._memory_cache:
            print(f"从内存缓存加载: {task_id}")
            return self._memory_cache[task_id]
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT state_data FROM task_states WHERE task_id = ?",
                (task_id,)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                state_dict = pickle.loads(row[0])
                state = PersistableState(**state_dict)
                
                # 加入内存缓存
                self._memory_cache[task_id] = state
                
                print(f"从数据库加载: {task_id}")
                return state
            
            return None
        
        except Exception as e:
            print(f"状态加载失败: {e}")
            return None
    
    def restore_to_state_machine(self, task_id: str) -> Optional[ParallelStateMachine]:
        """从持久化状态恢复到状态机"""
        state_data = self.load(task_id)
        
        if not state_data:
            return None
        
        # 创建新的状态机
        sm = ParallelStateMachine(task_id)
        
        # 恢复状态
        sm.parallel_state = ParallelState(
            states=state_data.active_states,
            context=state_data.context
        )
        
        # 恢复历史
        sm.history = state_data.history
        
        print(f"状态机已恢复: task_id={task_id}")
        return sm
    
class AIConversationStateMachine:
    """
    AI对话状态机
    
    深度结合多轮对话管理，支持：
    - 对话上下文追踪
    - 意图识别驱动的状态转换
    - 记忆管理与遗忘机制
    - 多轮澄清流程
    """
    
    class ConversationState(Enum):
        """对话状态"""
        GREETING = "greeting"           # 问候
        INTENT_DETECTION = "intent"     # 意图识别
        REQUIREMENT_GATHERING = "gather" # 需求收集
        PROCESSING = "processing"       # 处理中
        RESPONDING = "responding"       # 响应中
        CONFIRMATION = "confirm"         # 确认
        COMPLETED = "completed"          # 完成
        FAILED = "failed"               # 失败
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.current_state = self.ConversationState.GREETING
        self.context: Dict[str, Any] = {
            "intents": [],
            "entities": {},
            "missing_info": [],
            "conversation_turns": 0
        }
        self.conversation_history: List[Dict] = []
        self.max_turns = 10
    
    async def process_message(self, user_message: str) -> Dict[str, Any]:
        """处理用户消息并更新状态"""
        self.context["conversation_turns"] += 1
        
        # 记录对话历史
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
            "state": self.current_state.value,
            "timestamp": datetime.now().isoformat()
        })
        
        # 根据当前状态处理
        response = {"state": self.current_state.value}
        
        if self.current_state == self.ConversationState.GREETING:
            response = await self._handle_greeting(user_message)
        
        elif self.current_state == self.ConversationState.INTENT_DETECTION:
            response = await self._handle_intent_detection(user_message)
        
        elif self.current_state == self.ConversationState.REQUIREMENT_GATHERING:
            response = await self._handle_requirement_gathering(user_message)
        
        elif self.current_state == self.ConversationState.PROCESSING:
            response = await self._handle_processing(user_message)
        
        elif self.current_state == self.ConversationState.CONFIRMATION:
            response = await self._handle_confirmation(user_message)
        
        # 检查是否超过最大轮次
        if self.context["conversation_turns"] >= self.max_turns:
            self.current_state = self.ConversationState.FAILED
            response["fallback"] = "对话超时，请重新开始"
        
        # 记录AI响应
        if "response" in response:
            self.conversation_history.append({
                "role": "assistant",
                "content": response["response"],
                "state": self.current_state.value,
                "timestamp": datetime.now().isoformat()
            })
        
        response["context"] = self.context
        return response
    
    async def _handle_greeting(self, message: str) -> Dict[str, Any]:
        """处理问候"""
        self.current_state = self.ConversationState.INTENT_DETECTION
        return {
            "response": "您好！我是智能作业批改助手。请问有什么可以帮助您的？",
            "action": "wait_for_intent"
        }
    
    async def _handle_intent_detection(self, message: str) -> Dict[str, Any]:
        """处理意图识别"""
        # 使用通义千问识别意图
        try:
            detection_prompt = f"""分析以下用户消息的意图，只能选择一个最可能的意图：

消息："{message}"

可选意图：
1. submit_homework - 提交作业
2. check_progress - 查看批改进度
3. view_result - 查看批改结果
4. ask_question - 提问
5. get_help - 请求帮助
6. other - 其他

请只返回意图名称，不要其他内容。"""

            response = Generation.call(
                model="qwen-plus",
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                messages=[
                    {"role": "system", "content": "你是一个意图分类器"},
                    {"role": "user", "content": detection_prompt}
                ],
                result_format='message'
            )
            
            if response.status_code == 200:
                intent = response.output.choices[0].message.content.strip()
                self.context["detected_intent"] = intent
                self.context["intents"].append(intent)
                
                # 根据意图转换状态
                if intent == "submit_homework":
                    self.current_state = self.ConversationState.REQUIREMENT_GATHERING
                    return {
                        "response": f"好的，我识别到您想提交作业。请提供作业内容。",
                        "action": "wait_for_homework"
                    }
                elif intent == "view_result":
                    self.current_state = self.ConversationState.PROCESSING
                    return await self._fetch_and_respond_results(message)
                else:
                    self.current_state = self.ConversationState.PROCESSING
                    return await self._handle_processing(message)
            
        except Exception as e:
            print(f"意图识别失败: {e}")
        
        self.current_state = self.ConversationState.PROCESSING
        return {"response": "我明白了，让我帮您处理。", "action": "process"}
    
    async def _handle_requirement_gathering(self, message: str) -> Dict[str, Any]:
        """处理需求收集"""
        # 提取作业内容
        self.context["homework_content"] = message
        
        # 询问额外信息
        self.current_state = self.ConversationState.CONFIRMATION
        return {
            "response": f"已收到您的作业内容（{len(message)}字符）。\n\n请问这是数学作业还是语文作业？",
            "action": "wait_for_subject"
        }
    
    async def _handle_processing(self, message: str) -> Dict[str, Any]:
        """处理请求"""
        self.current_state = self.ConversationState.RESPONDING
        
        # 模拟处理
        return {
            "response": "正在为您处理，请稍候...",
            "action": "processing"
        }
    
    async def _handle_confirmation(self, message: str) -> Dict[str, Any]:
        """处理确认"""
        # 提取科目信息
        if "数学" in message:
            self.context["subject"] = "math"
        elif "语文" in message:
            self.context["subject"] = "chinese"
        
        self.current_state = self.ConversationState.COMPLETED
        return {
            "response": f"好的，已记录为{self.context.get('subject', '未指定')}作业。正在提交批改...",
            "action": "submit_for_grading"
        }
    
    async def _fetch_and_respond_results(self, message: str) -> Dict[str, Any]:
        """获取并返回结果"""
        return {
            "response": "让我帮您查找批改结果...",
            "action": "fetch_results"
        }
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import threading


class Observer(ABC):
    """观察者抽象基类"""
    
    @abstractmethod
    def on_update(self, event: str, data: Any):
        """接收更新通知"""
        pass


class InferenceProgressObserver(Observer):
    """推理进度观察者"""
    
    def __init__(self, name: str):
        self.name = name
    
    def on_update(self, event: str, data: Any):
        """处理推理进度更新"""
        if event == "progress":
            progress = data.get("progress", 0)
            stage = data.get("stage", "")
            print(f"[{self.name}] 进度更新: {stage} - {progress*100:.1f}%")
        elif event == "complete":
            print(f"[{self.name}] 推理完成: {data}")
        elif event == "error":
            print(f"[{self.name}] 推理错误: {data}")


class Observable:
    """
    可观察对象
    
    iOS类比：类似Combine的Publisher
    支持同步和异步通知
    """
    
    def __init__(self):
        self._observers: List[Observer] = []
        self._lock = threading.Lock()
    
    def attach(self, observer: Observer):
        """添加观察者"""
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)
                print(f"观察者已添加: {observer.name}")
    
    def detach(self, observer: Observer):
        """移除观察者"""
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)
                print(f"观察者已移除: {observer.name}")
    
    def notify(self, event: str, data: Any):
        """通知所有观察者"""
        with self._lock:
            observers_copy = self._observers.copy()
        
        for observer in observers_copy:
            try:
                observer.on_update(event, data)
            except Exception as e:
                print(f"通知观察者失败: {e}")


class AIInferenceTask(Observable):
    """
    AI推理任务（可观察对象）
    
    支持多阶段推理、进度通知、错误处理
    """
    
    def __init__(self, task_id: str, model_name: str = "qwen-plus"):
        super().__init__()
        self.task_id = task_id
        self.model_name = model_name
        self.state = "pending"
        self.progress = 0.0
        self.result: Optional[Dict] = None
        self.error: Optional[str] = None
    
    def set_progress(self, progress: float, stage: str = ""):
        """更新进度"""
        self.progress = progress
        self.notify("progress", {
            "task_id": self.task_id,
            "progress": progress,
            "stage": stage,
            "state": self.state
        })
    
    def start_inference(self, prompt: str) -> Dict:
        """开始推理"""
        self.state = "running"
        self.set_progress(0.1, "准备阶段")
        
        try:
            # 阶段1：Prompt预处理
            self.set_progress(0.2, "Prompt预处理")
            processed_prompt = self._preprocess_prompt(prompt)
            
            # 阶段2：API调用
            self.set_progress(0.4, "发送请求")
            response = self._call_api(processed_prompt)
            
            # 阶段3：响应解析
            self.set_progress(0.8, "解析响应")
            result = self._parse_response(response)
            
            # 完成
            self.set_progress(1.0, "完成")
            self.state = "completed"
            self.result = result
            
            self.notify("complete", {
                "task_id": self.task_id,
                "result": result
            })
            
            return result
        
        except Exception as e:
            self.state = "failed"
            self.error = str(e)
            self.notify("error", {
                "task_id": self.task_id,
                "error": str(e)
            })
            raise
    
    def _preprocess_prompt(self, prompt: str) -> str:
        """预处理Prompt"""
        # 模拟处理
        return prompt.strip()
    
    def _call_api(self, prompt: str) -> Generation:
        """调用通义千问API"""
        # 模拟API调用
        return Generation.call(
            model=self.model_name,
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            messages=[
                {"role": "user", "content": prompt}
            ],
            result_format='message'
        )
    
    def _parse_response(self, response) -> Dict:
        """解析响应"""
        if response.status_code == 200:
            return {
                "content": response.output.choices[0].message.content,
                "model": self.model_name,
                "task_id": self.task_id
            }
        else:
            raise Exception(f"API错误: {response.message}")