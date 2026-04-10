from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

# 创建基类
Base = declarative_base()

# ============================================
# SQLAlchemy模型（定义数据库表结构）
# ============================================
class Student(Base):
    """学生表 - 对应数据库中的students表"""
    __tablename__ = "students"  # 表名
    
    # Column(数据类型, 约束)
    id = Column(Integer, primary_key=True, index=True)  # 主键，自增
    student_no = Column(String(20), unique=True, index=True, nullable=False)  # 学号，唯一索引
    name = Column(String(50), nullable=False)  # 姓名，不能为空
    age = Column(Integer, nullable=False)
    gender = Column(String(10))
    phone = Column(String(20))
    email = Column(String(100))
    
    # 关系定义（类似iOS的NSFetchedProperty）
    scores = relationship("Score", back_populates="student", cascade="all, delete-orphan")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 更新时间

class Course(Base):
    """课程表"""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True)
    name = Column(String(100), nullable=False)
    teacher = Column(String(50))
    credit = Column(Float, default=0)  # 学分
    is_active = Column(Boolean, default=True)
    
    # 关系定义
    scores = relationship("Score", back_populates="course")

class Score(Base):
    """成绩表 - 关联学生和课程"""
    __tablename__ = "scores"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 外键 - 关联学生表
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    # 外键 - 关联课程表
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    
    # 成绩字段
    score = Column(Float, nullable=False)  # 分数
    grade = Column(String(2))  # 等级（A/B/C/D/F）
    
    # 关系定义
    student = relationship("Student", back_populates="scores")
    course = relationship("Course", back_populates="scores")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())