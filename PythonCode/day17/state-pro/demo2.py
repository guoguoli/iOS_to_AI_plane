"""
# 企业级智能作业批改系统
# 项目归属：成都教育科技
# 核心架构：五层分层架构
# 1.接入层(API Gateway)  2.状态管理层(State Machine)
# 3.管道处理层(Pipeline) 4.观察者通知层(Observer)
# 5.持久化层(Persistence)
# 核心能力：
# 1.多题型批改：选择题/填空题/解答题
# 2.AI自动批改 + 人工复核流程
# 3.状态机流转 + 断点续传(状态持久化)
# 4.全链路实时进度通知
# 5.JWT身份认证、模块化热插拔、可水平扩展
"""

import json
import uuid
import time
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
import jwt

# ==============================================
# 全局常量配置模块
# 作用：统一管理密钥、加密算法、全局参数，便于环境切换
# ==============================================
SECRET_KEY = "smart_homework_cd_edu_2026"  # 成都教育科技专属密钥
ALGORITHM = "HS256"                       # JWT加密算法

# ==============================================
# 枚举定义模块
# 作用：统一约束状态、题型，避免魔法值，提升可维护性
# ==============================================
class HomeworkStatus(Enum):
    """
    作业全生命周期状态机
    严格对应架构图状态流转：
    RECEIVED → PARSING → ANALYZING → GRADING → CORRECTING → REVIEWING → COMPLETED
    支持并行状态：GRADING + NOTIFYING
    """
    RECEIVED = "已接收"
    PARSING = "解析中"
    ANALYZING = "特征提取中"
    GRADING = "AI批改中"
    CORRECTING = "批改修正中"
    REVIEWING = "人工复核中"
    COMPLETED = "批改完成"


class QuestionType(Enum):
    """支持批改的题型枚举"""
    CHOICE = "选择题"
    FILL_BLANK = "填空题"
    ANSWER = "解答题"

# ==============================================
# 核心数据模型模块
# 作用：定义题目、作业结构化实体，统一数据规范
# ==============================================
@dataclass
class Question:
    """
    题目实体模型
    :param q_id: 题目唯一标识
    :param q_type: 题目类型(选择/填空/解答)
    :param content: 题目内容
    :param standard_answer: 标准答案
    :param score: 题目满分分值
    """
    q_id: str
    q_type: QuestionType
    content: str
    standard_answer: str
    score: int


@dataclass
class Homework:
    """
    作业主体实体模型
    :param homework_id: 作业全局唯一ID
    :param student_id: 学生ID
    :param questions: 题目列表
    :param student_answers: 学生作答答案字典 {题目ID: 学生答案}
    :param status: 当前作业流转状态
    :param ai_score: AI自动批改得分
    :param final_score: 人工复核后最终得分
    :param review_comment: 人工复核评语
    :param create_time: 作业创建时间戳
    :param update_time: 作业最后更新时间戳
    """
    homework_id: str
    student_id: str
    questions: List[Question]
    student_answers: Dict[str, str]
    status: HomeworkStatus
    ai_score: Optional[int] = None
    final_score: Optional[int] = None
    review_comment: Optional[str] = None
    create_time: float = time.time()
    update_time: float = time.time()

# ==============================================
# 持久化层 Persistence
# 设计：模拟 PostgreSQL(落库持久化) + Redis(高速缓存)
# 能力：状态落地存储、缓存加速查询、断点续传数据支撑
# ==============================================
class Persistence:
    """
    持久化管理类
    - 数据库：存储全量作业数据，保证断电/服务重启不丢失
    - 缓存：热点作业状态缓存，提升查询性能
    """
    def __init__(self):
        # 模拟PostgreSQL 持久化数据库
        self.homework_db: Dict[str, Dict] = {}
        # 模拟Redis 内存缓存，用于高频状态查询
        self.redis_cache: Dict[str, Any] = {}

    def save_homework(self, homework: Homework) -> None:
        """
        保存作业数据
        1. 更新最后修改时间
        2. 同步写入数据库 + 缓存
        :param homework: 作业实例
        """
        homework.update_time = time.time()
        data = asdict(homework)
        self.homework_db[homework.homework_id] = data
        self.redis_cache[f"homework:{homework.homework_id}"] = data

    def get_homework(self, homework_id: str) -> Optional[Homework]:
        """
        查询作业信息
        缓存优先策略：先查Redis，未命中再查数据库
        :param homework_id: 作业ID
        :return: 作业实例 / None
        """
        cache_key = f"homework:{homework_id}"
        cache_data = self.redis_cache.get(cache_key)
        if cache_data:
            return Homework(**cache_data)
        db_data = self.homework_db.get(homework_id)
        return Homework(**db_data) if db_data else None

