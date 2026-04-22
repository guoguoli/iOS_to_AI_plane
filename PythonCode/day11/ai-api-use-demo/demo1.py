"""
通义千问（Qwen）API 调用示例

安装依赖：
    pip install dashscope python-dotenv

.env 文件配置：
    DASHSCOPE_API_KEY=your-api-key
"""

import os
from dotenv import load_dotenv

# 从 .env 文件加载环境变量
load_dotenv()

# 导入 dashscope 库（阿里云通义千问 SDK）
import dashscope
from dashscope import Generation
from dashscope.api_entities.dashscope_response import GenerationResponse


def test_connection():
    """测试 API 连接"""
    messages = [
        {'role': 'user', 'content': '你好，请简单介绍一下你自己'}
    ]

    response = Generation.call(
        model=dashscope.Generation.Models.qwen_turbo,  # 或 qwen_plus, qwen_turbo
        messages=messages,
        result_format='message'
    )

    if response.status_code == 200:
        print("API 连接成功!")
        print(f"回复: {response.output.choices[0].message.content}")
    else:
        print(f"请求失败: {response.code} - {response.message}")

    return response


if __name__ == "__main__":
    test_connection()