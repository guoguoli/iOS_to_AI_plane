# iOS风格的Token预算管理类比
class TokenBudgetManager:
    """
    iOS类比：这就像iOS的内存压力监测系统
    - 监控当前Token使用量
    - 达到阈值时触发清理
    - 优先保留重要上下文
    """
    
    def __init__(self, max_tokens=8000):
        self.max_tokens = max_tokens
        self.current_tokens = 0
        self.priority_contexts = []
    
    def add_context(self, context: str, priority: int = 1):
        """添加上下文，iOS的priority类似UIView的tag"""
        estimated_tokens = len(context) // 2
        if self.current_tokens + estimated_tokens > self.max_tokens:
            # 类似于didReceiveMemoryWarning
            self._trigger_cleanup()
        self.priority_contexts.append((priority, context))
        self.current_tokens += estimated_tokens
    
    def _trigger_cleanup(self):
        """触发清理，类似内存警告处理"""
        # 按优先级排序，移除低优先级上下文
        self.priority_contexts.sort(key=lambda x: x[0])
        while self.current_tokens > self.max_tokens * 0.7:
            if self.priority_contexts:
                _, removed = self.priority_contexts.pop(0)
                self.current_tokens -= len(removed) // 2
                
# iOS风格的缓存架构设计
class CacheStrategy:
    """
    iOS类比：结合NSCache和Core Data的缓存设计
    
    L1缓存（内存）：类似NSCache
    - 自动管理内存
    - 线程安全
    - 低延迟
    
    L2缓存（磁盘）：类似Core Data
    - 持久化存储
    - 支持复杂查询
    - 跨会话复用
    """
    
    L1_CACHE_MAX_SIZE = 1000  # 内存缓存最大条数
    L2_CACHE_MAX_SIZE = 10000  # 磁盘缓存最大条数
    DEFAULT_TTL = 3600  # 默认过期时间（秒）
    
    def __init__(self):
        # L1缓存 - 类似NSCache
        self.l1_cache = {}  # 简单实现，实际用NSCache
        self.l1_access_order = []
        
        # L2缓存 - 类似Core Data
        self.l2_cache = {}  # 实际用Core Data存储
    
    def set(self, key: str, value: dict, ttl: int = None):
        """存储缓存，iOS的setObject:forKey:"""
        ttl = ttl or self.DEFAULT_TTL
        expire_time = time.time() + ttl
        
        # L1缓存
        self.l1_cache[key] = {'value': value, 'expire': expire_time}
        self.l1_access_order.append(key)
        self._trim_l1_cache()
        
        # L2缓存持久化
        self.l2_cache[key] = {'value': value, 'expire': expire_time}
        self._trim_l2_cache()
    
    def get(self, key: str):
        """获取缓存"""
        now = time.time()
        
        # 优先L1
        if key in self.l1_cache:
            entry = self.l1_cache[key]
            if entry['expire'] > now:
                # 更新访问顺序，类似LRU
                self.l1_access_order.remove(key)
                self.l1_access_order.append(key)
                return entry['value']
            else:
                del self.l1_cache[key]
        
        # 降级L2
        if key in self.l2_cache:
            entry = self.l2_cache[key]
            if entry['expire'] > now:
                # 回填L1
                self.set(key, entry['value'], int(entry['expire'] - now))
                return entry['value']
            else:
                del self.l2_cache[key]
        
        return None
    
    def _trim_l1_cache(self):
        """修剪L1缓存，类似NSCache的自动清理"""
        while len(self.l1_cache) > self.L1_CACHE_MAX_SIZE:
            oldest = self.l1_access_order.pop(0)
            if oldest in self.l1_cache:
                del self.l1_cache[oldest]
