"""
文档加载器 - 支持多种格式
"""
import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
import json

# 文档类型
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    TextLoader,
    PyMuPDFLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader
)


@dataclass
class LoadedDocument:
    """加载的文档"""
    content: str
    metadata: dict
    source: str


class DocumentLoader:
    """通用文档加载器"""
    
    # 支持的格式
    SUPPORTED_EXTENSIONS = {
        '.txt': 'text',
        '.md': 'markdown',
        '.html': 'html',
        '.pdf': 'pdf',
        '.json': 'json'
    }
    
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding
        self._loaders = {
            'text': self._load_text,
            'markdown': self._load_markdown,
            'html': self._load_html,
            'pdf': self._load_pdf,
            'json': self._load_json
        }
    
    def load(self, file_path: str) -> LoadedDocument:
        """加载单个文档"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"不支持的文件格式: {ext}")
        
        doc_type = self.SUPPORTED_EXTENSIONS[ext]
        loader = self._loaders[doc_type]
        
        return loader(path)
    
    def load_directory(self, directory: str) -> List[LoadedDocument]:
        """加载目录下所有支持的文档"""
        docs = []
        path = Path(directory)
        
        for ext, doc_type in self.SUPPORTED_EXTENSIONS.items():
            for file_path in path.rglob(f"*{ext}"):
                try:
                    doc = self.load(str(file_path))
                    docs.append(doc)
                    print(f"✅ 加载: {file_path.name}")
                except Exception as e:
                    print(f"❌ 加载失败: {file_path.name} - {e}")
        
        return docs
    
    def _load_text(self, path: Path) -> LoadedDocument:
        """加载文本文件"""
        with open(path, 'r', encoding=self.encoding) as f:
            content = f.read()
        
        return LoadedDocument(
            content=content,
            metadata={"source": "text", "file_name": path.name},
            source=str(path)
        )
    
    def _load_markdown(self, path: Path) -> LoadedDocument:
        """加载Markdown文件"""
        loader = UnstructuredMarkdownLoader(str(path))
        docs = loader.load()
        doc = docs[0]
        
        return LoadedDocument(
            content=doc.page_content,
            metadata={**doc.metadata, "source": "markdown"},
            source=str(path)
        )
    
    def _load_html(self, path: Path) -> LoadedDocument:
        """加载HTML文件"""
        loader = UnstructuredHTMLLoader(str(path))
        docs = loader.load()
        doc = docs[0]
        
        return LoadedDocument(
            content=doc.page_content,
            metadata={**doc.metadata, "source": "html"},
            source=str(path)
        )
    
    def _load_pdf(self, path: Path) -> LoadedDocument:
        """加载PDF文件"""
        loader = PyMuPDFLoader(str(path))
        docs = loader.load()
        
        # 合并所有页面
        content = "\n\n".join([doc.page_content for doc in docs])
        
        return LoadedDocument(
            content=content,
            metadata={**docs[0].metadata, "source": "pdf", "pages": len(docs)},
            source=str(path)
        )
    
    def _load_json(self, path: Path) -> LoadedDocument:
        """加载JSON文件（FAQ格式）"""
        with open(path, 'r', encoding=self.encoding) as f:
            data = json.load(f)
        
        # 假设JSON是FAQ格式: [{"question": ..., "answer": ...}]
        if isinstance(data, list):
            content = "\n\n".join([
                f"Q: {item.get('question', '')}\nA: {item.get('answer', '')}"
                for item in data
            ])
        else:
            content = json.dumps(data, ensure_ascii=False, indent=2)
        
        return LoadedDocument(
            content=content,
            metadata={"source": "json", "records": len(data) if isinstance(data, list) else 1},
            source=str(path)
        )


# 便捷函数
def load_education_docs(directory: str) -> List[Document]:
    """加载教育相关文档并转换为LangChain Document格式"""
    loader = DocumentLoader()
    loaded_docs = loader.load_directory(directory)
    
    documents = []
    for doc in loaded_docs:
        documents.append(Document(
            page_content=doc.content,
            metadata={
                **doc.metadata,
                "source_file": doc.source
            }
        ))
    
    return documents