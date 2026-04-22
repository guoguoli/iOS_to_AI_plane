# 通义千问也支持OpenAI兼容模式
import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

response = client.chat.completions.create(
    model="qwen-turbo",
    messages=[
        {"role": "system", "content": "你是一位成都教育科技公司的数学老师。"},
        {"role": "user", "content": "请批改这道数学题：12 × 8 = 96"}
    ]
)

print(response.choices[0].message.content)