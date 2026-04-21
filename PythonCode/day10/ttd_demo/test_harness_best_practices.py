# test_harness_best_practices.py
# Test Harness工程化最佳实践

import pytest
from typing import Protocol, runtime_checkable
from dataclasses import dataclass
from unittest.mock import Mock, MagicMock
from test_harness_mock import (
    AICorrectionService,
    NotificationService,
    HomeworkCorrectionFacade
)

from test_harness_stub import (
    GradeRepositoryStub,
    GradeService
)

# ============================================
# 最佳实践1：使用Protocol定义接口
# ============================================

@runtime_checkable
class GradeRepositoryProtocol(Protocol):
    """成绩仓库协议（接口）"""
    
    def get_student_grades(self, student_id: str) -> dict:
        ...


class StubGradeRepository:
    """符合Protocol的Stub实现"""
    
    def get_student_grades(self, student_id: str) -> dict:
        return {"scores": [90, 85]}


def test_stub_conforms_to_protocol():
    """验证Stub符合接口协议"""
    stub = StubGradeRepository()
    assert isinstance(stub, GradeRepositoryProtocol)
    print("✅ Stub符合接口协议")


# ============================================
# 最佳实践2：使用Fixture管理Test Harness
# ============================================

@pytest.fixture
def ai_service_mock():
    """AI服务Mock Fixture"""
    mock = Mock(spec=AICorrectionService)
    mock.correct_homework.return_value = {"score": 85, "feedback": "良好"}
    return mock


@pytest.fixture
def notification_service_mock():
    """通知服务Mock Fixture"""
    return Mock(spec=NotificationService)


@pytest.fixture
def homework_facade(ai_service_mock, notification_service_mock):
    """作业批改门面Fixture"""
    return HomeworkCorrectionFacade(ai_service_mock, notification_service_mock)


def test_with_fixtures(homework_facade, ai_service_mock):
    """使用Fixture简化测试代码"""
    result = homework_facade.correct_and_notify("student_001", "作业")
    
    assert result["score"] == 85
    ai_service_mock.correct_homework.assert_called_once()


# ============================================
# 最佳实践3：使用Pytest参数化生成Test Harness
# ============================================

@pytest.mark.parametrize("scores,expected_average,expected_level", [
    ([95, 90, 88], 91.0, "A"),
    ([85, 82, 78], 81.67, "B"),
    ([75, 72, 68], 71.67, "C"),
    ([65, 62, 58], 61.67, "D"),
    ([55, 52, 48], 51.67, "F"),
])
def test_parametrized_harness(scores, expected_average, expected_level):
    """参数化测试：不同输入组合"""
    
    # 动态创建Stub
    stub = GradeRepositoryStub()
    stub.stub_data = {"test_student": {"scores": scores}}
    
    service = GradeService(stub)
    
    # 验证
    assert service.calculate_average_score("test_student") == pytest.approx(expected_average, rel=0.01)
    assert service.get_grade_level("test_student") == expected_level


# ============================================
# 最佳实践4：Test Harness清理
# ============================================

@pytest.fixture
def cleanable_mock():
    """可清理的Mock Fixture"""
    mock = MagicMock()
    yield mock
    # 测试后清理
    mock.reset_mock()
    mock.reset_mock(return_value=True, side_effect=True)


def test_with_cleanup(cleanable_mock):
    """使用可清理的Mock"""
    cleanable_mock.operation.return_value = "result"
    
    result = cleanable_mock.operation()
    assert result == "result"
    
    # Fixture会自动清理