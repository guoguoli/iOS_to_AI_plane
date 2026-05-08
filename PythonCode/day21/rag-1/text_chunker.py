"""
文本分块器 - 多种分块策略
"""
from typing import List, Callable, Optional
from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownTextSplitter,
    PythonCodeTextSplitter,
    TokenTextSplitter
)


class TextChunker:
    """文本分块器"""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        length_function: Optional[Callable] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function or len
        
        # 默认分块器（按字符）
        self.default_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self.length_function,   # 修复：使用 self.length_function 而非原始的 None
            separators=["\n\n", "\n", "。", "！", "？", " ", ""]
        )
    
    def chunk_documents(
        self,
        documents: List[Document],
        strategy: str = "default"
    ) -> List[Document]:
        """
        对文档进行分块
        
        Args:
            documents: 原始文档列表
            strategy: 分块策略
                - "default": 递归字符分块（通用）
                - "markdown": Markdown感知分块
                - "code": 代码分块
                - "semantic": 语义分块（按段落）
        
        Returns:
            分块后的文档列表
        """
        if strategy == "markdown":
            splitter = MarkdownTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        elif strategy == "code":
            splitter = PythonCodeTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        elif strategy == "semantic":
            # 语义分块：先按段落分割，再合并小段落
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""],
                is_separator_regex=False
            )
        else:
            splitter = self.default_splitter
        
        return splitter.split_documents(documents)
    
    def chunk_by_token(
        self,
        documents: List[Document],
        encoding_name: str = "cl100k_base"
    ) -> List[Document]:
        """基于Token数量的分块（更精确）"""
        try:
            import tiktoken
            encoding = tiktoken.get_encoding(encoding_name)
            
            def token_length(text: str) -> int:
                return len(encoding.encode(text))
            
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=token_length,
                separators=["\n\n", "\n", "。", "！", "？", " ", ""]
            )
            
            return splitter.split_documents(documents)
        except ImportError:
            print("⚠️  tiktoken未安装，使用字符分块")
            return self.chunk_documents(documents)


class SmartChunker:
    """智能分块器 - 根据文档类型自动选择策略"""
    
    # 文档类型识别模式
    TYPE_PATTERNS = {
        "markdown": [r"^#\s", r"^\*\*.+?\*\*", r"```"],
        "code": [r"^def\s", r"^class\s", r"^import\s", r"^from\s"],
        "qa": [r"^Q:", r"^A:", r"^\d+\.\s"]
    }
    
    @classmethod
    def detect_type(cls, content: str) -> str:
        """检测文档类型"""
        import re
        
        for doc_type, patterns in cls.TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.MULTILINE):
                    return doc_type
        
        return "default"
    
    @classmethod
    def chunk(cls, documents: List[Document]) -> List[Document]:
        """智能分块"""
        chunker = TextChunker()
        result = []
        
        for doc in documents:
            doc_type = cls.detect_type(doc.page_content)
            
            if doc_type == "markdown":
                chunks = chunker.chunk_documents([doc], strategy="markdown")
            elif doc_type == "code":
                chunks = chunker.chunk_documents([doc], strategy="code")
            elif doc_type == "qa":
                # QA文档：按问答对分割
                chunks = cls._chunk_qa(doc)
            else:
                chunks = chunker.chunk_documents([doc])
            
            result.extend(chunks)
        
        return result
    
    @classmethod
    def _chunk_qa(cls, doc: Document) -> List[Document]:
        """问答对分块"""
        import re
        
        content = doc.page_content
        # 匹配问答对
        pattern = r'(?:^|\n)(Q:|问题|问)[：:]\s*(.+?)\n(?:A:|答案|答)[：:]\s*(.+?)(?=\n(?:Q:|问题|问)|$)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if not matches:
            # 没有匹配到，使用默认分块
            chunker = TextChunker()
            return chunker.chunk_documents([doc])
        
        chunks = []
        for i, (q_label, question, answer) in enumerate(matches):
            qa_text = f"问题：{question.strip()}\n答案：{answer.strip()}"
            chunks.append(Document(
                page_content=qa_text,
                metadata={**doc.metadata, "qa_index": i, "doc_type": "qa"}
            ))
        
        return chunks