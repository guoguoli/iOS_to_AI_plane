"""
配置管理模块
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置"""
    
    # 通义千问配置
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    QWEN_MODEL: str = "qwen-plus"  # qwen-turbo / qwen-plus / qwen-max
    EMBEDDING_MODEL: str = "text-embedding-v2"
    
    # 向量数据库配置
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"
    COLLECTION_NAME: str = "education_kb"
    
    # 分块配置
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # 检索配置
    TOP_K: int = 3  # 检索返回数量
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置完整性"""
        if not cls.DASHSCOPE_API_KEY:
            print("⚠️  警告: DASHSCOPE_API_KEY 未设置")
            print("   请在 .env 文件中设置: DASHSCOPE_API_KEY=your_api_key")
            return False
        return True

# 全局配置实例
config = Config()
