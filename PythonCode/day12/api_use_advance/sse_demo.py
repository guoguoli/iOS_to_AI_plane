import dashscope
from dashscope import Generation 
import os
import time
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
class StreamingChat:
    """带打字机效果的流式聊天"""
    
    def __init__(self):
        self.conversation_history = []
    
    def chat(self, user_input: str) -> str:
        """流式对话"""
        
        # 添加用户消息到历史
        self.conversation_history.append({
            'role': 'user',
            'content': user_input
        })
        
        print(f"\n👤 你: {user_input}\n")
        print("🤖 AI: ", end='', flush=True)
        
        # 流式调用
        responses = Generation.call(
            model='qwen-turbo',
            messages=self.conversation_history,
            stream=True,
            incremental_output=True,
            result_format='message'
            
        )
        
        full_response = ""
        for response in responses:
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                if content:
                    print(content, end='', flush=True)
                    full_response += content
                    time.sleep(0.02)  # 打字机效果延时
            else:
                print(f"\n错误: {response.code}")
                break
        
        print()
        
        # 保存AI回复到历史
        self.conversation_history.append({
            'role': 'assistant',
            'content': full_response
        })
        
        return full_response
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []

# 使用示例
if __name__ == "__main__":
    chat = StreamingChat()
    
    while True:
        user_input = input("\n你: ")
        if user_input.lower() in ['quit', 'exit', '退出']:
            break
        chat.chat(user_input)

