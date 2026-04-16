# Event Loop的工作流程
import asyncio


async def main():
    print("任务开始")
    await asyncio.sleep(2)
    print("第一个任务完成")
    await asyncio.sleep(1)
    print("第二个任务完成")

# 现代官方推荐写法，自动处理事件循环
asyncio.run(main())
# async def - 定义协程函数
# 来源：Python 3.5+ 内置语法

# 基础协程
async def simple_coroutine():
    """最简单的协程"""
    return "Hello, Async!"

# 带参数的协程
async def fetch_student(student_id: int) -> dict:
    """异步获取学生信息"""
    await asyncio.sleep(0.5)  # 模拟数据库查询
    return {
        "id": student_id,
        "name": f"学生{student_id}",
        "score": 85
    }

# 带异常的协程
async def risky_operation():
    """可能失败的协程"""
    await asyncio.sleep(1)
    raise ValueError("操作失败！")