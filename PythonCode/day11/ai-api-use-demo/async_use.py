import asyncio
import aiohttp
from typing import List, Dict

async def batch_chat_completion(
    prompts: List[str],
    model: str = "qwen-turbo",
    max_concurrent: int = 3
) -> List[str]:
    """
    批量异步调用通义千问API
    
    使用信号量控制并发数，避免触发Rate Limit
    
    Args:
        prompts: 提示词列表
        model: 模型名称
        max_concurrent: 最大并发数
        
    Returns:
        响应列表
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def call_api(prompt: str) -> str:
        async with semaphore:  # 控制并发
            async with aiohttp.ClientSession() as session:
                # 实现带重试的API调用
                for attempt in range(3):
                    try:
                        async with session.post(
                            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {os.getenv('DASHSCOPE_API_KEY')}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": model,
                                "messages": [{"role": "user", "content": prompt}]
                            },
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as response:
                            if response.status == 429:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            data = await response.json()
                            return data["choices"][0]["message"]["content"]
                    except Exception as e:
                        if attempt == 2:
                            return f"Error: {str(e)}"
                        await asyncio.sleep(2 ** attempt)
    
    # 并发执行所有请求
    tasks = [call_api(prompt) for prompt in prompts]
    results = await asyncio.gather(*tasks)
    
    return list(results)