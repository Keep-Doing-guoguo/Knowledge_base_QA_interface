#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/6/30 10:57
@source from: 
"""
from langchain.docstore.document import Document
from configs import logger,EMBEDDING_MODEL,EMBEDDING_API_KEY
from server.utils import BaseResponse
from fastapi import Body
from fastapi.concurrency import run_in_threadpool
from typing import Dict, List

import httpx


# === 配置 ===
EMBEDDING_API_URL = "https://api.siliconflow.cn/v1/embeddings"

from typing import List, Any
import requests

# 假设这个是你已有的函数
def call_embedding(prompt):
    url = "https://api.siliconflow.cn/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {EMBEDDING_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "BAAI/bge-large-zh-v1.5",
        "input": f"{prompt}",
        "encoding_format": "float"
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['data'][0]['embedding']
    else:
        return response.status_code

# BaseResponse 定义

# ✅ 你需要的 embed_texts 实现
# ✅ 非 async 的同步 embedding 批处理函数（线程池会调用这个）
def embed_texts(texts: List[str], embed_model: str, to_query: bool = False) -> BaseResponse:
    try:
        embeddings = []
        for text in texts:
            embeddings.append(call_embedding(text))
        return BaseResponse(data=embeddings)
    except Exception as e:
        logger.error(e)
        return BaseResponse(code=500, msg=f"文本向量化过程中出现错误：{e}")

# ✅ async 包装，模拟你之前的结构
# === 异步单条文本请求 ===
async def async_call_embedding(text: str, client: httpx.AsyncClient):
    try:
        payload = {
            "model": EMBEDDING_MODEL,
            "input": text,
            "encoding_format": "float"
        }
        headers = {
            "Authorization": f"Bearer {EMBEDDING_API_KEY}",
            "Content-Type": "application/json"
        }
        resp = await client.post(EMBEDDING_API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()['data'][0]['embedding']
    except Exception as e:
        return f"Error: {e}"


# === 并发处理多个文本 ===
async def async_embed_texts(texts: List[str]) -> BaseResponse:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            tasks = [async_call_embedding(text, client) for text in texts]
            results = await asyncio.gather(*tasks)

        # 检查是否有错误
        if any(isinstance(r, str) and r.startswith("Error") for r in results):
            return BaseResponse(code=500, msg="部分请求失败", data=results)

        return BaseResponse(code=200, msg="success", data=results)

    except Exception as e:
        return BaseResponse(code=500, msg=f"向量化异常：{e}")
def embed_texts_endpoint(
        texts: List[str] = Body(..., description="要嵌入的文本列表", examples=[["hello", "world"]]),
        embed_model: str = Body(EMBEDDING_MODEL,
                                description=f"使用的嵌入模型，除了本地部署的Embedding模型，也支持在线API()提供的嵌入服务。"),
        to_query: bool = Body(False, description="向量是否用于查询。有些模型如Minimax对存储/查询的向量进行了区分优化。"),
) -> BaseResponse:
    '''
    对文本进行向量化，返回 BaseResponse(data=List[List[float]])
    '''
    return embed_texts(texts=texts, embed_model=embed_model, to_query=to_query)


def embed_documents(
        docs: List[Document],
        embed_model: str = EMBEDDING_MODEL,
        to_query: bool = False,
) -> Dict:
    """
    将 List[Document] 向量化，转化为 VectorStore.add_embeddings 可以接受的参数
    """
    texts = [x.page_content for x in docs]
    metadatas = [x.metadata for x in docs]
    embeddings = embed_texts(texts=texts, embed_model=embed_model, to_query=to_query).data
    if embeddings is not None:
        return {
            "texts": texts,
            "embeddings": embeddings,
            "metadatas": metadatas,
        }
import asyncio
from langchain.docstore.document import Document

def main():
    print("===== ✅ 测试 embed_texts 同步版本 =====")
    sync_resp = embed_texts(["你好", "世界"], embed_model=EMBEDDING_MODEL)
    print("同步返回结果：", sync_resp.json())

    print("\n===== ✅ 测试 embed_documents 同步封装 =====")
    docs = [
        Document(page_content="这是第一个文档", metadata={"id": 1}),
        Document(page_content="这是第二个文档", metadata={"id": 2})
    ]
    doc_result = embed_documents(docs)
    print("文档嵌入结果：")
    print(doc_result)

    print("\n===== ✅ 测试 embed_texts_endpoint 接口封装 =====")
    endpoint_resp = embed_texts_endpoint(["测试", "接口"])
    print("接口封装返回：", endpoint_resp.json())

    print("\n===== ✅ 测试 aembed_texts 异步版本 =====")
    asyncio.run(test_async_embed())


async def test_async_embed():
    aresp = await async_embed_texts(["异步", "向量化测试"])
    print("异步返回结果：", aresp.json())


if __name__ == "__main__":
    main()