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