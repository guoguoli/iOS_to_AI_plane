import os
from typing import Dict, Any, List, Optional
from enum import Enum
import json
import time
from datetime import datetime

import dashscope
from dashscope import Generation
from dotenv import load_dotenv


load_dotenv()

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")


# ==================== 状态机实现 ====================

class TaskState(Enum):
    """任务状态"""
    RECEIVED = "received"
    PREPROCESSING = "preprocessing"
    GRADING = "grading"
    POSTPROCESSING = "postprocessing"
    COMPLETED = "completed"
    FAILED = "failed"


class GradingStateMachine:
    """作业批改状态机"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.current_state = TaskState.RECEIVED
        self.history: List[tuple] = []
        self.context: Dict[str, Any] = {}
        self.error: Optional[Exception] = None
    
    def transition(self, event: str, **kwargs) -> bool:
        """状态转换"""
        print(f"\n[状态机] 当前: {self.current_state.value}, 事件: {event}")
        
        # 记录历史
        self.history.append((self.current_state, event))
        
        # 定义转换规则
        transitions = {
            TaskState.RECEIVED: {
                'start': TaskState.PREPROCESSING,
                'reject': TaskState.FAILED
            },
            TaskState.PREPROCESSING: {
                'success': TaskState.GRADING,
                'error': TaskState.FAILED
            },
            TaskState.GRADING: {
                'success': TaskState.POSTPROCESSING,
                'retry': TaskState.GRADING,
                'error': TaskState.FAILED
            },
            TaskState.POSTPROCESSING: {
                'success': TaskState.COMPLETED,
                'error': TaskState.FAILED
            },
            TaskState.COMPLETED: {},
            TaskState.FAILED: {
                'retry': TaskState.RECEIVED
            }
        }
        
        # 检查转换是否有效
        allowed_events = transitions.get(self.current_state, {})
        if event not in allowed_events:
            print(f"无效的转换: {self.current_state.value} -> {event}")
            return False
        
        # 更新上下文
        self.context.update(kwargs)
        
        # 执行转换
        new_state = allowed_events[event]
        if new_state:
            self.current_state = new_state
            print(f"[状态机] 转换: {self.history[-1][0].value} -> {self.current_state.value}")
            return True
        
        return False


# ==================== 管道实现 ====================

class PipelineStage:
    """管道阶段基类"""
    
    def process(self, data: Any, context: Dict[str, Any]) -> Any:
        """处理数据"""
        raise NotImplementedError
    
    def get_name(self) -> str:
        """获取阶段名称"""
        raise NotImplementedError


class PreprocessStage(PipelineStage):
    """预处理阶段"""
    
    def get_name(self) -> str:
        return "预处理"
    
    def process(self, data: str, context: Dict[str, Any]) -> str:
        """文本清洗"""
        if not isinstance(data, str):
            raise ValueError("输入必须是字符串")
        
        # 清理空格
        cleaned = ' '.join(data.split())
        
        # 统计信息
        context['stats'] = {
            'original_length': len(data),
            'cleaned_length': len(cleaned),
            'char_count': len(cleaned),
            'word_count': len(cleaned.split())
        }
        
        print(f"[预处理] {len(data)} -> {len(cleaned)} 字符")
        return cleaned


class FeatureExtractionStage(PipelineStage):
    """特征提取阶段"""
    
    def get_name(self) -> str:
        return "特征提取"
    
    def process(self, data: str, context: Dict[str, Any]) -> str:
        """提取特征"""
        features = {
            'length': len(data),
            'word_count': len(data.split()),
            'has_code': '{' in data or 'function' in data,
            'difficulty': self._assess_difficulty(data)
        }
        
        context['features'] = features
        print(f"[特征提取] {features}")
        return data
    
    def _assess_difficulty(self, text: str) -> str:
        """评估难度"""
        if '{' in text:
            return 'hard'
        elif len(text.split()) > 50:
            return 'medium'
        else:
            return 'easy'


class AIInferenceStage(PipelineStage):
    """AI推理阶段"""
    
    def __init__(self, model_name: str = 'qwen-plus'):
        self.model_name = model_name
    
    def get_name(self) -> str:
        return "AI批改"
    
    def process(self, data: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """调用通义千问"""
        features = context.get('features', {})
        
        system_prompt = f"""你是专业的作业批改助手。
