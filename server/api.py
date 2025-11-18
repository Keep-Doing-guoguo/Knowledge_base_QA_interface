#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/6/30 14:17
@source from:
"""
import nltk
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import argparse
import uvicorn
from starlette.responses import RedirectResponse


from server.embeddings_api import embed_texts_endpoint

from server.utils import (BaseResponse, ListResponse, FastAPI, MakeFastAPIOffline,get_prompt_template)
from server.knowledge_base.model.kb_document_model import DocumentWithVSId
from server.knowledge_base.kb_doc_api import list_files,search_docs,delete_docs

from typing import List
async def document():
    return RedirectResponse(url="/docs")


def create_app(run_mode: str = None):
    app = FastAPI(
        title="API Server",
    )
    MakeFastAPIOffline(app)
    # ✅ 加上这一段
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    mount_app_routes(app, run_mode=run_mode)
    return app


def mount_app_routes(app: FastAPI, run_mode: str = None):
    app.get("/",
            response_model=BaseResponse,
            summary="swagger 文档")(document)

    # 知识库相关接口
    mount_knowledge_routes(app)

    app.post("/other/embed_texts",
            tags=["Other"],
            summary="将文本向量化，支持本地模型和在线模型",
            )(embed_texts_endpoint)#该接口已经测试，可以正常运行。


def mount_knowledge_routes(app: FastAPI):
    from server.knowledge_base.kb_doc_api import ( upload_docs,

                                            )
    from server.knowledge_base.kb_api import create_kb,delete_kb

    app.post("/knowledge_base/create_knowledge_base",
             tags=["Knowledge Base Management"],
             response_model=BaseResponse,
             summary="创建知识库"
             )(create_kb)#关于知识库的都在kb_api中。

    app.post("/knowledge_base/delete_knowledge_base",
             tags=["Knowledge Base Management"],
             response_model=BaseResponse,
             summary="删除知识库"
             )(delete_kb)#关于知识库的都在kb_api中。

    app.post("/knowledge_base/list_knowledge_bases",
             tags=['Knowledge Base Management'],
             response_model = BaseResponse,
             summary='获取知识库列表')#关于知识库的都在kb_api中。

    app.get("/knowledge_base/list_files",
            tags=["Knowledge Base Management"],
            response_model=ListResponse,
            summary="获取知识库内的文件列表"
            )(list_files)#关于文件的都再kb_doc_api中。

    app.post("/knowledge_base/search_docs",
             tags=["Knowledge Base Management"],
             response_model=List[DocumentWithVSId],
             summary="根据query去知识库文件里面进行检索答案"
             )(search_docs)#关于知识库文件的都放在kb_doc_api# 中。

    app.post("/knowledge_base/upload_docs",
             tags=["Knowledge Base Management"],
             response_model=BaseResponse,
             summary="上传文件到知识库，并/或进行向量化"
             )(upload_docs)#该接口可以正常使用；针对的是单线程的情况。

    app.post("/knowledge_base/delete_docs",
             tags=["Knowledge Base Management"],
             response_model=BaseResponse,
             summary="删除知识库内指定文件"
             )(delete_docs)  # 该接口可以正常使用
def run_api(host, port, **kwargs):
    if kwargs.get("ssl_keyfile") and kwargs.get("ssl_certfile"):
        uvicorn.run(app,
                    host=host,
                    port=port,
                    ssl_keyfile=kwargs.get("ssl_keyfile"),
                    ssl_certfile=kwargs.get("ssl_certfile"),
                    )
    else:
        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='嘿嘿嘿',
                                     description='基于本地知识库的问答')
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7861)
    parser.add_argument("--ssl_keyfile", type=str)
    parser.add_argument("--ssl_certfile", type=str)
    # 初始化消息
    args = parser.parse_args()
    args_dict = vars(args)

    app = create_app()

    run_api(host=args.host,
            port=args.port,
            ssl_keyfile=args.ssl_keyfile,
            ssl_certfile=args.ssl_certfile,
            )
