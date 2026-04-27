import os
import time
import hashlib
import json
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, Dict, Any, List, Tuple

import dashscope
from dashscope import Generation
from dashscope.common import _message_state
from dashscope.api_entities import GenerationRequest

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")


class TokenCounter:
    """
    Token计数器
    
    iOS类比：这就像iOS的内存占用分析器
    - 精确计算每个文本块的Token数
    - 估算调用成本
    - 提供优化建议
    """
    
    # 通义千问模型的Token估算比率
    CHARS_PER_TOKEN_CHINESE = 1.5  # 中文平均每Token字符数
    CHARS_PER_TOKEN_ENGLISH = 4.0  # 英文平均每Token字符数
    
    # 价格表（元/千Token）
    PRICING = {
        'qwen-turbo': {'input': 0.002, 'output': 0.006},
        'qwen-plus': {'input': 0.02, 'output': 0.06},
        'qwen-max': {'input': 0.10, 'output': 0.30}
    }
    
    def __init__(self):
        self.total_tokens = 0
        self.total_cost = 0.0
    
    def count_tokens(self, text: str) -> int:
        """
        估算Token数量
        
        使用简单的字符统计：
        - 中文：每1.5个字符约1个Token
        - 英文：每4个字符约1个Token
        """
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_chars = len(text) - chinese_chars
        
        return int(chinese_chars / self.CHARS_PER_TOKEN_CHINESE + 
                  english_chars / self.CHARS_PER_TOKEN_ENGLISH)
    
    def estimate_cost(self, model: str, input_tokens: int, 
                     output_tokens: int) -> float:
        """
        估算调用成本
        
        成本 = (输入Token数 × 输入单价 + 输出Token数 × 输出单价) / 1000
        """
        if model not in self.PRICING:
            return 0.0
        
        pricing = self.PRICING[model]
        cost = (input_tokens * pricing['input'] + 
                output_tokens * pricing['output']) / 1000
        
        self.total_tokens += input_tokens + output_tokens
        self.total_cost += cost
        
        return cost
    
    def estimate_cost_from_text(self, model: str, 
                               input_text: str, 
                               output_text: str = "") -> dict:
        """
        从文本直接估算成本
        
        返回包含详细信息的字典
        """
        input_tokens = self.count_tokens(input_text)
        output_tokens = self.count_tokens(output_text)
        cost = self.estimate_cost(model, input_tokens, output_tokens)
        
        return {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'estimated_cost': cost,
            'cost_breakdown': f"输入: {input_tokens} tokens ({input_tokens * self.PRICING.get(model, {}).get('input', 0):.6f}元), "
                              f"输出: {output_tokens} tokens ({output_tokens * self.PRICING.get(model, {}).get('output', 0):.6f}元)"
        }
    
    def optimize_prompt(self, prompt: str) -> dict:
        """
        返回Prompt优化建议
        
        iOS类比：这就像Instruments的内存优化建议
        """
        current_tokens = self.count_tokens(prompt)
        suggestions = []
        
        # 检查点1：长度分析
        if current_tokens > 4000:
            suggestions.append("⚠️ Token数量较高，建议精简Prompt")
        
        # 检查点2：重复内容
        words = prompt.split()
        if len(words) != len(set(words)):
            suggestions.append("💡 检测到重复词语，可合并或去除")
        
        # 检查点3：标点符号
        if prompt.count('。') > 50 or prompt.count(',') > 50:
            suggestions.append("💡 标点符号过多，可适当精简")
        
        # 检查点4：空白字符
        if '  ' in prompt or '\n\n\n' in prompt:
            suggestions.append("💡 检测到多余空白，建议清理")
        
        # 检查点5：英文占比
        english_ratio = sum(1 for c in prompt if c.isascii()) / len(prompt) if prompt else 0
        if english_ratio > 0.5:
            suggestions.append("💡 英文占比较高，注意Token消耗")
        
        # 优化后的估算
        optimized = ' '.join(prompt.split())
        optimized_tokens = self.count_tokens(optimized)
        
        return {
            'original_tokens': current_tokens,
            'optimized_tokens': optimized_tokens,
            'saved_tokens': current_tokens - optimized_tokens,
            'suggestions': suggestions,
            'optimized_prompt': optimized if suggestions else prompt
        }


