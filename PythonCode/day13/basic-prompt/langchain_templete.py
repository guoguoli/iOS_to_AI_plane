
from langchain_core.prompts import PromptTemplate 
from langchain_community.llms import Tongyi  # 通义千问
import os
from dotenv import load_dotenv
load_dotenv()

# 创建Prompt模板
code_review_template = PromptTemplate(
    input_variables=["language", "code", "focus_areas"],
    template="""
你是资深的{language}开发工程师，擅长代码审查。

## 代码
{language}代码：
{code}

## 审查重点
{focus_areas}

## 输出要求
请按以下结构输出审查结果：

1. 总体评价：[简要评价]

2. 问题列表：
   - 【严重程度】位置 - 问题描述
   - 建议：解决方案

3. 优化建议：[2-3条优化建议]

4. 代码评分（1-10分）：
   - 可读性：X分
   - 性能：X分
   - 安全性：X分
"""
)

qwen_llm = Tongyi(
    model_name="qwen-turbo",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature=0.1
)
# 使用模板（需配合通义千问）
chain = code_review_template | qwen_llm

# 运行（新版用 invoke，不是 run）
result = chain.invoke({
    "language": "swift",
    "code": "class MyVC: UIViewController { var data: String! }",
    "focus_areas": "内存管理、可选类型安全"
})
print(result)