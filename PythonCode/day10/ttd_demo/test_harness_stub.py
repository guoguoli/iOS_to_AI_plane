# test_harness_stub.py
# Stub 桩程序示例
# 来源：unittest.mock官方文档 https://docs.python.org/3/library/unittest.mock.html

from typing import Any, Optional
from dataclasses import dataclass
import json
import pytest


# ============================================
# 被测系统：学生成绩查询服务
# ============================================

class GradeRepository:
    """成绩数据访问层（需要被Stub替换）"""
    
    def get_student_grades(self, student_id: str) -> dict:
        """从数据库获取学生成绩"""
        # 实际实现会连接数据库
        raise NotImplementedError("需要数据库连接")
    
    def save_grade(self, student_id: str, grade: dict) -> bool:
        """保存成绩到数据库"""
        raise NotImplementedError("需要数据库连接")


class GradeService:
    """成绩业务逻辑层（被测对象）"""
    
    def __init__(self, repository: GradeRepository):
        self.repository = repository
    
    def calculate_average_score(self, student_id: str) -> float:
        """
        计算学生平均分
        
        Args:
            student_id: 学生ID
        Returns:
            平均分
        """
        grades_data = self.repository.get_student_grades(student_id)
        scores = grades_data.get("scores", [])
        
        if not scores:
            return 0.0
        
        return sum(scores) / len(scores)
    
    def get_grade_level(self, student_id: str) -> str:
        """
        获取学生等级
        
        Args:
            student_id: 学生ID
        Returns:
            等级（A/B/C/D/F）
        """
        average = self.calculate_average_score(student_id)
        
        if average >= 90:
            return "A"
        elif average >= 80:
            return "B"
        elif average >= 70:
            return "C"
        elif average >= 60:
            return "D"
        else:
            return "F"


# ============================================
# Stub实现：模拟数据库访问
# ============================================

@dataclass
class GradeRepositoryStub(GradeRepository):
    """
    成绩仓库桩程序（Stub）
    返回预设的固定响应，不实际连接数据库
    """
    
    # 预设的测试数据
    stub_data: dict = None
    
    def __post_init__(self):
        # 默认测试数据
        if self.stub_data is None:
            self.stub_data = {
                "student_001": {"scores": [95, 88, 92, 90]},
                "student_002": {"scores": [75, 82, 78, 80]},
                "student_003": {"scores": []},  # 无成绩
            }
    
    def get_student_grades(self, student_id: str) -> dict:
        """
        Stub实现：返回预设数据
        """
        if student_id in self.stub_data:
            return self.stub_data[student_id]
        return {"scores": []}
    
    def save_grade(self, student_id: str, grade: dict) -> bool:
        """
        Stub实现：总是返回成功
        """
        return True


# ============================================
# 使用Stub进行测试
# ============================================

def test_grade_service_with_stub():
    """使用Stub测试成绩服务"""
    
    # 创建Stub
    stub = GradeRepositoryStub()
    
    # 注入Stub到被测系统
    service = GradeService(stub)
    
    # 测试学生1（优秀学生）
    average_1 = service.calculate_average_score("student_001")
    assert average_1 == pytest.approx(91.25)  # (95+88+92+90)/4
    assert service.get_grade_level("student_001") == "A"
    
    # 测试学生2（中等学生）
    average_2 = service.calculate_average_score("student_002")
    assert average_2 == pytest.approx(78.75)  # (75+82+78+80)/4
    assert service.get_grade_level("student_002") == "C"
    
    # 测试学生3（无成绩）
    average_3 = service.calculate_average_score("student_003")
    assert average_3 == 0.0
    assert service.get_grade_level("student_003") == "F"
    
    # 测试不存在的学生
    average_4 = service.calculate_average_score("student_999")
    assert average_4 == 0.0
    
    print("✅ Stub测试通过：成功隔离数据库依赖")


# ============================================
# 使用unittest.mock创建动态Stub
# ============================================

from unittest.mock import MagicMock

def test_grade_service_with_magic_mock():
    """使用MagicMock创建动态Stub"""
    
    # 创建Mock对象
    mock_repo = MagicMock(spec=GradeRepository)
    
    # 配置Mock行为
    mock_repo.get_student_grades.return_value = {"scores": [90, 85, 88]}
    
    # 注入Mock
    service = GradeService(mock_repo)
    
    # 执行测试
    average = service.calculate_average_score("any_student")
    
    # 验证
    assert average == pytest.approx(87.67, rel=0.01)
    
    # 验证Mock被正确调用
    mock_repo.get_student_grades.assert_called_once_with("any_student")
    
    print("✅ Magic Mock测试通过")
