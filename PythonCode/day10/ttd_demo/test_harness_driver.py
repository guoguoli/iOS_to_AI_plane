# test_harness_driver.py
# pytest Test Driver 示例
# 来源：pytest官方文档 https://docs.pytest.org/

import pytest
from typing import Callable, Any, Dict, List

class TestDriver:
    """
    Test Driver - 测试驱动器
    负责调用被测代码、传递测试数据、捕获结果
    """
    
    def __init__(self, test_target: Callable):
        """
        初始化测试驱动
        
        Args:
            test_target: 被测函数或方法
        """
        self.test_target = test_target
        self.test_results: List[Dict[str, Any]] = []
    
    def execute_test(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个测试用例
        
        Args:
            test_data: 测试数据字典，包含 input 和 expected
        """
        test_input = test_data.get("input", {})
        expected = test_data.get("expected")
        
        try:
            # 调用被测代码
            actual = self.test_target(**test_input)
            
            # 验证结果
            passed = actual == expected
            
            # 记录结果
            result = {
                "input": test_input,
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "error": None
            }
        except Exception as e:
            result = {
                "input": test_input,
                "expected": expected,
                "actual": None,
                "passed": False,
                "error": str(e)
            }
        
        self.test_results.append(result)
        return result
    
    def execute_batch(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量执行测试用例
        """
        return [self.execute_test(case) for case in test_cases]
    
    def get_report(self) -> Dict[str, Any]:
        """
        生成测试报告
        """
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": f"{passed/total*100:.2f}%" if total > 0 else "0%",
            "details": self.test_results
        }


# ============================================
# 实战案例：学生成绩计算器的Test Driver
# ============================================

def calculate_grade(score: float) -> str:
    """
    被测函数：根据分数计算等级
    """
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def test_calculate_grade_with_driver():
    """使用Test Driver测试成绩计算"""
    
    # 创建测试驱动
    driver = TestDriver(calculate_grade)
    
    # 测试数据集
    test_cases = [
        {"input": {"score": 95}, "expected": "A"},
        {"input": {"score": 85}, "expected": "B"},
        {"input": {"score": 75}, "expected": "C"},
        {"input": {"score": 65}, "expected": "D"},
        {"input": {"score": 55}, "expected": "F"},
        {"input": {"score": 90}, "expected": "A"},  # 边界值
        {"input": {"score": 89.9}, "expected": "B"},  # 边界值
    ]
    
    # 批量执行
    driver.execute_batch(test_cases)
    
    # 获取报告
    report = driver.get_report()
    
    # 断言
    assert report["passed"] == report["total"], f"测试失败: {report}"
    print(f"✅ Test Driver测试通过: {report['pass_rate']}")
test_calculate_grade_with_driver()
