"""嵌入模型封装 - text-embedding-v4 2048维（兼容阿里云MaaS）"""
import os
from typing import List
from openai import OpenAI
from langchain_core.embeddings import Embeddings
from core.config import settings


class AlibabaEmbeddings(Embeddings):
    """
    阿里云MaaS嵌入模型封装
    直接使用OpenAI SDK调用，兼容text-embedding-v4
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=60.0,
        )
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
        self.batch_size = settings.embedding_batch_size

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量嵌入文档（分批处理，每批最多10条）
        :param texts: 文本列表
        :return: 向量列表
        """
        all_embeddings = []
        # 过滤空文本
        valid_texts = [t if t and t.strip() else " " for t in texts]
        for i in range(0, len(valid_texts), self.batch_size):
            batch = valid_texts[i:i + self.batch_size]
            create_kwargs = {"model": self.model, "input": batch}
            if self.dimensions and self.dimensions > 0:
                create_kwargs["dimensions"] = self.dimensions
            response = self.client.embeddings.create(**create_kwargs)
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        嵌入单条查询文本
        :param text: 查询文本
        :return: 向量
        """
        create_kwargs = {
            "model": self.model,
            "input": text if text and text.strip() else " ",
        }
        if self.dimensions and self.dimensions > 0:
            create_kwargs["dimensions"] = self.dimensions
        response = self.client.embeddings.create(**create_kwargs)
        return response.data[0].embedding


def get_embeddings() -> Embeddings:
    """获取嵌入模型实例"""
    return AlibabaEmbeddings()
