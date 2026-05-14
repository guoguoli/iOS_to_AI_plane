"""
文本预处理的重要性

为什么需要预处理？
1. 去除噪声（特殊字符、HTML标签）
2. 规范化文本（繁简转换、大小写统一）
3. 分句处理（长文本分块）
4. 保留关键信息（不丢失语义）

类比iOS开发:
- 原始数据 → 数据清洗 → 模型训练
- 就像用户输入 → 表单验证 → 保存到数据库
"""

import re
import unicodedata
from typing import list

class TextPreprocessor:
    """文本预处理器"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        清洗文本
        
        Args:
            text: 原始文本
        
        Returns:
            清洗后的文本
        """
        # 1. 去除HTML标签
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 2. 去除特殊字符（保留中文、英文、数字、标点）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s，。！？、；：""''（）《》【】]', ' ', text)
        
        # 3. 去除多余空格
        text = re.sub(r'\s+', ' ', text)
        
        # 4. 去除首尾空格
        text = text.strip()
        
        return text
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        规范化文本
        
        Args:
            text: 原始文本
        
        Returns:
            规范化后的文本
        """
        # 1. Unicode规范化
        text = unicodedata.normalize('NFKC', text)
        
        # 2. 全角转半角
        text = text.replace('（', '(').replace('）', ')')
        text = text.replace('，', ',').replace('。', '.')
        text = text.replace('：', ':').replace('；', ';')
        
        # 3. 英文转小写
        text = text.lower()
        
        return text
    
    @staticmethod
    def split_sentences(text: str) -> list[str]:
        """
        分句
        
        Args:
            text: 输入文本
        
        Returns:
            句子列表
        """
        # 中文分句标点
        delimiters = ['。', '！', '？', '；', '！\n', '？\n', '。\n']
        
        sentences = [text]
        for delimiter in delimiters:
            new_sentences = []
            for sent in sentences:
                new_sentences.extend(sent.split(delimiter))
            sentences = new_sentences
        
        # 过滤空句
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> list[str]:
        """
        文本分块
        
        Args:
            text: 输入文本
            chunk_size: 每块最大字符数
            overlap: 块间重叠字符数
        
        Returns:
            文本块列表
        """
        chunks = []
        
        start = 0
        while start < len(text):
            end = start + chunk_size
            
            # 如果不等于总长度，尝试在句号处分块
            if end < len(text):
                last_period = text.rfind('。', start, end)
                if last_period > start + chunk_size * 0.5:
                    end = last_period + 1
            
            chunks.append(text[start:end].strip())
            start = end - overlap
        
        return chunks
    
    @staticmethod
    def preprocess_pipeline(
        text: str,
        clean: bool = True,
        normalize: bool = True,
        chunk: bool = False,
        chunk_size: int = 500
    ) -> list[str] | str:
        """
        完整的预处理管道
        
        Args:
            text: 原始文本
            clean: 是否清洗
            normalize: 是否规范化
            chunk: 是否分块
            chunk_size: 分块大小
        
        Returns:
            处理后的文本或文本块列表
        """
        if clean:
            text = TextPreprocessor.clean_text(text)
        
        if normalize:
            text = TextPreprocessor.normalize_text(text)
        
        if chunk:
            return TextPreprocessor.chunk_text(text, chunk_size)
        
        return text

# 使用示例
def preprocessing_demo():
    """文本预处理示例"""
    
    # 原始文本（模拟从网页抓取）
    raw_text = """
    <p>二次函数求导是微积分的基础知识点。</p>
    <p>对于函数 f(x) = ax² + bx + c，其导数为 f'(x) = 2ax + b。</p>
    <p>这个公式在高考数学中经常出现！</p>
    """
    
    preprocessor = TextPreprocessor()
    
    # 1. 清洗
    cleaned = preprocessor.clean_text(raw_text)
    print("清洗后:", cleaned)
    
    # 2. 分句
    sentences = preprocessor.split_sentences(cleaned)
    print("分句:", sentences)
    
    # 3. 分块
    chunks = preprocessor.chunk_text(cleaned, chunk_size=100)
    print(f"分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"块{i+1}: {chunk[:50]}...")