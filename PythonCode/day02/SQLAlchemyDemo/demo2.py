from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# 定义模型后，创建表
def init_db():
    """初始化数据库，创建所有表"""
    engine = create_engine("sqlite:///./student.db")
    Base.metadata.create_all(bind=engine)  # 创建所有表
    print("数据库表创建成功！")

# 删除所有表（慎用）
def drop_db():
    """删除所有表"""
    Base.metadata.drop_all(bind=engine)