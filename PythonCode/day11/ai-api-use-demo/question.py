# ============ 代码填空1：完成API调用 ============
"""
填空1：完成基本的API调用代码
"""

import os
from dotenv import load_dotenv
import dashscope
from dashscope import Generation

load_dotenv()

# 设置API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")  # 从环境变量获取API Key (DASHSCOPE_API_KEY)

def ask_question(question: str) -> str:
    """问答函数"""
    response = Generation.call(
        model="qwen-turbo",  # 选择 qwen-turbo
        messages=[
            {"role": "user", "content": question}  # 传入question
        ],
        result_format='message'
    )
    return response.output.choices[0].message.content  # 返回回复内容

# 测试
print(ask_question("什么是Token？"))

# ============ 代码填空2：实现Token计算 ============
"""
填空2：实现Token计数函数
"""
import re
def count_tokens_cn(text: str) -> int:
    """估算中文文本的Token数"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    other_chars = len(text) - chinese_chars - english_chars
    
    # Token估算
    estimated_tokens = chinese_chars / 1.5 + english_chars / 4 + other_chars / 2
    return int(estimated_tokens)  # 返回估算的token数量

# 测试
print(count_tokens_cn("成都教育科技"))  # 预期：约4-6个Token