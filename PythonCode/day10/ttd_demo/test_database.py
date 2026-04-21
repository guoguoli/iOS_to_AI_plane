# test_database.py
# SQLAlchemy测试文档：https://docs.sqlalchemy.org/

from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import pytest

# ============================================
# 数据库配置
# ============================================

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite特定
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 定义模型
class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    score = Column(Float, default=0.0)

# 创建表
Base.metadata.create_all(bind=engine)

# FastAPI应用
app = FastAPI()

# ============================================
# 依赖：获取数据库会话
# ============================================

def get_db():
    """数据库依赖"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# API路由
# ============================================

@app.post("/students/")
def create_student(name: str, score: float, db: Session = Depends(get_db)):
    """创建学生"""
    db_student = Student(name=name, score=score)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return {"id": db_student.id, "name": name, "score": score}

@app.get("/students/{student_id}")
def get_student(student_id: int, db: Session = Depends(get_db)):
    """获取学生"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    return {"id": student.id, "name": student.name, "score": student.score}

# ============================================
# 测试：使用事务回滚
# ============================================

client = TestClient(app)

def test_create_and_get_student():
    """测试创建和获取学生（使用事务回滚）"""
    # 创建测试会话
    db = TestingSessionLocal()
    
    # 开始事务
    transaction = db.begin()
    
    try:
        # 测试创建
        response = client.post("/students/?name=测试学生&score=88.5")
        assert response.status_code == 200
        student_id = response.json()["id"]
        
        # 测试获取
        response = client.get(f"/students/{student_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "测试学生"
        
        # 回滚事务（测试数据不保存）
        transaction.rollback()
    finally:
        db.close()

# ============================================
# 更优雅的方式：使用Fixture
# ============================================

@pytest.fixture
def test_db():
    """测试数据库Fixture"""
    connection = engine.connect()
    transaction = connection.begin()
    
    # 使用绑定会话
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

def test_with_fixture(test_db):
    """使用Fixture的测试"""
    # 创建学生
    student = Student(name="Fixture学生", score=92.0)
    test_db.add(student)
    test_db.commit()
    test_db.refresh(student)
    
    # 查询学生
    result = test_db.query(Student).filter(Student.name == "Fixture学生").first()
    
    # 数据存在（仅在测试事务内）
    assert result is not None
    assert result.score == 92.0
    
    # 事务回滚后，数据不存在
# 运行所有测试
if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])