import os
import dashscope
from dashscope import Generation 
from dotenv import load_dotenv

load_dotenv()

BASE_PROMPT = """角色】你是成都本地K12学科专业批改老师，熟悉四川中小学教学大纲、评分标准。
【任务】批改用户提交的数学作业题目与学生答案。
【批改要求】
1. 先判断：答案正确 / 部分错误 / 完全错误
2. 写出标准解题步骤，步骤清晰、符合校内答题规范
3. 精准指出学生错误点：计算错误、公式误用、审题失误、逻辑漏洞
4. 给出错因总结+简短学习建议
5. 最后给出：得分/满分
【约束】语言简洁通俗，符合中小学批改风格

待批改内容：
{question}
学生答案：{student_answer}
"""
INPUT_PRICE = 0.0015    # 元/1000token
OUTPUT_PRICE = 0.006    # 元/1000token


def correct_math_homework(question, student_answer):
    prompt = BASE_PROMPT.format(question=question, student_answer=student_answer)
    response = Generation.call(
        model="qwen-turbo",
        messages=[{"role":"user","content":prompt}],
        temperature=0.3,
        result_format="message"
    )
    content = response.output.choices[0].message.content
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost = input_tokens * INPUT_PRICE + output_tokens * OUTPUT_PRICE
    return {
        "结果":content,
        "输入token数":input_tokens,
        "输出token数":output_tokens,
        "本次成本(元)":round(cost/1000,6)
    }
if __name__ == '__main__':
    question1 = "计算题：25×(40+4)"
    student_answer1 = "25×40+4 = 1000+4 = 1004"
    res1 = correct_math_homework(question1, student_answer1)

    question2 = "应用题：一个长方形长12cm，宽5cm，求周长"
    student_answer2 = "周长=12*5=60平方厘米"
    res2 = correct_math_homework(question2, student_answer2)

    question3 = "解方程：3x+6=24"
    student_answer3 = "3x=24+6  3x=30  x=10"
    res3 = correct_math_homework(question3, student_answer3)
    print("===== 第1题批改结果 =====")
    print(res1)
    print("===== 第2题批改结果 =====")
    print(res2)
    print("===== 第3题批改结果 =====")
    print(res3)
   