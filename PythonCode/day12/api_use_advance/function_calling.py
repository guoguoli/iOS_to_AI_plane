import dashscope
from dashscope import Generation 
import os
from dotenv import load_dotenv
import json


load_dotenv()

dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')


def function_schema_examples():
    """
    Function Calling 函数定义示例
    """
    
    # ============================================================
    # 示例1：天气查询函数
    # ============================================================
    weather_function = {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如：北京、上海、Tokyo"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位，默认celsius",
                        "default": "celsius"
                    }
                },
                "required": ["city"]
            }
        }
    }
    
    # ============================================================
    # 示例2：数据库查询函数
    # ============================================================
    db_query_function = {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": "执行SQL数据库查询",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "数据库表名"
                    },
                    "conditions": {
                        "type": "object",
                        "description": "查询条件，键值对形式"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回记录数限制",
                        "default": 100
                    }
                },
                "required": ["table"]
            }
        }
    }
    
    # ============================================================
    # 示例3：发送邮件函数
    # ============================================================
    email_function = {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "发送电子邮件",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "收件人邮箱地址"
                    },
                    "subject": {
                        "type": "string", 
                        "description": "邮件主题"
                    },
                    "body": {
                        "type": "string",
                        "description": "邮件正文内容"
                    },
                    "cc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "抄送邮箱列表"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        }
    }
    
    print("✅ 函数Schema定义完成")
    return [weather_function, db_query_function, email_function]


class FunctionCallingDemo:
    """Function Calling 使用示例"""
    
    def __init__(self):
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "获取指定城市的天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "城市名称"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "description": "温度单位"
                            }
                        },
                        "required": ["city"]
                    }
                }
            }
        ]
    
    def execute_weather_query(self, city: str, unit: str = "celsius") -> dict:
        """
        模拟天气查询（实际项目中连接天气API）
        """
        # 模拟天气数据
        weather_data = {
            "北京": {"temp": 22, "weather": "晴", "humidity": 45},
            "上海": {"temp": 25, "weather": "多云", "humidity": 60},
            "广州": {"temp": 28, "weather": "雷阵雨", "humidity": 75},
            "深圳": {"temp": 29, "weather": "晴", "humidity": 55}
        }
        
        city_weather = weather_data.get(city, {"temp": 20, "weather": "未知", "humidity": 50})
        
        # 转换温度
        if unit == "fahrenheit":
            city_weather["temp"] = city_weather["temp"] * 9/5 + 32
        
        return city_weather
    
    def chat_with_function(self, user_input: str) -> str:
        """
        带Function Calling的对话
        """
        
        messages = [{"role": "user", "content": user_input}]
        
        response = Generation.call(
            model='qwen-turbo',
            messages=messages,
            result_format = "message",
            tools=self.tools
        )
        
        if response.status_code != 200:
            return f"错误: {response.code} - {response.message}"
        
        # 检查是否有函数调用
        print(f"\n🔧 检查是否有函数调用...")
        print(response.output)
        tool_calls = response.output.choices[0].message.tool_calls
        
        if tool_calls:
            # 处理函数调用
            for tool_call in tool_calls:
                print('函数调用')
                print(tool_call)
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"\n🔧 调用函数: {function_name}")
                print(f"📋 参数: {arguments}")
                
                # 执行函数
                if function_name == "get_weather":
                    result = self.execute_weather_query(
                        city=arguments.get("city"),
                        unit=arguments.get("unit", "celsius")
                    )
                    
                    print(f"📊 查询结果: {result}")
                    
                    # 将函数结果返回给模型
                    messages.append({
                        "role": "assistant",
                        "content": ""
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                    
                    # 再次调用获取最终回复
                    final_response = Generation.call(
                        model='qwen-turbo',
                        messages=messages,
                        result_format = "message",
                        tools=self.tools
                    )
                    
                    if final_response.status_code == 200:
                        return final_response.output.choices[0].message.content
        
        # 无函数调用，直接返回文本
        return response.output.choices[0].message.content

# 使用示例
if __name__ == "__main__":
    demo = FunctionCallingDemo()
    
    questions = [
        "北京今天天气怎么样？查询具体信息",
        "上海温度是多少华氏度？",
        "广州天气好吗？"
    ]
    
    for q in questions:
        print(f"\n{'='*60}")
        print(f"👤 用户: {q}")
        print('='*60)
        answer = demo.chat_with_function(q)
        print(f"🤖 AI回复: {answer}")

