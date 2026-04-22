"""
带重试机制的API调用封装

使用指数退避策略处理Rate Limit和临时错误

Reference:
    https://help.aliyun.com/zh/model-studio/developer-reference/use-qwen-by-calling-api
"""

import time
import random
from functools import wraps
from typing import Callable, Any
from dashscope import CallBackException

def with_retry(max_attempts: int = 3, base_delay: float = 1.0):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大尝试次数
        base_delay: 基础延迟时间（秒）
        
    iOS类比：Alamofire的RetryPolicy
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    error_str = str(e).lower()
                    
                    # 判断是否应该重试
                    should_retry = False
                    retry_message = ""
                    
                    # Rate Limit 错误
                    if "rate" in error_str or "429" in error_str:
                        should_retry = True
                        retry_message = "⏳ Rate Limit触发"
                    
                    # 超时错误
                    elif "timeout" in error_str or "timeout" in error_str:
                        should_retry = True
                        retry_message = "⏱️ 请求超时"
                    
                    # 服务器错误（5xx）
                    elif "500" in error_str or "503" in error_str or "internal" in error_str:
                        should_retry = True
                        retry_message = "🔧 服务器错误"
                    
                    # 不可重试的错误
                    if not should_retry:
                        print(f"❌ 不可重试的错误: {type(e).__name__}")
                        raise
                    
                    # 检查是否还有重试机会
                    if attempt >= max_attempts - 1:
                        print(f"❌ 达到最大重试次数 ({max_attempts})")
                        raise
                    
                    # 计算延迟时间（指数退避）
                    delay = min(
                        base_delay * (2 ** attempt),
                        60.0  # 最大延迟60秒
                    )
                    
                    # 添加随机抖动，避免多请求同时重试
                    delay *= random.uniform(1.0, 1.5)
                    
                    print(f"{retry_message}，{delay:.1f}s后重试 ({attempt + 1}/{max_attempts})...")
                    time.sleep(delay)
            
            # 所有重试都失败
            raise last_exception
        
        return wrapper
    return decorator

# ============ 使用示例 ============
@with_retry(max_attempts=3, base_delay=1.0)
def call_qwen_api(messages: list, model: str = "qwen-turbo"):
    """带重试的API调用"""
    import dashscope
    from dashscope import Generation
    
    dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
    
    response = Generation.call(
        model=model,
        messages=messages,
        result_format='message',
    )
    
    if response.status_code != 200:
        raise Exception(f"{response.code} - {response.message}")
    
    return response

# 使用
messages = [{"role": "user", "content": "成都的特产有哪些？"}]
response = call_qwen_api(messages)
print(response.output.choices[0].message.content)