class SemanticCache:
    """
    语义缓存系统
    
    iOS类比：这就像iOS的照片库智能搜索
    - 不仅缓存完全匹配的内容
    - 还支持语义相似的内容复用
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.cache: Dict[str, dict] = {}
        self.vectors: Dict[str, List[float]] = {}
        self.similarity_threshold = similarity_threshold
        self.stats = {'hits': 0, 'misses': 0, 'saves': 0}
    
    def _simple_hash(self, text: str) -> str:
        """简单哈希用于精确匹配"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _simple_vectorize(self, text: str, dim: int = 10) -> List[float]:
        """
        简单向量化（实际生产应使用 embedding API）
        
        这里使用字符频率作为简易向量
        """
        # 统计字符频率
        char_freq = defaultdict(int)
        for c in text:
            if c.isalnum():
                char_freq[c.lower()] += 1
        
        # 转换为固定维度向量
        vector = [0.0] * dim
        chars = list(char_freq.keys())[:dim]
        for i, c in enumerate(chars):
            vector[i] = char_freq[c] / max(len(text), 1)
        
        return vector
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def set(self, query: str, response: dict, ttl: int = 3600):
        """存储问答对"""
        key = self._simple_hash(query)
        self.cache[key] = {
            'query': query,
            'response': response,
            'timestamp': time.time(),
            'ttl': ttl,
            'access_count': 0
        }
        self.vectors[key] = self._simple_vectorize(query)
        self.stats['saves'] += 1
    
    def get(self, query: str) -> Optional[dict]:
        """
        获取缓存
        
        支持精确匹配和语义相似匹配
        """
        # 1. 精确匹配
        exact_key = self._simple_hash(query)
        if exact_key in self.cache:
            entry = self.cache[exact_key]
            if self._is_valid(entry):
                entry['access_count'] += 1
                self.stats['hits'] += 1
                return entry['response']
        
        # 2. 语义相似匹配
        query_vector = self._simple_vectorize(query)
        best_match = None
        best_similarity = 0.0
        
        for key, cached_vector in self.vectors.items():
            if key == exact_key:
                continue
            
            similarity = self._cosine_similarity(query_vector, cached_vector)
            if similarity >= self.similarity_threshold:
                entry = self.cache[key]
                if self._is_valid(entry) and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = entry
        
        if best_match:
            best_match['access_count'] += 1
            self.stats['hits'] += 1
            result = best_match['response'].copy()
            result['_cache_hit'] = True
            result['_similarity'] = best_similarity
            return result
        
        self.stats['misses'] += 1
        return None
    
    def _is_valid(self, entry: dict) -> bool:
        """检查缓存是否有效"""
        age = time.time() - entry['timestamp']
        return age < entry['ttl']
    
    def get_cache_stats(self) -> dict:
        """获取缓存统计"""
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
        
        # 访问频率统计
        access_counts = [e['access_count'] for e in self.cache.values()]
        
        return {
            'total_cached': len(self.cache),
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': f"{hit_rate:.2f}%",
            'total_saves': self.stats['saves'],
            'avg_access': sum(access_counts) / len(access_counts) if access_counts else 0,
            'max_access': max(access_counts) if access_counts else 0
        }
    
    def clear_expired(self):
        """清理过期缓存"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if not self._is_valid(entry)
        ]
        for key in expired_keys:
            del self.cache[key]
            if key in self.vectors:
                del self.vectors[key]
        
        return len(expired_keys)


class APIMonitor:
    """
    API调用监控器
    
    iOS类比：这就像Instruments的Allocations工具
    - 追踪所有API调用
    - 统计资源消耗
    - 告警异常情况
    """
    
    def __init__(self, daily_cost_limit: float = 100.0):
        self.records: List[dict] = []
        self.daily_limit = daily_cost_limit
        self.daily_cost = 0.0
        self.last_reset = datetime.now().date()
        self.alerts: List[dict] = []
    
    def record_call(self, model: str, tokens_in: int, tokens_out: int,
                   latency: float, success: bool):
        """记录一次API调用"""
        # Token计数器
        counter = TokenCounter()
        cost = counter.estimate_cost(model, tokens_in, tokens_out)
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'total_tokens': tokens_in + tokens_out,
            'cost': cost,
            'latency': latency,
            'success': success
        }
        
        self.records.append(record)
        self.daily_cost += cost
        
        # 检查告警
        self._check_alerts(record)
        
        return record
    
    def _check_alerts(self, record: dict):
        """检查是否触发告警"""
        # 成本告警
        if self.daily_cost > self.daily_limit:
            self.alerts.append({
                'type': 'COST_LIMIT',
                'level': 'CRITICAL',
                'message': f'日成本超限: {self.daily_cost:.2f}元 > {self.daily_limit}元',
                'time': datetime.now().isoformat()
            })
        
        # 延迟告警
        if record['latency'] > 10.0:
            self.alerts.append({
                'type': 'HIGH_LATENCY',
                'level': 'WARNING',
                'message': f'响应延迟过高: {record["latency"]:.2f}秒',
                'time': datetime.now().isoformat()
            })
        
        # 错误告警
        if not record['success']:
            self.alerts.append({
                'type': 'API_ERROR',
                'level': 'ERROR',
                'message': f'API调用失败: model={record["model"]}',
                'time': datetime.now().isoformat()
            })
    
    def get_daily_stats(self) -> dict:
        """获取每日统计"""
        today = datetime.now().date()
        
        # 重置每日成本计数
        if today > self.last_reset:
            self.daily_cost = 0.0
            self.last_reset = today
        
        today_records = [r for r in self.records 
                         if datetime.fromisoformat(r['timestamp']).date() == today]
        
        if not today_records:
            return {
                'date': str(today),
                'total_calls': 0,
                'total_tokens': 0,
                'total_cost': 0.0,
                'avg_latency': 0.0,
                'success_rate': '100%'
            }
        
        total_calls = len(today_records)
        total_tokens = sum(r['total_tokens'] for r in today_records)
        total_cost = sum(r['cost'] for r in today_records)
        avg_latency = sum(r['latency'] for r in today_records) / total_calls
        success_count = sum(1 for r in today_records if r['success'])
        
        return {
            'date': str(today),
            'total_calls': total_calls,
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'avg_latency': avg_latency,
            'success_rate': f"{(success_count/total_calls)*100:.2f}%",
            'daily_limit': self.daily_limit,
            'budget_usage': f"{(total_cost/self.daily_limit)*100:.2f}%"
        }
    
    def check_alerts(self) -> List[dict]:
        """获取所有未处理的告警"""
        return self.alerts[-10:]  # 返回最近10条


class CostController:
    """
    成本控制器
    
    iOS类比：这就像iOS的家长控制/屏幕时间管理
    - 控制每日/每周支出
    - 用户配额管理
    - 自动降级策略
    """
    
    def __init__(self, daily_limit: float = 100.0):
        self.daily_limit = daily_limit
        self.daily_spent = 0.0
        self.user_quotas: Dict[str, dict] = {}
        self.last_reset = datetime.now().date()
        
        # 模型优先级
        self.model_priority = ['qwen-max', 'qwen-plus', 'qwen-turbo']
    
    def set_budget(self, daily_limit: float):
        """设置日预算"""
        self.daily_limit = daily_limit
    
    def set_user_quota(self, user_id: str, daily_limit: float, 
                      monthly_limit: float = None):
        """设置用户配额"""
        self.user_quotas[user_id] = {
            'daily_limit': daily_limit,
            'daily_used': 0.0,
            'monthly_limit': monthly_limit,
            'monthly_used': 0.0
        }
    
    def can_call(self, model: str, estimated_tokens: int, 
                user_id: str = None) -> Tuple[bool, str]:
        """
        检查是否可以调用API
        
        返回：(是否允许, 原因)
        """
        # 检查每日预算
        today = datetime.now().date()
        if today > self.last_reset:
            self.daily_spent = 0.0
            self.last_reset = today
        
        # 估算成本
        counter = TokenCounter()
        cost = counter.estimate_cost(model, estimated_tokens, 0)
        
        if self.daily_spent + cost > self.daily_limit:
            return False, f"日预算超限: {self.daily_spent + cost:.4f} > {self.daily_limit}"
        
        # 检查用户配额
        if user_id and user_id in self.user_quotas:
            quota = self.user_quotas[user_id]
            if quota['daily_used'] + cost > quota['daily_limit']:
                return False, f"用户配额超限"
        
        return True, "允许调用"
    
    def get_remaining_budget(self) -> dict:
        """获取剩余预算"""
        return {
            'daily_limit': self.daily_limit,
            'daily_spent': self.daily_spent,
            'daily_remaining': self.daily_limit - self.daily_spent,
            'usage_percentage': f"{self.daily_spent/self.daily_limit*100:.2f}%"
        }
    
    def select_optimal_model(self, task_complexity: str, 
                           estimated_tokens: int) -> Tuple[str, bool]:
        """
        选择最优模型
        
        返回：(选择的模型, 是否需要降级)
        """
        # 根据复杂度选择模型
        complexity_model_map = {
            'simple': 'qwen-turbo',
            'normal': 'qwen-plus',
            'complex': 'qwen-max'
        }
        
        preferred_model = complexity_model_map.get(task_complexity, 'qwen-plus')
        
        # 检查是否允许使用首选模型
        can_use, reason = self.can_call(preferred_model, estimated_tokens)
        
        if can_use:
            return preferred_model, False
        
        # 需要降级
        for model in self.model_priority:
            if model == preferred_model:
                continue
            can_use, _ = self.can_call(model, estimated_tokens)
            if can_use:
                return model, True
        
        return 'qwen-turbo', True


def optimize_api_call(prompt: str, model: str = 'qwen-plus',
                     use_cache: bool = True) -> dict:
    """
    优化的API调用函数
    
    整合所有优化组件的完整调用流程
    """
    # 初始化组件
    counter = TokenCounter()
    cache = SemanticCache()
    monitor = APIMonitor()
    controller = CostController()
    
    result = {
        'original_prompt': prompt,
        'steps': []
    }
    
    # Step 1: Token计数和成本估算
    token_result = counter.estimate_cost_from_text(model, prompt)
    result['steps'].append({
        'step': 'token_analysis',
        'data': token_result
    })
    
    # Step 2: Prompt优化
    optimize_result = counter.optimize_prompt(prompt)
    result['steps'].append({
        'step': 'prompt_optimization',
        'data': optimize_result
    })
    
    # Step 3: 缓存检查
    if use_cache:
        cached = cache.get(prompt)
        if cached:
            result['steps'].append({
                'step': 'cache_hit',
                'data': cached
            })
            result['final_response'] = cached
            result['cost_saved'] = token_result['estimated_cost']
            return result
    
    # Step 4: 成本检查
    can_proceed, reason = controller.can_call(
        model, token_result['input_tokens'])
    
    result['steps'].append({
        'step': 'budget_check',
        'data': {'allowed': can_proceed, 'reason': reason}
    })
    
    if not can_proceed:
        result['error'] = 'Budget exceeded'
        return result
    
    # Step 5: API调用（实际调用需要API密钥）
    # response = call_qwen_api(optimize_result['optimized_prompt'], model)
    
    # Step 6: 记录监控
    # monitor.record_call(model, tokens_in, tokens_out, latency, success)
    
    return result
class EducationGradingOptimizer:
    """
    教育科技智能批改系统成本优化器
    
    成都教育科技场景实战
    """
    
    def __init__(self, daily_budget: float = 500.0):
        self.counter = TokenCounter()
        self.cache = SemanticCache(similarity_threshold=0.85)
        self.monitor = APIMonitor(daily_cost_limit=daily_budget)
        self.controller = CostController(daily_limit=daily_budget)
        
        # 教育场景特定配置
        self.subject_cache_ttl = {
            'math': 86400,      # 数学：24小时
            'chinese': 172800,  # 语文：48小时
            'english': 172800   # 英语：48小时
        }
    
    def optimize_grading_prompt(self, student_answer: dict) -> str:
        """
        优化批改Prompt
        
        原始格式：详细的富文本描述
        优化格式：简洁的结构化数据
        """
        # 简化题目描述
        simplified_items = []
        for item in student_answer.get('items', []):
            question = item['question']
            answer = item['student_answer']
            
            # 标准化格式
            simplified = f"[{question} → {answer}]"
            simplified_items.append(simplified)
        
        return ', '.join(simplified_items)
    
    def grade_homework(self, homework_data: dict, 
                      user_id: str) -> dict:
        """
        智能批改核心方法
        
        整合所有优化策略
        """
        start_time = time.time()
        
        result = {
            'homework_id': homework_data.get('id'),
            'student_id': homework_data.get('student_id'),
            'items': [],
            'summary': {}
        }
        
        # Step 1: 优化Prompt
        optimized_prompt = self.optimize_grading_prompt(homework_data)
        
        # Step 2: Token分析
        token_info = self.counter.estimate_cost_from_text(
            'qwen-plus', optimized_prompt)
        
        # Step 3: 成本检查
        can_proceed, reason = self.controller.can_call(
            'qwen-plus', token_info['input_tokens'], user_id)
        
        if not can_proceed:
            return {
                'error': 'QUOTA_EXCEEDED',
                'message': f'用户{user_id}今日配额已用完',
                'suggestion': '请明天再来或联系老师'
            }
        
        # Step 4: 缓存检查
        cache_result = self.cache.get(optimized_prompt)
        
        if cache_result:
            result['items'] = cache_result.get('items', [])
            result['from_cache'] = True
            result['cost'] = 0.0
        else:
            # Step 5: API调用（实际实现需要API密钥）
            # response = self._call_grading_api(optimized_prompt)
            
            # 模拟API响应
            response = {
                'items': [
                    {'correct': True, 'score': 10, 'feedback': '正确'}
                    for _ in homework_data.get('items', [])
                ],
                'total_score': len(homework_data.get('items', [])) * 10
            }
            
            result['items'] = response['items']
            result['from_cache'] = False
            result['cost'] = token_info['estimated_cost']
            
            # Step 6: 存储缓存
            self.cache.set(optimized_prompt, response, 
                          ttl=self.subject_cache_ttl.get('math', 86400))
        
        # Step 7: 计算汇总
        correct_count = sum(1 for item in result['items'] if item.get('correct'))
        total_count = len(result['items'])
        
        result['summary'] = {
            'correct': correct_count,
            'total': total_count,
            'accuracy': f"{(correct_count/total_count*100) if total_count > 0 else 0:.1f}%",
            'processing_time': f"{time.time() - start_time:.3f}秒",
            'cached': result.get('from_cache', False)
        }
        
        # Step 8: 记录监控
        self.monitor.record_call(
            model='qwen-plus',
            tokens_in=token_info['input_tokens'],
            tokens_out=token_info['output_tokens'],
            latency=time.time() - start_time,
            success=True
        )
        
        return result
    
    def get_cost_report(self, user_id: str = None) -> dict:
        """获取成本报告"""
        daily_stats = self.monitor.get_daily_stats()
        cache_stats = self.cache.get_cache_stats()
        budget_status = self.controller.get_remaining_budget()
        
        report = {
            '日期': daily_stats['date'],
            'API调用统计': {
                '总调用次数': daily_stats['total_calls'],
                '总Token消耗': daily_stats['total_tokens'],
                '总成本': f"{daily_stats['total_cost']:.4f}元",
                '平均延迟': f"{daily_stats['avg_latency']:.3f}秒"
            },
            '缓存统计': {
                '命中率': cache_stats['hit_rate'],
                '节省成本': f"约{cache_stats['hits'] * 0.01:.2f}元（按平均成本估算）"
            },
            '预算状态': {
                '日预算': f"{budget_status['daily_limit']:.2f}元",
                '已使用': f"{budget_status['daily_spent']:.2f}元",
                '剩余': f"{budget_status['daily_remaining']:.2f}元",
                '使用率': budget_status['usage_percentage']
            }
        }
        
        # 添加告警信息
        alerts = self.monitor.check_alerts()
        if alerts:
            report['告警'] = alerts
        
        return report


# 使用示例
def demo_grading_system():
    """演示智能批改系统"""
    optimizer = EducationGradingOptimizer(daily_budget=500.0)
    
    # 模拟作业数据
    homework = {
        'id': 'HW20240115001',
        'student_id': 'STU001',
        'subject': 'math',
        'items': [
            {'question': '12+8=?', 'student_answer': '20'},
            {'question': '15-7=?', 'student_answer': '8'},
            {'question': '3×4=?', 'student_answer': '12'},
            {'question': '20÷5=?', 'student_answer': '4'}
        ]
    }
    
    # 执行批改
    result = optimizer.grade_homework(homework, user_id='STU001')
    
    print("批改结果：")
    print(f"正确: {result['summary']['correct']}/{result['summary']['total']}")
    print(f"正确率: {result['summary']['accuracy']}")
    print(f"处理时间: {result['summary']['processing_time']}")
    print(f"来自缓存: {result['summary']['cached']}")
    
    # 获取成本报告
    report = optimizer.get_cost_report()
    print("\n成本报告：")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    demo_grading_system()