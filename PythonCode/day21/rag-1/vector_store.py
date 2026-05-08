"""
向量数据库管理 - 使用Chroma
"""
import os
from typing import List, Optional, Dict, Any
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain_core.documents import Document
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma

from config import config


class VectorStoreManager:
    """向量存储管理器"""
    
    def __init__(
        self,
        persist_directory: str = None,
        collection_name: str = "education_kb"
    ):
        self.persist_directory = persist_directory or config.CHROMA_PERSIST_DIR
        self.collection_name = collection_name
        
        # 初始化嵌入模型（通义千问）
        self.embeddings = DashScopeEmbeddings(
            model=config.EMBEDDING_MODEL,
            dash_api_key=config.DASHSCOPE_API_KEY
        )
        
        # 确保目录存在
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # 初始化向量存储
        self._vectorstore: Optional[Chroma] = None
    
    @property
    def vectorstore(self) -> Chroma:
        """获取或创建向量存储"""
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                client=self._get_client(),
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )
        return self._vectorstore
    
    def _get_client(self) -> chromadb.PersistentClient:
        """获取Chroma客户端"""
        return chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
    
    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档列表
            ids: 可选的ID列表
        
        Returns:
            添加的文档ID列表
        """
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        # 添加文档
        self.vectorstore.add_documents(documents, ids=ids)
        
        # 持久化
        self.vectorstore.persist()
        
        return ids
    
    def search(
        self,
        query: str,
        k: int = 3,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        相似度检索
        
        Args:
            query: 查询文本
            k: 返回数量
            filter_dict: 元数据过滤条件
        
        Returns:
            相似文档列表
        """
        return self.vectorstore.similarity_search(
            query=query,
            k=k,
            filter=filter_dict
        )
    
    def search_with_score(
        self,
        query: str,
        k: int = 3,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """
        带分数的相似度检索
        
        Returns:
            [(Document, score), ...]
        """
        return self.vectorstore.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter_dict
        )
    
    def delete(self, ids: List[str]) -> None:
        """删除文档"""
        self.vectorstore.delete(ids=ids)
        self.vectorstore.persist()
    
    def clear(self) -> None:
        """清空集合"""
        self._vectorstore.delete_collection()
        self._vectorstore = None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        collection = self.vectorstore._collection
        return {
            "name": self.collection_name,
            "count": collection.count(),
            "persist_directory": self.persist_directory
        }


# 全局实例
_vector_store: Optional[VectorStoreManager] = None


def get_vector_store() -> VectorStoreManager:
    """获取全局向量存储实例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreManager()
    return _vector_store