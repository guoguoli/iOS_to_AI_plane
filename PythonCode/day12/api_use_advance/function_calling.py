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

function_schema_examples()

