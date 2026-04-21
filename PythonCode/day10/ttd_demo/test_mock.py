# test_mock.py
# unittest.mock文档：https://docs.python.org/

from unittest.mock import Mock, patch, MagicMock, AsyncMock
import pytest

# ============================================
# 基础Mock
# ============================================

def test_basic_mock():
    """基础Mock使用"""
    mock_function = Mock()
    mock_function.return_value = "mocked result"
    
    result = mock_function("arg1", "arg2")
    
    assert result == "mocked result"
    mock_function.assert_called_once_with("arg1", "arg2")

# ============================================
# Mock属性和链式调用
# ============================================

def test_mock_attributes():
    """Mock链式调用"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    
    # 链式调用
    assert mock_response.json()["data"] == "test"
    mock_response.json.assert_called_once()

# ============================================
# Patch装饰器和上下文管理器
# ============================================

class AIAgent:
    """AI代理类"""
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def analyze(self, text: str) -> dict:
        # 实际调用API
        return {"sentiment": "positive", "confidence": 0.9}

def test_with_patch_decorator():
    """使用@patch装饰器Mock"""
    with patch("test_mock.AIAgent") as MockAIAgent:
        # 配置Mock
        mock_instance = MockAIAgent.return_value
        mock_instance.analyze.return_value = {
            "sentiment": "mocked",
            "confidence": 1.0
        }
        
        # 使用Mock
        agent = AIAgent("fake_key")
        result = agent.analyze("test text")
        
        assert result["sentiment"] == "mocked"
        assert result["confidence"] == 1.0

def test_patch_context_manager():
    """使用with语句Patch"""
    with patch("test_mock.AIAgent.analyze") as mock_analyze:
        mock_analyze.return_value = {"sentiment": "negative", "confidence": 0.8}
        
        # 测试代码
        mock_instance = AIAgent("fake_key")
        result = mock_instance.analyze("sad text")
        
        assert result["sentiment"] == "negative"

# ============================================
# Mock AI API调用（实战场景）
# ============================================

# 模拟的OpenAI响应结构
def create_mock_openai_response(content: str) -> dict:
    """创建模拟的OpenAI API响应"""
    return {
        "id": "chatcmpl-mock",
        "object": "chat.completion",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": content
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }

def test_homework_grading_with_mock_api():
    """测试作业批改API（Mock外部AI服务）"""
    
    # 模拟的正确答案
    CORRECT_ANSWERS = ["A", "B", "C", "D", "A"]
    
    # Mock外部AI API
    with patch("test_mock.AIAgent.analyze") as mock_analyze:
        # 配置Mock返回
        mock_analyze.return_value = {
            "sentiment": "positive",
            "score": 100
        }
        
        # 模拟学生答题并调用AI评估
        agent = AIAgent("fake_key")
        student_answers = ["A", "B", "C", "D", "A"]
        result = agent.analyze(str(student_answers))
        
        # 验证
        assert result["score"] == 100
        mock_analyze.assert_called_once()

# ============================================
# AsyncMock
# ============================================

@pytest.mark.asyncio
async def test_async_mock():
    """异步Mock"""
    async_mock = AsyncMock(return_value={"result": "async_mocked"})
    
    # 调用异步函数
    result = await async_mock()
    
    assert result == {"result": "async_mocked"}
    async_mock.assert_called_once()
# 运行所有测试
if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])