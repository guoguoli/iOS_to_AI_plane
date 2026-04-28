from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
import json


class PipelineStage(ABC):
    """
    管道阶段抽象基类
    
    iOS类比：类似Combine的Operator协议
    """
    
    @abstractmethod
    def process(self, data: Any, context: Dict[str, Any]) -> Any:
        """
        处理数据
        
        Args:
            data: 输入数据
            context: 共享上下文
        
        Returns:
            处理后的数据
        """
        pass

    
    @abstractmethod
    def get_name(self) -> str:
        """获取阶段名称"""
        pass


class PreprocessStage(PipelineStage):
    """预处理阶段"""
    
    def get_name(self) -> str:
        return "预处理"
    
    def process(self, data: Any, context: Dict[str, Any]) -> Any:
        """文本清洗和标准化"""
        if not isinstance(data, str):
            raise ValueError("输入必须是字符串")
        
        # 清理多余空格
        cleaned = ' '.join(data.split())
        
        # 标准化标点
        cleaned = cleaned.replace('，', ',').replace('。', '.')
        
        # 存储到上下文
        context['original_length'] = len(data)
        context['cleaned_length'] = len(cleaned)
        
        print(f"预处理: {len(data)} -> {len(cleaned)} 字符")
        return cleaned


class FeatureExtractionStage(PipelineStage):
    """特征提取阶段"""
    
    def get_name(self) -> str:
        return "特征提取"
    
    def process(self, data: Any, context: Dict[str, Any]) -> Any:
        """提取文本特征"""
        features = {
            'length': len(data),
            'sentence_count': data.count('.') + data.count('。') + 1,
            'word_count': len(data.split()),
            'has_code': '{' in data or 'function' in data,
            'difficulty': 'easy'  # 简化版
        }
        
        # 存储特征到上下文
        context['features'] = features
        
        print(f"特征提取: {features}")
        return data


class AIInferenceStage(PipelineStage):
    """AI推理阶段"""
    
    def __init__(self, model_name: str = 'qwen-plus'):
        self.model_name = model_name
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
    
    def get_name(self) -> str:
        return "AI批改"
    
    def process(self, data: Any, context: Dict[str, Any]) -> Any:
        """调用通义千问进行批改"""
        features = context.get('features', {})
        
        # 构建Prompt
        system_prompt = f"""你是一个专业的作业批改助手。请批改以下作业。

任务类型：{'代码题' if features.get('has_code') else '文本题'}
难度：{features.get('difficulty', 'unknown')}

请提供：
1. 评分（0-100分）
2. 具体反馈
3. 改进建议
4. 置信度（0-1之间）"""

        try:
            # 调用通义千问API
            response = Generation.call(
                model=self.model_name,
                api_key=self.api_key,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': data}
                ],
                result_format='message'
            )
            
            if response.status_code == 200:
                result = response.output.choices[0].message.content
                
                # 解析结果（简化版）
                inference_result = {
                    'raw_response': result,
                    'score': 85,  # 应该从结果中解析
                    'feedback': '完成良好',
                    'suggestions': '继续保持',
                    'confidence': 0.92
                }
                
                context['inference_result'] = inference_result
                print(f"AI批改完成: 评分 {inference_result['score']}")
                return inference_result
            else:
                raise Exception(f"API调用失败: {response.message}")
        
        except Exception as e:
            print(f"AI推理错误: {e}")
            raise


class PostprocessStage(PipelineStage):
    """后处理阶段"""
    
    def get_name(self) -> str:
        return "后处理"
    
    def process(self, data: Any, context: Dict[str, Any]) -> Any:
        """格式化输出结果"""
        inference_result = context.get('inference_result', {})
        features = context.get('features', {})
        
        # 生成最终报告
        report = {
            'task_id': context.get('task_id', 'unknown'),
            'timestamp': context.get('timestamp'),
            'score': inference_result.get('score', 0),
            'feedback': inference_result.get('feedback', ''),
            'suggestions': inference_result.get('suggestions', []),
            'confidence': inference_result.get('confidence', 0),
            'metrics': {
                'original_length': context.get('original_length', 0),
                'processing_time': context.get('processing_time', 0)
            }
        }
        
        print(f"报告生成完成: {json.dumps(report, ensure_ascii=False, indent=2)}")
        return report


class Pipeline:
    """
    管道类
    
    iOS类比：类似Combine的Publisher链
    """
    
    def __init__(self, stages: List[PipelineStage]):
        self.stages = stages
    
    def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        处理数据
        
        Args:
            input_data: 输入数据
            context: 共享上下文
        
        Returns:
            最终处理结果
        """
        if context is None:
            context = {}
        
        current_data = input_data
        
        for stage in self.stages:
            stage_name = stage.get_name()
            print(f"\n{'='*50}")
            print(f"执行阶段: {stage_name}")
            print('='*50)
            
            try:
                current_data = stage.process(current_data, context)
            except Exception as e:
                print(f"阶段 {stage_name} 执行失败: {e}")
                raise
        
        return current_data
    
    def add_stage(self, stage: PipelineStage, position: int = -1):
        """添加阶段"""
        if position == -1:
            self.stages.append(stage)
        else:
            self.stages.insert(position, stage)
    
    def remove_stage(self, stage_name: str):
        """移除阶段"""
        self.stages = [s for s in self.stages if s.get_name() != stage_name]