"""
文心一言 API 调用示例（可选备选模型）

来源：erniebot库
文档：https://cloud.baidu.com/doc/wenxinworkshop/s/Clnt6u51x
"""

import erniebot
import os
from dotenv import load_dotenv

load_dotenv()

# 设置API Key
erniebot.api_key = os.getenv("ERNIE_API_KEY")

def ernie_chat(
    messages: list,
    model: str = "ernie-4.0",
    max_tokens: int = 1024
) -> dict:
    """
    文心一言聊天补全函数
    """
    try:
        response = erniebot.ChatCompletion.create(
            model=model,
            messages=messages,
            max_output_tokens=max_tokens,
        )
        
        return {
            "content": response.result,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            }
        }
        
    except Exception as e:
        return {"error": str(e), "content": None}

# ============ 使用示例 ============
if __name__ == "__main__":
    messages = [
        {
            "role": "user",
            "content": "用一句话解释为什么大模型能生成文本"
        }
    ]
    
    result = ernie_chat(messages)
    print(result.get("content", result.get("error")))