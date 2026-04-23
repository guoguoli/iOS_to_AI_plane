from dashscope import Generation 
import os
from dotenv import load_dotenv

load_dotenv()

def basic_stream_example():
    """基础流式输出示例"""
    print("=" * 60)
    print("基础流式输出示例")
    print("=" * 60) 

    responses = Generation.call(
        model="qwen_turbo",
        messages=[{
            'role':'user',
            'content':'用三句话解释什么是人工智能'
        }],
        stream=True,
        incremental_output = True
    )
    print("开始流式输出")
    print("=" * 60)

    full_response = ""
    for response in responses:
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            if content:
                print(content,end='',flush=True)
                full_response += content
        else:
            print(f"\n ❌错误 :{response.code} - {response.message}")
            break
    print("=" * 60)
    return full_response
if __name__ == '__main__':
    basic_stream_example()
    

