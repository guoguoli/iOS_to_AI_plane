# test_async.py
# pytest-asyncio文档：https://docs.pytest.org/
# pytest-asyncio >= 0.21 使用 STRICT 模式，需在 pytest.ini / pyproject.toml
# 或直接在文件顶部用 pytestmark 指定 loop_scope

import asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
import httpx
from httpx import AsyncClient, ASGITransport
import pytest

app = FastAPI()

@app.get("/async/students")
async def get_students():
    """异步获取学生列表"""
    await asyncio.sleep(0.1)  # 模拟异步操作
    return {"students": ["张三", "李四", "王五"]}

@app.post("/async/homework")
async def submit_homework(student_id: int, score: float):
    """异步提交作业"""
    await asyncio.sleep(0.1)
    return {
        "student_id": student_id,
        "score": score,
        "status": "submitted"
    }

# ============================================
# 同步测试（使用TestClient）
# ============================================

def test_async_endpoint_with_test_client():
    """同步方式测试异步端点"""
    client = TestClient(app)
    response = client.get("/async/students")
    assert response.status_code == 200

# ============================================
# 异步测试（使用AsyncClient + pytest-asyncio）
# ============================================

# 需要安装：pip install pytest-asyncio httpx

@pytest.mark.asyncio
async def test_async_endpoint():
    """异步方式测试"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/async/students")
        assert response.status_code == 200
        assert "students" in response.json()

@pytest.mark.asyncio
async def test_async_homework_submit():
    """异步提交作业测试"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/async/homework",
            params={"student_id": 1, "score": 95.5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 95.5
        assert data["status"] == "submitted"
# 运行所有测试
if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])