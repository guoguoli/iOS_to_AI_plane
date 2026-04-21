# test_fastapi_basic.py
# FastAPI测试文档：https://fastapi.tiangolo.com/tutorial/testing/

from fastapi import FastAPI,HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

app = FastAPI()

# 定义数据模型
class Student(BaseModel):
    id: int
    name: str
    score: float

class GradeRequest(BaseModel):
    student_id: int
    scores: list[float]

# 模拟数据库
students_db = {
    1: {"id": 1, "name": "张三", "score": 95},
    2: {"id": 2, "name": "李四", "score": 78},
}

# 定义API路由
@app.get("/students/{student_id}")
def get_student(student_id: int):
    """获取学生信息"""
    if student_id not in students_db:
        raise HTTPException(status_code=404, detail="学生不存在")
    return students_db[student_id]

@app.post("/students/grade")
def calculate_grade(request: GradeRequest):
    """计算学生平均分"""
    if not request.scores:
        raise HTTPException(status_code=400, detail="成绩列表不能为空")
    
    average = sum(request.scores) / len(request.scores)
    return {
        "student_id": request.student_id,
        "average": round(average, 2),
        "count": len(request.scores)
    }

# ============ 测试代码 ============

# 创建TestClient
client = TestClient(app)

def test_get_student_success():
    """测试获取学生成功"""
    response = client.get("/students/1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "张三"
    assert data["score"] == 95

def test_get_student_not_found():
    """测试获取不存在的学生"""
    response = client.get("/students/999")
    assert response.status_code == 404

def test_calculate_grade():
    """测试计算平均分"""
    response = client.post(
        "/students/grade",
        json={"student_id": 1, "scores": [90, 85, 95]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["average"] == 90.0
    assert data["count"] == 3

def test_calculate_grade_empty_scores():
    """测试空成绩列表"""
    response = client.post(
        "/students/grade",
        json={"student_id": 1, "scores": []}
    )
    assert response.status_code == 400

# 运行所有测试
if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])