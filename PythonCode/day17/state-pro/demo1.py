from datetime import datetime
from typing import Any, Dict, List

from guard import AIInferenceTask, LoggingObserver, MetricsObserver, Observer, ParallelStateMachine, PersistableState, StatePersistence, UIUpdateObserver


class EnterpriseGradingSystem:
    """
    企业级作业批改系统
    
    结合状态机、管道、观察者三种架构模式
    """
    
    def __init__(self, db_path: str = "grading_system.db"):
        # 状态机：管理任务状态
        self.task_states: Dict[str, ParallelStateMachine] = {}
        
        # 管道：处理流水线
        self.pipeline = Pipeline([
            SubmissionStage(),      # 接收阶段
            ParsingStage(),         # 解析阶段
            FeatureStage(),         # 特征提取
            AIGradingStage(),       # AI批改
            ReviewStage(),          # 审核阶段
            ReportStage()           # 报告生成
        ])
        
        # 观察者：通知系统
        self.observers: List[Observer] = [
            UIUpdateObserver(),
            LoggingObserver(),
            MetricsObserver()
        ]
        
        # 持久化
        self.persistence = StatePersistence(db_path)
        
        # AI客户端
        self.ai_client = AIInferenceTask(task_id="", model_name="qwen-plus")
    
    def submit_homework(self, user_id: str, homework_data: Dict) -> str:
        """提交作业"""
        task_id = f"task_{user_id}_{datetime.now().timestamp()}"
        
        # 创建状态机
        state_machine = ParallelStateMachine(task_id)
        state_machine.transition(
            "submit",
            states_to_add=["received", "pending_review"],
            context={"user_id": user_id, "homework_data": homework_data}
        )
        
        # 注册观察者
        for observer in self.observers:
            state_machine.add_listener(
                lambda tid, evt, states, obs=observer: obs.on_update(evt, {"task_id": tid, "states": states})
            )
        
        # 存储状态机
        self.task_states[task_id] = state_machine
        
        # 持久化状态
        persistable = PersistableState(
            task_id=task_id,
            current_state=state_machine.parallel_state.get_active_states()[0],
            active_states=state_machine.parallel_state.get_active_states(),
            context=state_machine.parallel_state.context,
            history=state_machine.history,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        self.persistence.save(persistable)
        
        return task_id
    
    async def process_task(self, task_id: str) -> Dict:
        """处理作业任务"""
        if task_id not in self.task_states:
            # 尝试从持久化恢复
            restored = self.persistence.restore_to_state_machine(task_id)
            if not restored:
                raise ValueError(f"任务不存在: {task_id}")
            self.task_states[task_id] = restored
        
        state_machine = self.task_states[task_id]
        
        # 更新状态
        state_machine.transition("start_processing", states_to_remove=["pending_review"])
        
        # 执行管道
        try:
            context = state_machine.parallel_state.context
            result = await self.pipeline.execute(context)
            
            # 完成
            state_machine.transition(
                "complete",
                states_to_remove=["running"],
                states_to_add=["completed", "notifying"]
            )
            
            return result
        
        except Exception as e:
            state_machine.transition("error", states_to_add=["failed"])
            raise


class Pipeline:
    """增强版管道，支持异步执行"""
    
    def __init__(self, stages: List[Any]):
        self.stages = stages
    
    async def execute(self, context: Dict) -> Dict:
        """异步执行管道"""
        for stage in self.stages:
            print(f"执行阶段: {stage.__class__.__name__}")
            if hasattr(stage, 'async_process'):
                result = await stage.async_process(context)
            else:
                result = stage.process(context)
            if result:
                context.update(result if isinstance(result, dict) else {"result": result})
        return context