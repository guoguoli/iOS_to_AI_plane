# test_harness_mock.py
# Mock 模拟对象示例
# 来源：unittest.mock官方文档 https://docs.python.org/3/library/unittest.mock.html

from unittest.mock import Mock, MagicMock, call, create_autospec
import pytest


# ============================================
# 被测系统：AI作业批改服务
# ============================================

class AICorrectionService:
    """AI批改服务接口"""
    
    def correct_homework(self, homework_text: str) -> dict:
        """
        批改作业
        
        Args:
            homework_text: 作业文本
        Returns:
            批改结果 {"score": int, "feedback": str}
        """
        raise NotImplementedError("需要调用AI API")


class NotificationService:
    """通知服务接口"""
    
    def send_notification(self, user_id: str, message: str) -> bool:
        """
        发送通知
        
        Args:
            user_id: 用户ID
            message: 通知消息
        Returns:
            是否发送成功
        """
        raise NotImplementedError("需要连接消息服务")


class HomeworkCorrectionFacade:
    """作业批改门面服务（被测对象）"""
    
    def __init__(self, ai_service: AICorrectionService, notification_service: NotificationService):
        self.ai_service = ai_service
        self.notification_service = notification_service
    
    def correct_and_notify(self, student_id: str, homework_text: str) -> dict:
        """
        批改作业并发送通知
        
        Args:
            student_id: 学生ID
            homework_text: 作业文本
        Returns:
            批改结果
        """
        # 调用AI批改
        correction_result = self.ai_service.correct_homework(homework_text)
        
        # 发送通知
        message = f"您的作业已批改完成，得分：{correction_result['score']}分"
        self.notification_service.send_notification(student_id, message)
        
        return correction_result


# ============================================
# Mock实现：验证行为交互
# ============================================

def test_homework_correction_with_mock():
    """使用Mock验证AI服务和通知服务的交互"""
    
    # 创建Mock对象
    mock_ai_service = Mock(spec=AICorrectionService)
    mock_notification_service = Mock(spec=NotificationService)
    
    # 配置AI服务Mock行为
    mock_ai_service.correct_homework.return_value = {
        "score": 85,
        "feedback": "结构清晰，论证有力"
    }
    
    # 配置通知服务Mock行为
    mock_notification_service.send_notification.return_value = True
    
    # 创建被测对象，注入Mock
    facade = HomeworkCorrectionFacade(mock_ai_service, mock_notification_service)
    
    # 执行测试
    homework_text = "这是一篇关于人工智能的作文..."
    result = facade.correct_and_notify("student_001", homework_text)
    
    # ============================================
    # Mock验证：检查交互行为
    # ============================================
    
    # 1. 验证AI服务被调用
    mock_ai_service.correct_homework.assert_called_once_with(homework_text)
    
    # 2. 验证通知服务被调用
    mock_notification_service.send_notification.assert_called_once()
    
    # 3. 验证通知内容
    call_args = mock_notification_service.send_notification.call_args
    assert call_args[0][0] == "student_001"  # 第一个参数是student_id
    assert "85分" in call_args[0][1]  # 第二个参数是message
    
    # 4. 验证返回结果
    assert result["score"] == 85
    assert result["feedback"] == "结构清晰，论证有力"
    
    print("✅ Mock测试通过：成功验证服务交互行为")


# ============================================
# Mock高级用法
# ============================================

def test_mock_advanced_features():
    """Mock高级特性示例"""
    
    # 1. side_effect - 多次调用返回不同值
    mock_service = Mock()
    mock_service.get_score.side_effect = [85, 90, 78]  # 第1次返回85，第2次返回90...
    
    assert mock_service.get_score() == 85
    assert mock_service.get_score() == 90
    assert mock_service.get_score() == 78
    
    # 2. side_effect - 抛出异常
    mock_service.risky_operation.side_effect = ConnectionError("网络错误")
    
    with pytest.raises(ConnectionError):
        mock_service.risky_operation()
    
    # 3. call_count - 验证调用次数
    mock_service.record.call_count == 0
    mock_service.record("test1")
    mock_service.record("test2")
    assert mock_service.record.call_count == 2
    
    # 4. call_args_list - 获取所有调用参数
    mock_service.process("a")
    mock_service.process("b")
    assert mock_service.process.call_args_list == [call("a"), call("b")]
    
    # 5. reset_mock - 重置Mock状态
    mock_service.reset_mock()
    assert mock_service.process.call_count == 0
    
    print("✅ Mock高级特性测试通过")


# ============================================
# create_autospec - 自动规格Mock
# ============================================

def test_autospec_mock():
    """使用create_autospec确保Mock符合真实接口"""
    
    # 创建符合真实接口规格的Mock
    # 如果调用不存在的方法或参数错误，会立即报错
    mock_ai = create_autospec(AICorrectionService)
    
    # 配置返回值
    mock_ai.correct_homework.return_value = {"score": 90, "feedback": "优秀"}
    
    # 正确调用
    result = mock_ai.correct_homework("作业文本")
    assert result["score"] == 90
    
    # 错误调用（如果真实方法不支持这些参数，会报错）
    # mock_ai.correct_homework("text", extra_param="value")  # 会抛出TypeError
    
    print("✅ Autospec Mock测试通过")

