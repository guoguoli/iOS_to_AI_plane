import dashscope
from dashscope import Generation 
import os
from dotenv import load_dotenv

load_dotenv()
 
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

def basic_stream_example():
    """基础流式输出示例"""
    print("=" * 60)
    print("基础流式输出示例")
    print("=" * 60) 

    responses = Generation.call(
        model="qwen-turbo",
        messages=[{
            'role':'user',
            'content':'用三句话解释什么是人工智能'
        }],
        result_format='message',
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
def stream_with_thinking():
    """带思考过程的流式输出"""
    
    print("=" * 60)
    print("思考过程流式输出示例")
    print("=" * 60)
    
    responses = Generation.call(
        model='qwen-plus',  # 使用更强的模型
        messages=[{
            'role': 'user', 
            'content': '分析一下Python和Swift两种语言的优劣'
        }],
        result_format='message',
        stream=True,
        incremental_output=True
    )
    
    print("\n🤖 正在分析：\n")
    
    for response in responses:
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            if content:
                print(content, end='', flush=True)
        else:
            print(f"\n❌ 错误: {response.code}")
            break
    
    print("\n")
if __name__ == '__main__':
    # basic_stream_example()
    stream_with_thinking()