from collections import defaultdict
import datetime
import time
# iOS风格的API监控系统
class APIMonitor:
    """
    iOS类比：类似Xcode的Instruments工具
    
    功能对应：
    - Time Profiler → 延迟监控
    - Memory Debugger → Token使用监控
    - Network Link Conditioner → API可用性监控
    """
    
    def __init__(self):
        # 指标存储 - 类似Instruments的记录
        self.metrics = {
            'total_calls': 0,
            'total_tokens_in': 0,
            'total_tokens_out': 0,
            'total_cost': 0.0,
            'total_latency': 0.0,
            'errors': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # 按时间聚合 - 类似Instruments的时间线视图
        self.hourly_stats = defaultdict(lambda: {
            'calls': 0, 'tokens': 0, 'cost': 0.0, 'errors': 0
        })
        
        # 告警配置
        self.alert_config = {
            'daily_cost_limit': 100.0,
            'error_rate_threshold': 0.05,
            'latency_threshold': 10.0,
            'daily_call_limit': 10000
        }
        
        self.alerts = []
    
    def record_call(self, model: str, tokens_in: int, tokens_out: int,
                   latency: float, success: bool, cache_hit: bool = False):
        """记录API调用，类似Instruments的数据采集"""
        self.metrics['total_calls'] += 1
        self.metrics['total_tokens_in'] += tokens_in
        self.metrics['total_tokens_out'] += tokens_out
        self.metrics['total_latency'] += latency
        
        # 成本计算
        cost = self._calculate_cost(model, tokens_in, tokens_out)
        self.metrics['total_cost'] += cost
        
        # 缓存统计
        if cache_hit:
            self.metrics['cache_hits'] += 1
        else:
            self.metrics['cache_misses'] += 1
        
        # 错误记录
        if not success:
            self.metrics['errors'] += 1
        
        # 时间聚合
        hour_key = time.strftime('%Y-%m-%d %H:00')
        self.hourly_stats[hour_key]['calls'] += 1
        self.hourly_stats[hour_key]['tokens'] += tokens_in + tokens_out
        self.hourly_stats[hour_key]['cost'] += cost
        self.hourly_stats[hour_key]['errors'] += 1 if not success else 0
        
        # 检查告警
        self._check_alerts(hour_key, cost)
    
    def _calculate_cost(self, model: str, tokens_in: int, tokens_out: int) -> float:
        """计算调用成本"""
        pricing = {
            'qwen-turbo': (0.002, 0.006),
            'qwen-plus': (0.02, 0.06),
            'qwen-max': (0.10, 0.30)
        }
        if model not in pricing:
            return 0.0
        
        input_price, output_price = pricing[model]
        return (tokens_in * input_price + tokens_out * output_price) / 1000
    
    def _check_alerts(self, hour_key: str, cost: float):
        """检查告警条件，类似Instruments的告警标记"""
        alerts = []
        
        # 检查日成本
        today_cost = sum(h['cost'] for h in self.hourly_stats.values() 
                        if h['cost'] > 0)
        if today_cost > self.alert_config['daily_cost_limit']:
            alerts.append(('CRITICAL', f'日成本超限: {today_cost:.2f}元'))
        
        # 检查错误率
        if self.metrics['total_calls'] > 0:
            error_rate = self.metrics['errors'] / self.metrics['total_calls']
            if error_rate > self.alert_config['error_rate_threshold']:
                alerts.append(('WARNING', f'错误率过高: {error_rate:.2%}'))
        
        # 检查平均延迟
        if self.metrics['total_calls'] > 0:
            avg_latency = self.metrics['total_latency'] / self.metrics['total_calls']
            if avg_latency > self.alert_config['latency_threshold']:
                alerts.append(('WARNING', f'平均延迟过高: {avg_latency:.2f}秒'))
        
        if alerts:
            self.alerts.extend(alerts)
            print(f"[ALERT] {'; '.join([a[1] for a in alerts])}")
    
    def get_report(self) -> dict:
        """生成监控报告，类似Instruments的导出功能"""
        cache_total = self.metrics['cache_hits'] + self.metrics['cache_misses']
        cache_hit_rate = (self.metrics['cache_hits'] / cache_total * 100 
                         if cache_total > 0 else 0)
        
        avg_latency = (self.metrics['total_latency'] / self.metrics['total_calls'] 
                      if self.metrics['total_calls'] > 0 else 0)
        
        return {
            '概览': {
                '总调用次数': self.metrics['total_calls'],
                '总成本': f"{self.metrics['total_cost']:.4f}元",
                '缓存命中率': f"{cache_hit_rate:.2f}%",
                '平均延迟': f"{avg_latency:.3f}秒",
                '错误数': self.metrics['errors']
            },
            'Token统计': {
                '输入Token': self.metrics['total_tokens_in'],
                '输出Token': self.metrics['total_tokens_out'],
                '总Token': self.metrics['total_tokens_in'] + self.metrics['total_tokens_out']
            },
            '告警列表': [a[1] for a in self.alerts[-10:]]  # 最近10条
        }

# iOS App Thinning风格的AI成本优化
class CostOptimizer:
    """
    iOS类比：App Thinning（应用瘦身）的AI版本
    
    App Thinning技术 → AI成本优化：
    - Bitcode（优化编译）→ Token压缩
    - On-Demand Resources（按需资源）→ 智能模型选择
    - Slice（应用切片）→ 缓存复用
    """
    
    # 模型配置 - 类似App的资源变体
    MODEL_CONFIG = {
        'simple': {'model': 'qwen-turbo', 'max_tokens': 2000},
        'normal': {'model': 'qwen-plus', 'max_tokens': 4000},
        'complex': {'model': 'qwen-max', 'max_tokens': 8000}
    }
    
    def __init__(self):
        self.monitor = APIMonitor()
        self.cache = SemanticCache()
        self.budget_manager = BudgetManager()
    
    def select_model(self, task_complexity: str) -> str:
        """智能选择模型，类似按需加载资源"""
        # 检查预算
        if not self.budget_manager.can_spend():
            # 降级到便宜模型
            return 'qwen-turbo'
        
        return self.MODEL_CONFIG.get(task_complexity, 'normal')['model']
    
    def optimize_request(self, prompt: str, context: str = "") -> dict:
        """优化请求，类似App的资源压缩"""
        original_length = len(prompt)
        
        # 1. 移除冗余空格和换行
        optimized = ' '.join(prompt.split())
        
        # 2. 压缩上下文
        if context and len(context) > 3000:
            context = context[:3000] + "...(已压缩)"
        
        # 3. 估算Token
        estimated_tokens = len(optimized) // 2 + len(context) // 2
        
        return {
            'prompt': optimized,
            'context': context,
            'original_length': original_length,
            'optimized_length': len(optimized),
            'estimated_tokens': estimated_tokens,
            'compression_rate': f"{(1 - len(optimized)/original_length)*100:.1f}%"
        }
    
    def batch_optimize(self, requests: list) -> list:
        """批量优化，类似App的批处理优化"""
        if len(requests) <= 3:
            # 少于3个单独处理
            return [self.optimize_request(r) for r in requests]
        
        # 合并为单个请求
        combined_prompt = "\n---\n".join([
            f"任务{i+1}: {r}" for i, r in enumerate(requests)
        ])
        
        # 优化合并后的请求
        return [self.optimize_request(combined_prompt)]


class BudgetManager:
    """
    预算管理器，类似iOS的家长控制/屏幕使用时间
    
    功能：
    - 设置每日/每周限额
    - 追踪使用情况
    - 自动限制超支
    """
    
    def __init__(self, daily_limit: float = 100.0):
        self.daily_limit = daily_limit
        self.daily_spent = 0.0
        self.last_reset = datetime.date.today()
    
    def can_spend(self, amount: float = 1.0) -> bool:
        """检查是否可以消费"""
        today = datetime.date.today()
        if today > self.last_reset:
            # 新的一天，重置预算
            self.daily_spent = 0.0
            self.last_reset = today
        
        return (self.daily_spent + amount) <= self.daily_limit
    
    def record_spend(self, amount: float):
        """记录消费"""
        self.daily_spent += amount
    
    def get_remaining(self) -> dict:
        """获取剩余预算"""
        return {
            'daily_limit': self.daily_limit,
            'spent': self.daily_spent,
            'remaining': self.daily_limit - self.daily_spent,
            'usage_rate': f"{(self.daily_spent/self.daily_limit)*100:.1f}%"
        }