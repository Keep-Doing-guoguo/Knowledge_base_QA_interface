#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/10/10 14:28
@source from: 
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
控制台可调试版知识库问答
同步执行，无 FastAPI 依赖。
"""

import json
from urllib.parse import urlencode
from typing import List, Optional

from langchain.chains import LLMChain
from langchain.prompts.chat import ChatPromptTemplate
from langchain.callbacks.base import BaseCallbackHandler

from server.utils import get_ChatOpenAI, get_prompt_template
from server.chat.utils import History
from server.knowledge_base.kb_service.base import KBServiceFactory
from server.knowledge_base.kb_doc_api import search_docs
from server.reranker.reranker import LangchainReranker
from configs import (
    VECTOR_SEARCH_TOP_K,
    SCORE_THRESHOLD,
    TEMPERATURE,
    USE_RERANKER,
    RERANKER_MODEL,
    RERANKER_MAX_LENGTH,
    MODEL_PATH,
)


def knowledge_base_chat_console(
    query: str,
    knowledge_base_name: str = "samples",
    top_k: int = VECTOR_SEARCH_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    history: Optional[List[History]] = None,
    model_name: str = "qwen-plus",
    temperature: float = TEMPERATURE,
    max_tokens: Optional[int] = None,
    prompt_name: str = "default",
):
    """
    同步执行版本：方便在 PyCharm / VSCode 控制台调试。
    """
    print(f"\n🔍 开始知识库问答：{query}")

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        print(f"❌ 未找到知识库：{knowledge_base_name}")
        return

    if history is None:
        history = []

    # 初始化模型
    model = get_ChatOpenAI(
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        callbacks=[],  # 可自定义打印回调
    )

    # 向量检索
    print("📚 检索知识库中相关文档...")
    docs = search_docs(
        query=query,
        knowledge_base_name=knowledge_base_name,
        top_k=top_k,
        score_threshold=score_threshold,
    )
    print(f"检索结果数量: {len(docs)}")

    # Reranker 排序
    if USE_RERANKER:
        reranker_model_path = MODEL_PATH["reranker"].get(RERANKER_MODEL, "BAAI/bge-reranker-large")
        reranker_model = LangchainReranker(
            top_n=top_k,
            device=None,
            max_length=RERANKER_MAX_LENGTH,
            model_name_or_path=reranker_model_path,
        )
        docs = reranker_model.compress_documents(documents=docs, query=query)
        print(f"🔁 Reranker 排序后文档数量: {len(docs)}")

    # 组装上下文
    context = "\n".join([doc.page_content for doc in docs])
    if len(docs) == 0:
        prompt_template = get_prompt_template("knowledge_base_chat", "empty")
    else:
        prompt_template = get_prompt_template("knowledge_base_chat", prompt_name)

    input_msg = History(role="user", content=prompt_template).to_msg_template(False)#转变为ChatMessagePromptTemplate模版
    chat_prompt = ChatPromptTemplate.from_messages([i.to_msg_template() for i in history] + [input_msg])#这里再将其转变为ChatPrompttemplate模版
    chain = LLMChain(prompt=chat_prompt, llm=model)

    # 执行调用
    print("\n🤖 正在调用大模型生成回答...")
    result = chain.run({"context": context, "question": query})
    print("\n✅ 模型回答：")
    print(result)

    # 输出参考文档
    print("\n📖 参考文档：")
    for i, doc in enumerate(docs):
        print(f"[{i + 1}] 来源: {doc.metadata.get('source')}")
        print(f"内容摘要: {doc.page_content[:200]}...\n")

    return result


if __name__ == "__main__":
    query = '新乡工程学院'
    knowledge_base_chat_console(query)