# ==============================================
# 观察者通知层 Observer
# 设计模式：观察者模式
# 能力：状态变更解耦，统一推送UI、日志、监控、Webhook
# ==============================================
class Observer(ABC):
    """观察者抽象父类，统一通知接口规范"""
    @abstractmethod
    def update(self, homework: Homework) -> None:
        """状态变更触发更新回调"""
        pass


class UIUpdateObserver(Observer):
    """前端UI实时更新观察者，用于学生/教师页面进度展示"""
    def update(self, homework: Homework) -> None:
        print(f"【UI实时通知】作业[{homework.homework_id}] 状态变更：{homework.status.value}")


class LogObserver(Observer):
    """系统日志观察者，全链路操作留痕，满足教育行业合规要求"""
    def update(self, homework: Homework) -> None:
        log_info = {
            "homework_id": homework.homework_id,
            "student_id": homework.student_id,
            "status": homework.status.value,
            "timestamp": round(time.time(), 2)
        }
        print(f"【系统日志记录】{json.dumps(log_info, ensure_ascii=False)}")


class WebhookObserver(Observer):
    """第三方回调观察者，对接教务系统、家校平台"""
    def update(self, homework: Homework) -> None:
        print(f"【Webhook回调】外部系统推送：作业{homework.homework_id} 状态={homework.status.value}")


class NotificationCenter:
    """
    通知中心调度器
    统一管理所有观察者，批量触发状态变更通知
    支持动态增删观察者，实现功能热插拔
    """
    def __init__(self):
        self.observers: List[Observer] = []

    def add_observer(self, observer: Observer) -> None:
        """注册观察者"""
        self.observers.append(observer)

    def notify_all(self, homework: Homework) -> None:
        """广播状态变更，通知所有订阅者"""
        for observer in self.observers:
            observer.update(homework)

# ==============================================
# 管道处理层 Pipeline
# 设计模式：责任链/流水线模式
# 能力：分段解耦、阶段可扩展、支持并行与热插拔
# 流程：接收 → 解析 → 特征提取 → AI批改 → 后处理
# ==============================================
class PipelineStage(ABC):
    """流水线阶段抽象类，约束每个处理阶段统一入参出参"""
    @abstractmethod
    def process(self, homework: Homework) -> Homework:
        """单阶段处理逻辑"""
        pass


class ReceiveStage(PipelineStage):
    """阶段1：作业接收，初始化状态"""
    def process(self, homework: Homework) -> Homework:
        homework.status = HomeworkStatus.RECEIVED
        return homework


class ParseStage(PipelineStage):
    """阶段2：作业解析 + 特征提取，结构化清洗作答数据"""
    def process(self, homework: Homework) -> Homework:
        homework.status = HomeworkStatus.PARSING
        time.sleep(0.2)  # 模拟文本解析、图片OCR耗时
        homework.status = HomeworkStatus.ANALYZING
        return homework


