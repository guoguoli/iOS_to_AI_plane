# 安装：pip install dashscope
import dashscope
from dashscope import Generation
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

# 发起聊天请求
response = Generation.call(
    model='qwen-turbo',  # 通义千问模型选择
    messages=[
        {'role': 'system', 'content': '你是一位成都教育科技公司的数学老师。'},
        {'role': 'user', 'content': '请批改这道数学题：12 × 8 = 94'}
    ],
    temperature=0.7,  # 创造性参数（0-2）
    max_tokens=500,   # 最大响应Token数
)

# 解析响应
if response.status_code == 200:
    print(f"回答: {response.output.text}")
    print(f"使用Token: {response.usage.total_tokens}")
else:
    print(f"请求失败: {response.code} - {response.message}")