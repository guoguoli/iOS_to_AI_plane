"""
RAG管道 - 检索增强生成
"""
import json
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass
from datetime import datetime

import dashscope
from dashscope import Generation
# from dashscope.common.api_key import api_key as DASHSCOPE_API_KEY

from config import config
from document_loader import DocumentLoader
from text_chunker import TextChunker, SmartChunker
from vector_store import VectorStoreManager


@dataclass
class RetrievalResult:
    """检索结果"""
    content: str
    metadata: Dict[str, Any]
    score: float
    source: str


@dataclass
class RAGResponse:
    """RAG响应"""
    answer: str
    sources: List[RetrievalResult]
    usage: Dict[str, int]
    latency: float


class RAGPipeline:
    """RAG管道"""
    
    def __init__(
        self,
        vector_store: Optional[VectorStoreManager] = None,
        top_k: int = 3
    ):
        self.vector_store = vector_store or VectorStoreManager()
        self.top_k = top_k
        
        # 设置API Key
        dashscope.api_key = config.DASHSCOPE_API_KEY
    
    def load_and_index(
        self,
        directory: str,
        use_smart_chunking: bool = True
    ) -> int:
        """
        加载并索引文档
        
        Args:
            directory: 文档目录
            use_smart_chunking: 是否使用智能分块
        
        Returns:
            索引的文档数量
        """
        print(f"📂 加载文档: {directory}")
        
        # 加载文档
        loader = DocumentLoader()
        loaded_docs = loader.load_directory(directory)
        
        if not loaded_docs:
            print("⚠️  未找到文档")
            return 0
        
        # 转换为LangChain格式
        from langchain_core.documents import Document
        documents = [
            Document(page_content=doc.content, metadata=doc.metadata)
            for doc in loaded_docs
        ]
        
        print(f"📄 共加载 {len(documents)} 个文档")
        
        # 分块
        print("✂️  分块处理...")
        if use_smart_chunking:
            chunks = SmartChunker.chunk(documents)
        else:
            chunker = TextChunker(
                chunk_size=config.CHUNK_SIZE,
                chunk_overlap=config.CHUNK_OVERLAP
            )
            chunks = chunker.chunk_documents(documents)
        
        print(f"📦 生成 {len(chunks)} 个文本块")
        
        # 索引
        print("🔍 向量化索引...")
        self.vector_store.add_documents(chunks)
        
        print(f"✅ 索引完成！")
        return len(chunks)
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[RetrievalResult]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回数量
        
        Returns:
            检索结果列表
        """
        k = top_k or self.top_k
        
        # 执行检索
        results = self.vector_store.search_with_score(query, k=k)
        
        retrieval_results = []
        for doc, score in results:
            retrieval_results.append(RetrievalResult(
                content=doc.page_content,
                metadata=doc.metadata,
                score=score,
                source=doc.metadata.get("source_file", "unknown")
            ))
        
        return retrieval_results
    
    def build_prompt(
        self,
        query: str,
        contexts: List[RetrievalResult],
        include_sources: bool = True
    ) -> str:
        """
        构建RAG提示词
        
        Args:
            query: 用户问题
            contexts: 检索到的上下文
            include_sources: 是否包含来源信息
        
        Returns:
            完整的提示词
        """
        # 构建上下文
        context_text = "\n\n".join([
            f"【文档{i+1}】{ctx.content}"
            for i, ctx in enumerate(contexts)
        ])
        
        # 构建提示词
        prompt = f"""你是一个专业的教育助手，基于给定的参考资料回答用户问题。

要求：
1. 只使用参考资料中的信息回答问题
2. 如果参考资料中没有相关信息，请明确说明"根据现有资料无法回答这个问题"
3. 回答要准确、清晰、专业
4. 如果涉及多个知识点，请分点说明

参考资料：
{context_text}

用户问题：{query}

回答："""
        
        if include_sources:
            prompt += "\n\n参考来源：\n" + "\n".join([
                f"- {ctx.source}"
                for ctx in contexts
            ])
        
        return prompt
    
    def generate(self, query: str, use_rag: bool = True) -> RAGResponse:
        """
        生成回答
        
        Args:
            query: 用户问题
            use_rag: 是否使用RAG
        
        Returns:
            RAG响应
        """
        import time
        start_time = time.time()
        
        contexts = []
        prompt = query
        
        if use_rag:
            # 1. 检索
            contexts = self.retrieve(query)
            
            if contexts:
                # 2. 构建提示词
                prompt = self.build_prompt(query, contexts)
            else:
                print("⚠️  未检索到相关文档，使用普通模式")
        
        # 3. 调用通义千问
        response = Generation.call(
            model=config.QWEN_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            result_format="message",
            temperature=0.7,
            max_tokens=1000
        )
        
        latency = time.time() - start_time
        
        if response.status_code != 200:
            raise Exception(f"API调用失败: {response.message}")
        
        answer = response.output.choices[0].message.content
        usage = {
            "input_tokens": response.usage.get("input_tokens", 0),
            "output_tokens": response.usage.get("output_tokens", 0)
        }
        
        return RAGResponse(
            answer=answer,
            sources=contexts,
            usage=usage,
            latency=latency
        )
    
    async def generate_stream(
        self,
        query: str,
        use_rag: bool = True
    ) -> AsyncIterator[str]:
        """
        流式生成回答
        
        Args:
            query: 用户问题
            use_rag: 是否使用RAG
        
        Yields:
            生成的文本片段
        """
        contexts = []
        prompt = query
        
        if use_rag:
            contexts = self.retrieve(query)
            if contexts:
                prompt = self.build_prompt(query, contexts)
        
        # 通义千问流式调用
        responses = Generation.call(
            model=config.QWEN_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            result_format="message",
            stream=True,
            temperature=0.7,
            max_tokens=1000
        )
        
        for response in responses:
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                if content:
                    yield content
            else:
                yield f"\n[错误: {response.message}]"
                break


# 便捷函数
def create_rag_pipeline() -> RAGPipeline:
    """创建RAG管道"""
    vector_store = VectorStoreManager(
        persist_directory=config.CHROMA_PERSIST_DIR,
        collection_name=config.COLLECTION_NAME
    )
    return RAGPipeline(vector_store=vector_store, top_k=config.TOP_K)