from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

# ============================================
# 开发环境：SQLite（轻量，无需安装）
# ============================================
# sqlite:/// = 相对路径
# sqlite://// = 绝对路径
engine = create_engine(
    "sqlite:///./student.db",
    connect_args={"check_same_thread": False}  # SQLite专用，允许多线程访问
)

# ============================================
# 生产环境：PostgreSQL
# ============================================
# 注意：需要安装psycopg2: pip install psycopg2-binary
engine = create_engine(
    "postgresql://username:password@localhost:5432/student_db",
    pool_size=10,      # 连接池大小
    max_overflow=20,  # 超出pool_size的连接数
    pool_pre_ping=True  # 使用前测试连接
)

# ============================================
# 创建会话工厂和基类
# ============================================
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()  # 所有模型的基类
