# test_dependency_override.py
# FastAPI依赖注入文档：https://fastapi.tiangolo.com/tutorial/dependencies/

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# ============================================
# 定义依赖项
# ============================================

class AIService:
    """AI服务（实际依赖）"""
    
    def analyze_homework(self, image_data: bytes) -> dict:
        # 实际调用AI API...
        return {"result": "correct", "score": 95}

def get_ai_service() -> AIService:
    """依赖注入：获取AI服务"""
    return AIService()

# ============================================
# 业务路由
# ============================================

class HomeworkRequest(BaseModel):
    student_id: int
    image_base64: str

@app.post("/homework/analyze")
def analyze_homework(
    request: HomeworkRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """作业分析API"""
    # 模拟处理
    result = ai_service.analyze_homework(b"data")
    return {
        "student_id": request.student_id,
        "analysis": result
    }

# ============================================
# 测试：覆盖依赖
# ============================================

# 创建Mock AI服务
class MockAIService:
    """Mock AI服务"""
    
    def analyze_homework(self, image_data: bytes) -> dict:
        return {
            "result": "mock_result",
            "score": 100,  # Mock返回满分
            "is_mock": True
        }

# 创建测试客户端
client = TestClient(app)

def test_analyze_homework_with_mock():
    """使用Mock AI服务测试"""
    # 覆盖依赖
    app.dependency_overrides[get_ai_service] = MockAIService
    
    response = client.post(
        "/homework/analyze",
        json={"student_id": 1, "image_base64": "fake_data"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["analysis"]["score"] == 100  # Mock返回值
    assert data["analysis"]["is_mock"] is True
    
    # 清理：移除覆盖
    app.dependency_overrides.clear()

def test_analyze_homework_real_service():
    """使用真实AI服务测试（需要网络）"""
    # 不覆盖，使用真实服务
    response = client.post(
        "/homework/analyze",
        json={"student_id": 1, "image_base64": "fake_data"}
    )
    
    # 注意：实际测试中可能失败，因为没有真实的AI服务
    assert response.status_code == 200
# 运行所有测试
if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])