"""
通义千问（Qwen）API 调用示例

安装依赖：
    pip install dashscope

环境变量设置：
    export DASHSCOPE_API_KEY="your-api-key"
    或在代码中设置：dashscope.api_key = "your-api-key"
"""

# 导入 dashscope 库（阿里云通义千问 SDK）
import dashscope
from dashscope import Generation
from dashscope.api_entities.dashscope_response import GenerationResponse

# 可选：设置 API Key
# dashscope.api_key = 'your-api-key'


def test_connection():
    """测试 API 连接"""
    messages = [
        {'role': 'user', 'content': '你好，请简单介绍一下你自己'}
    ]

    response = Generation.call(
        model=dashscope.Generation.Models.qwen_max,  # 或 qwen_plus, qwen_turbo
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