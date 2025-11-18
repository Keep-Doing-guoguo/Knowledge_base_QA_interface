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

from server.utils import (BaseResponse, ListResponse, FastAPI, MakeFastAPIOffline)
from typing import List, Literal

async def document():
    return RedirectResponse(url="/docs")


def create_app(run_mode: str = None):
    app = FastAPI(
        title="API Server",
    )
    MakeFastAPIOffline(app)


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
    from server.chat.knowledge_base_chat import knowledge_base_chat
    from server.knowledge_base.kb_doc_api import ( upload_docs

                                                )

    app.post("/chat/knowledge_base_chat",
             tags=["Chat"],
             summary="与知识库对话")(knowledge_base_chat)#该接口可以使用，但是并没有检索到内容。



    app.post("/knowledge_base/upload_docs",
             tags=["Knowledge Base Management"],
             response_model=BaseResponse,
             summary="上传文件到知识库，并/或进行向量化"
             )(upload_docs)#该接口可以正常使用；针对的是单线程的情况。




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
    parser.add_argument("--host", type=str, default="127.0.0.1")
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
