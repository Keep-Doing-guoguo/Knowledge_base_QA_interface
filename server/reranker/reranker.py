#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/6/30 14:41
@source from: 
"""
import datetime
import requests
from typing import Sequence, Optional, Any
from pydantic import Field, PrivateAttr
from langchain.schema import Document
from langchain_core.callbacks.base import Callbacks
from langchain.retrievers.document_compressors.base import BaseDocumentCompressor


class LangchainReranker(BaseDocumentCompressor):
    """Document compressor that uses external rerank API (e.g. Cohere, SiliconFlow)."""

    model_name_or_path: str = Field()
    _model: Any = PrivateAttr(default=None)  # 不再使用
    top_n: int = Field()
    device: str = Field()
    max_length: int = Field()
    batch_size: int = Field()
    num_workers: int = Field()

    def __init__(self,
                 model_name_or_path: str,
                 top_n: int = 3,
                 device: str = "cuda",
                 max_length: int = 1024,
                 batch_size: int = 32,
                 num_workers: int = 0):
        self.model_name_or_path = model_name_or_path
        self.top_n = top_n
        self.device = device
        self.max_length = max_length
        self.batch_size = batch_size
        self.num_workers = num_workers
        self._model = None  # 不再使用本地模型

    def call_rerank_api(self, query: str, docs: Sequence[str]) -> Sequence[float]:
        """
        调用远程 rerank API 获取每个文档的相关性分数。
        """
        url = "https://api.siliconflow.cn/v1/rerank"
        headers = {
            "Authorization": "Bearer sk-xuabveedydrxkanzbbiwienzsceltpsralfdblujmxiuzbcz",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "BAAI/bge-reranker-v2-m3",
            "query": query,
            "documents": docs,
            "top_n": len(docs),
            "return_documents": False,
            "max_chunks_per_doc": 1024,
            "overlap_tokens": 80
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return [r["relevance_score"] for r in response.json()["results"]]
        else:
            raise RuntimeError(f"API Error: {response.status_code} - {response.text}")

    def compress_documents(
            self,
            documents: Sequence[Document],
            query: str,
            callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        """
        Compress documents using remote rerank API.

        Returns:
            Top-N scored documents with relevance_score in metadata.
        """
        if len(documents) == 0:
            return []

        doc_list = list(documents)
        texts = [d.page_content for d in doc_list]

        # 调用 API 获取分数
        scores = self.call_rerank_api(query, texts)

        # topk 逻辑等价于原来的 topk
        scored_docs = list(zip(doc_list, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        top_k = min(self.top_n, len(scored_docs))
        final_results = []
        for doc, score in scored_docs[:top_k]:
            doc.metadata["relevance_score"] = score
            final_results.append(doc)

        return final_results