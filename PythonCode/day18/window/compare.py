"""
会话存储方案对比

对比三种常见的会话存储方案：
1. 内存存储（Memory）
2. SQLite本地存储
3. Redis分布式存储
"""

from abc import ABC, abstractmethod
from typing import Optional
import time

# ============ 存储接口定义 ============

class StorageBackend(ABC):
    """存储后端抽象接口"""
    
    @abstractmethod
    def save(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """保存数据"""
        pass
    
    @abstractmethod
    def load(self, key: str) -> Optional[str]:
        """加载数据"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除数据"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查是否存在"""
        pass


# ============ 内存存储实现 ============

class MemoryStorage(StorageBackend):
    """
    内存存储
    
    优点：
    - 读写速度极快
    - 实现简单
    
    缺点：
    - 数据不持久化，重启丢失
    - 无法跨进程/服务器共享
    - 内存占用随会话数增长
    
    适用场景：开发测试、单机部署、短期会话
    """
    
    def __init__(self):
        self._store: dict[str, tuple[str, Optional[float]]] = {}
    
    def save(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        expire_at = time.time() + ttl if ttl else None
        self._store[key] = (value, expire_at)
        return True
    
    def load(self, key: str) -> Optional[str]:
        if key not in self._store:
            return None
        
        value, expire_at = self._store[key]
        
        # 检查过期
        if expire_at and time.time() > expire_at:
            del self._store[key]
            return None
        
        return value
    
    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        return self.load(key) is not None


# ============ SQLite存储实现 ============

import sqlite3
import json

class SQLiteStorage(StorageBackend):
    """
    SQLite存储
    
    优点：
    - 数据持久化
    - 单文件，无需额外服务
    - 支持复杂查询
    - 跨平台
    
    缺点：
    - 并发写入有限制（但对会话场景足够）
    - 不适合超大规模分布式场景
    
    适用场景：中小型应用、需要持久化、单体或简单部署
    """
    
    def __init__(self, db_path: str = "sessions.db"):
        self.db_path = db_path
        self._init_table()
    
    def _init_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expire_at REAL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expire_at ON sessions(expire_at)
        """)
        conn.commit()
        conn.close()
    
    def save(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        expire_at = time.time() + ttl if ttl else None
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO sessions (key, value, expire_at) VALUES (?, ?, ?)",
            (key, value, expire_at)
        )
        conn.commit()
        conn.close()
        return True
    
    def load(self, key: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value, expire_at FROM sessions WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        value, expire_at = row
        
        # 检查过期
        if expire_at and time.time() > expire_at:
            self.delete(key)
            return None
        
        return value
    
    def delete(self, key: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE key = ?", (key,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    def exists(self, key: str) -> bool:
        return self.load(key) is not None


# ============ Redis存储实现 ============

class RedisStorage(StorageBackend):
    """
    Redis存储
    
    优点：
    - 高性能，支持海量会话
    - 支持分布式部署
    - 内置过期机制
    - 支持丰富的数据结构
    
    缺点：
    - 需要额外的Redis服务
    - 运维复杂度增加
    - 有连接成本
    
    适用场景：大规模应用、需要分布式部署、高并发场景
    """
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        # 注意：实际使用时需要 pip install redis
        # import redis
        # self._client = redis.Redis(host=host, port=port, db=db)
        self._client = None  # 简化示例，实际使用需要初始化
        self._host = host
        self._port = port
        self._db = db
    
    def save(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        # if self._client is None:
        #     import redis
        #     self._client = redis.Redis(host=self._host, port=self._port, db=self._db)
        # if ttl:
        #     self._client.setex(key, ttl, value)
        # else:
        #     self._client.set(key, value)
        return True  # 简化
    
    def load(self, key: str) -> Optional[str]:
        # if self._client is None:
        #     import redis
        #     self._client = redis.Redis(host=self._host, port=self._port, db=self._db)
        # return self._client.get(key)
        return None  # 简化
    
    def delete(self, key: str) -> bool:
        # if self._client:
        #     return bool(self._client.delete(key))
        return True
    
    def exists(self, key: str) -> bool:
        # if self._client:
        #     return bool(self._client.exists(key))
        return False


# ============ 存储方案对比表 ============

def print_comparison():
    """打印存储方案对比"""
    comparison = """
    ╔════════════════╦═══════════╦═══════════╦═══════════╗
    ║     维度        ║   内存    ║  SQLite   ║   Redis   ║
    ╠════════════════╬═══════════╬═══════════╬═══════════╣
    ║ 读写速度        ║   最快   ║    快    ║    快    ║
    ║ 数据持久化      ║    否    ║    是    ║    是    ║
    ║ 分布式支持      ║    否    ║    有限   ║    是    ║
    ║ 运维复杂度      ║    低    ║    低    ║    高    ║
    ║ 数据量上限      ║   内存   ║   磁盘   ║   内存   ║
    ║ 实现复杂度      ║    低    ║    中    ║    高    ║
    ╠════════════════╬═══════════╬═══════════╬═══════════╣
    ║ 开发测试        ║    ⭐    ║    ⭐    ║    ⭐    ║
    ║ 小型应用        ║    ⭐    ║   ⭐⭐   ║    ⭐    ║
    ║ 中型应用        ║    ❌    ║   ⭐⭐   ║   ⭐⭐   ║
    ║ 大型分布式      ║    ❌    ║    ❌    ║   ⭐⭐   ║
    ╚════════════════╩═══════════╩═══════════╩═══════════╝
    
    推荐选择：
    - 个人项目/学习：SQLite（无需配置，直接使用）
    - 小型产品：SQLite（稳定可靠）
    - 企业级应用：Redis（高并发+分布式）
    """
    print(comparison)


if __name__ == "__main__":
    print_comparison()
    
    # 测试内存存储
    memory = MemoryStorage()
    memory.save("test", "hello world", ttl=10)
    print(f"内存读取: {memory.load('test')}")
    
    # 测试SQLite存储
    sqlite_store = SQLiteStorage("test.db")
    sqlite_store.save("test", "hello from sqlite")
    print(f"SQLite读取: {sqlite_store.load('test')}")