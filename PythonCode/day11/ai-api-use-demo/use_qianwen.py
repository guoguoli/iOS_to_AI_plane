"""
通义千问 API 完整调用示例

来源：dashscope库
文档：https://help.aliyun.com/zh/model-studio/developer-reference/use-qwen-by-calling-api

前置准备：
1. pip install dashscope
2. 设置环境变量 DASHSCOPE_API_KEY
"""

import dashscope
from dashscope import Generation
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

def chat(
    messages: list,
    model: str = "qwen-turbo",
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> dict:
    """
    通用的聊天补全函数
    
    Args:
        messages: 消息列表，格式为 [{"role": "system"/"user"/"assistant", "content": "..."}]
        model: 模型名称（qwen-turbo / qwen-plus / qwen-max）
        temperature: 创造性参数（0-2），越低越确定性
        max_tokens: 最大输出Token数
        
    Returns:
        包含响应内容和usage信息的字典
        
    Reference: 
        https://help.aliyun.com/zh/model-studio/developer-reference/use-qwen-by-calling-api
    """
    try:
        response = Generation.call(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            result_format='message',
        )
        
        if response.status_code == 200:
            return {
                "content": response.output.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "model": model,
                "finish_reason": response.output.choices[0].finish_reason,
            }
        else:
            return {
                "error": f"{response.code} - {response.message}",
                "content": None,
                "usage": None
            }
        
    except Exception as e:
        return {
            "error": str(e),
            "content": None,
            "usage": None
        }

# ============ 使用示例 ============
if __name__ == "__main__":
    # 成都教育科技场景：作业批改助手
    messages = [
        {
            "role": "system", 
            "content": """你是成都某教育科技公司的数学作业批改助手。
            你的职责是：
            1. 检查学生答案是否正确
            2. 给出简要的批改意见
            3. 如果错误，提供正确的解题思路
            4. 用鼓励性语言反馈"""
        },
        {
            "role": "user", 
            "content": """请批改这道数学题：
            题目：小明有25个苹果，给了小红8个，还剩多少个？
            学生答案：25 - 8 = 16（个）"""
        }
    ]
    
    result = chat(messages)
    
    if result.get("content"):
        print("批改结果：")
        print(result["content"])
        print(f"\n使用Token数：{result['usage']['total_tokens']}")