class AIGradingStage(PipelineStage):
    """
    阶段3：AI智能批改核心逻辑
    差异化批改策略：
    - 选择题：精准匹配判分
    - 填空题：文本精准匹配
    - 解答题：语义相似度、关键词匹配AI模糊判分
    """
    def __init__(self):
        self.total_score = 0

    def _grade_choice(self, std_ans: str, stu_ans: str, score: int) -> int:
        """选择题批改：完全一致得分"""
        return score if std_ans.strip() == stu_ans.strip() else 0

    def _grade_fill_blank(self, std_ans: str, stu_ans: str, score: int) -> int:
        """填空题批改：文本精准匹配"""
        return score if std_ans.strip() == stu_ans.strip() else 0

    def _grade_answer(self, std_ans: str, stu_ans: str, score: int) -> int:
        """解答题AI批改：关键词匹配，模拟大模型语义理解"""
        std_key = set(std_ans[:6])
        stu_key = set(stu_ans[:6])
        return score if std_key & stu_key else score // 2

    def process(self, homework: Homework) -> Homework:
        homework.status = HomeworkStatus.GRADING
        total = 0
        # 遍历所有题目批量批改
        for question in homework.questions:
            answer = homework.student_answers.get(question.q_id, "")
            if question.q_type == QuestionType.CHOICE:
                total += self._grade_choice(question.standard_answer, answer, question.score)
            elif question.q_type == QuestionType.FILL_BLANK:
                total += self._grade_fill_blank(question.standard_answer, answer, question.score)
            elif question.q_type == QuestionType.ANSWER:
                total += self._grade_answer(question.standard_answer, answer, question.score)
        homework.ai_score = total
        homework.status = HomeworkStatus.CORRECTING
        return homework


class PostProcessStage(PipelineStage):
    """
    阶段4：后处理 + 人工复核
    AI批改完成后流转至人工审核环节，保证批改准确率
    """
    def process(self, homework: Homework) -> Homework:
        homework.status = HomeworkStatus.REVIEWING
        time.sleep(0.2)  # 模拟教师人工复核操作
        # 人工复核默认采信AI得分，实际业务可手动修改分数
        homework.final_score = homework.ai_score
        homework.review_comment = "成都教育科技-人工复核通过，批改有效"
        homework.status = HomeworkStatus.COMPLETED
        return homework


class Pipeline:
    """
    批改流水线总调度
    按顺序串联全处理阶段，支持阶段动态插拔、并行扩展
    """
    def __init__(self):
        # 初始化完整处理链路
        self.stages = [
            ReceiveStage(),
            ParseStage(),
            AIGradingStage(),
            PostProcessStage()
        ]

    def execute(self, homework: Homework) -> Homework:
        """串行执行全流水线"""
        for stage in self.stages:
            homework = stage.process(homework)
        return homework

# ==============================================
# 状态管理层 State Machine
# 核心能力：状态严格流转控制、断点续传、状态持久化联动
# ==============================================
class StateManager:
    """
    状态机管理器
    1. 管控作业合法状态流转
    2. 状态变更自动持久化+消息通知
    3. 提供断点续传恢复能力
    """
    def __init__(self, persistence: Persistence, notify_center: NotificationCenter):
        self.persistence = persistence    # 持久化依赖
        self.notify_center = notify_center# 消息通知依赖

    def update_state(self, homework: Homework, status: HomeworkStatus) -> None:
        """
        更新作业状态
        :param homework: 作业实例
        :param status: 目标新状态
        """
        homework.status = status
        self.persistence.save_homework(homework)
        self.notify_center.notify_all(homework)

    def resume_homework(self, homework_id: str) -> Optional[Homework]:
        """
        断点续传核心方法
        服务重启/异常中断后，根据作业ID恢复历史进度
        """
        homework = self.persistence.get_homework(homework_id)
        if homework:
            print(f"【断点续传恢复】作业ID:{homework_id} 当前滞留状态:{homework.status.value}")
        return homework