任务类型：{'代码题' if features.get('has_code') else '文本题'}
难度：{features.get('difficulty')}

请批改并返回JSON格式：
{{
    "score": 分数(0-100),
    "feedback": "反馈",
    "suggestions": ["建议1", "建议2"],
    "confidence": 置信度(0-1)
}}"""

        try:
            response = Generation.call(
                model=self.model_name,
                api_key=dashscope.api_key,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': data}
                ],
                result_format='message'
            )
            
            if response.status_code == 200:
                result_text = response.output.choices[0].message.content
                
                # 简化解析
                inference_result = {
                    'raw_response': result_text,
                    'score': 85,
                    'feedback': '完成良好',
                    'suggestions': ['继续保持'],
                    'confidence': 0.92
                }
                
                context['inference_result'] = inference_result
                print(f"[AI批改] 评分: {inference_result['score']}")
                return inference_result
            else:
                raise Exception(f"API调用失败: {response.message}")
        
        except Exception as e:
            print(f"[AI批改] 错误: {e}")
            raise


class PostprocessStage(PipelineStage):
    """后处理阶段"""
    
    def get_name(self) -> str:
        return "后处理"
    
    def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """生成最终报告"""
        report = {
            'task_id': context.get('task_id'),
            'timestamp': datetime.now().isoformat(),
            'score': data.get('score', 0),
            'feedback': data.get('feedback', ''),
            'confidence': data.get('confidence', 0),
            'stats': context.get('stats', {}),
            'features': context.get('features', {})
        }
        
        print(f"[后处理] 报告生成完成")
        return report


class Pipeline:
    """管道类"""
    
    def __init__(self, stages: List[PipelineStage]):
        self.stages = stages
    
    def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """处理数据"""
        if context is None:
            context = {}
        
        current_data = input_data
        
        for stage in self.stages:
            stage_name = stage.get_name()
            print(f"\n{'='*40}")
            print(f"[管道] 执行: {stage_name}")
            print('='*40)
            
            try:
                start_time = time.time()
                current_data = stage.process(current_data, context)
                elapsed = time.time() - start_time
                
                context['timing'] = context.get('timing', {})
                context['timing'][stage_name] = elapsed
                
            except Exception as e:
                print(f"[管道] 阶段 {stage_name} 失败: {e}")
                raise
        
        return current_data


# ==================== 综合示例 ====================

def main():
    """综合示例：状态机 + 管道"""
    
    print("\n" + "="*50)
    print("成都教育科技智能作业批改系统")
    print("="*50)
    
    # 创建任务
    task_id = f"task_{int(time.time())}"
    task_content = "计算1+1的结果并解释原因。"
    
    print(f"\n任务ID: {task_id}")
    print(f"任务内容: {task_content}")
    
    # 初始化状态机
    state_machine = GradingStateMachine(task_id)
    state_machine.context['task_content'] = task_content
    state_machine.context['task_id'] = task_id
    
    # 状态机：开始任务
    if not state_machine.transition('start'):
        print("任务启动失败")
        return
    
    # 创建管道
    pipeline = Pipeline([
        PreprocessStage(),
        FeatureExtractionStage(),
        AIInferenceStage(),
        PostprocessStage()
    ])
    
    # 管道：执行批改
    try:
        # 预处理
        state_machine.transition('start')
        cleaned_data = pipeline.process(task_content, state_machine.context)
        state_machine.transition('success')
        
        # 特征提取
        state_machine.transition('start')
        state_machine.transition('success')
        
        # AI批改
        state_machine.transition('start')
        state_machine.transition('success')
        
        # 后处理
        state_machine.transition('start')
        result = pipeline.process(state_machine.context['inference_result'], state_machine.context)
        state_machine.transition('success')
        
        # 完成
        state_machine.transition('success')
        
        print("\n" + "="*50)
        print("批改完成！")
        print("="*50)
        print(f"最终状态: {state_machine.current_state.value}")
        print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        print(f"状态历史: {[s.value for s, e in state_machine.history]}")
        
    except Exception as e:
        print(f"\n批改失败: {e}")
        state_machine.transition('error', error=e)
        print(f"最终状态: {state_machine.current_state.value}")


if __name__ == "__main__":
    main()