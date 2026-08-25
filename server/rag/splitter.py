"""文本分块器"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.config import settings


def split_text(text: str) -> list[str]:
    """
    将文本分割为多个块
    :param text: 原始文本
    :return: 文本块列表
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
    )
    return splitter.split_text(text)