# ==============================================
# 接入层 API Gateway
# 企业级能力：JWT认证、请求路由、权限控制、限流熔断(预留)
# 对外统一入口，隔离下层业务实现
# ==============================================
class APIGateway:
    """
    统一API网关
    对外提供作业提交、批改查询、任务执行接口
    内置JWT身份鉴权，防止未授权访问
    """
    def __init__(self, state_manager: StateManager, pipeline: Pipeline):
        self.state_manager = state_manager
        self.pipeline = pipeline

    def create_token(self, user_id: str) -> str:
        """
        生成JWT令牌
        :param user_id: 操作人ID
        :return: 加密Token字符串
        """
        payload = {"user_id": user_id, "create_time": time.time()}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def verify_token(self, token: str) -> bool:
        """
        令牌合法性校验
        :param token: 客户端请求令牌
        :return: 校验通过True / 失败False
        """
        try:
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return True
        except jwt.ExpiredSignatureError:
            print("Token已过期")
            return False
        except jwt.InvalidTokenError:
            print("非法Token")
            return False

    def submit_homework(self, token: str, student_id: str, questions: List[Question], answers: Dict[str, str]) -> str:
        """
        作业提交接口
        :param token: 身份令牌
        :param student_id: 学生ID
        :param questions: 题目列表
        :param answers: 学生作答答案
        :return: 生成的作业唯一ID
        """
        # 身份拦截
        if not self.verify_token(token):
            raise PermissionError("身份认证失败，禁止提交作业")
        # 生成全局唯一作业ID
        homework_id = f"CDHW_{uuid.uuid4().hex[:8].upper()}"
        # 初始化作业实例
        homework = Homework(
            homework_id=homework_id,
            student_id=student_id,
            questions=questions,
            student_answers=answers,
            status=HomeworkStatus.RECEIVED
        )
        # 落地存储+初始状态通知
        self.state_manager.persistence.save_homework(homework)
        self.state_manager.notify_center.notify_all(homework)
        return homework_id

    def grade_homework(self, homework_id: str) -> Homework:
        """
        触发AI批改任务接口
        :param homework_id: 待批改作业ID
        :return: 批改完成后的完整作业实例
        """
        homework = self.state_manager.persistence.get_homework(homework_id)
        if not homework:
            raise FileNotFoundError("作业不存在或已过期")
        # 执行全流水线批改
        homework = self.pipeline.execute(homework)
        # 最终结果持久化
        self.state_manager.persistence.save_homework(homework)
        self.state_manager.notify_center.notify_all(homework)
        return homework

# ==============================================
# 系统入口 & 业务测试用例
# 模拟完整业务链路：认证→提交→AI批改→人工复核→断点恢复
# ==============================================
def main():
    """系统主入口，完整业务流程演示"""
    # 1. 底层依赖组件初始化
    persistence = Persistence()
    notify_center = NotificationCenter()
    state_manager = StateManager(persistence, notify_center)
    pipeline = Pipeline()
    api_gateway = APIGateway(state_manager, pipeline)

    # 2. 注册全量观察者，开启全链路通知
    notify_center.add_observer(UIUpdateObserver())
    notify_center.add_observer(LogObserver())
    notify_center.add_observer(WebhookObserver())

    # 3. 构造测试题库：覆盖三种题型
    test_questions = [
        Question(
            q_id="Q001",
            q_type=QuestionType.CHOICE,
            content="1+1等于几？",
            standard_answer="2",
            score=10
        ),
        Question(
            q_id="Q002",
            q_type=QuestionType.FILL_BLANK,
            content="Python属于____编程语言",
            standard_answer="解释型",
            score=20
        ),
        Question(
            q_id="Q003",
            q_type=QuestionType.ANSWER,
            content="简述面向对象三大特性",
            standard_answer="封装、继承、多态",
            score=30
        )
    ]

    # 4. 模拟学生作答数据
    student_answer_data = {
        "Q001": "2",
        "Q002": "解释型",
        "Q003": "封装、继承、多态三大核心特性"
    }

    # 5. 模拟师生登录，签发JWT
    user_token = api_gateway.create_token("TEA_CD001")
    print(f"✅ 身份认证通过，JWT令牌：{user_token[:30]}...")

    # 6. 提交作业
    hw_id = api_gateway.submit_homework(user_token, "STU_CD10086", test_questions, student_answer_data)
    print(f"✅ 作业提交成功，作业编号：{hw_id}")

    # 7. 执行AI+人工全流程批改
    print("\n========== 开始智能批改流程 ==========")
    result_homework = api_gateway.grade_homework(hw_id)

    # 8. 断点续传功能演示
    print("\n========== 断点续传测试 ==========")
    resume_hw = state_manager.resume_homework(hw_id)

    # 9. 输出最终批改结果
    print("\n========== 批改结果汇总 ==========")
    print(f"作业编号：{resume_hw.homework_id}")
    print(f"AI自动得分：{resume_hw.ai_score}")
    print(f"最终复核得分：{resume_hw.final_score}")
    print(f"复核评语：{resume_hw.review_comment}")
    print(f"当前状态：{resume_hw.status.value}")


if __name__ == "__main__":
    main()