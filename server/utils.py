#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/5/13 14:39
@source from: 
"""
import asyncio
import logging
import os
import pydantic
from pydantic import BaseModel
from typing import List
from fastapi import FastAPI
from pathlib import Path
from typing import Literal, Optional, Callable, Generator, Dict, Any, Awaitable, Union, Tuple
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI, AzureOpenAI, Anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed

#wrap_done 的作用是确保：无论 task_fn 成功或出错，最终都会 event.set() 通知外部，“我这个任务结束了”，这样不会卡住等待的逻辑。

#该函数的作用就是当被包裹的函数出现异常的时候，其他的任务还可以正常进行。
async def wrap_done(fn:Awaitable,event:asyncio.Event):
    try:
        await fn
    except Exception as e:
        msg = f"Caught exception: {e}"
        print(f'{e.__class__.__name__}: {msg}')
    finally:
        event.set()

def get_ChatOpenAI(
        model_name: str,
        temperature: float,
        max_tokens: int = None,
        streaming: bool = True,
        callbacks: List[Callable] = [],
        verbose: bool = True,
        **kwargs: Any,
):
    model = ChatOpenAI(
        streaming=streaming,
        verbose=verbose,
        callbacks=callbacks,
        openai_api_key='',
        openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model_name="qwen-plus",
        temperature=0.7,
        max_tokens=max_tokens,
        **kwargs
    )
    return model
class BaseResponse(BaseModel):
    code : int = pydantic.Field(200,description='')
    msg : str = pydantic.Field('success',description='')
    data : Any = pydantic.Field(None,description='')

    class Config:
        schema_extra = {
            'example': {
                'code':200,
                'msg':'success',
            }
        }
class ListResponse(BaseResponse):#用于构建统一的响应对象。无论成功还是失败，响应的结构都统一，这有助于客户端处理响应。
    data: List[str] = pydantic.Field(..., description="List of names")

    class Config:
        schema_extra = {
            "example": {
                "code": 200,
                "msg": "success",
                "data": ["doc1.docx", "doc2.pdf", "doc3.txt"],
            }
        }

def torch_gc():
    try:
        import torch
        if torch.cuda.is_available():
            # with torch.cuda.device(DEVICE):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        elif torch.backends.mps.is_available():
            try:
                from torch.mps import empty_cache
                empty_cache()
            except Exception as e:
                msg = ("如果您使用的是 macOS 建议将 pytorch 版本升级至 2.0.0 或更高版本，"
                       "以支持及时清理 torch 产生的内存占用。")
                print(msg)
    except Exception:
        ...


def MakeFastAPIOffline(
        app: FastAPI,
        static_dir=Path(__file__).parent / "static",
        static_url="/static-offline-docs",
        docs_url: Optional[str] = "/docs",
        redoc_url: Optional[str] = "/redoc",
) -> None:
    """patch the FastAPI obj that doesn't rely on CDN for the documentation page"""
    from fastapi import Request
    from fastapi.openapi.docs import (
        get_redoc_html,
        get_swagger_ui_html,
        get_swagger_ui_oauth2_redirect_html,
    )
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import HTMLResponse

    openapi_url = app.openapi_url
    swagger_ui_oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url

    def remove_route(url: str) -> None:
        '''
        remove original route from app
        '''
        index = None
        for i, r in enumerate(app.routes):
            if r.path.lower() == url.lower():
                index = i
                break
        if isinstance(index, int):
            app.routes.pop(index)

    # Set up static file mount
    app.mount(
        static_url,
        StaticFiles(directory=Path(static_dir).as_posix()),
        name="static-offline-docs",
    )

    if docs_url is not None:
        remove_route(docs_url)
        remove_route(swagger_ui_oauth2_redirect_url)

        # Define the doc and redoc pages, pointing at the right files
        @app.get(docs_url, include_in_schema=False)
        async def custom_swagger_ui_html(request: Request) -> HTMLResponse:
            root = request.scope.get("root_path")
            favicon = f"{root}{static_url}/favicon.png"
            return get_swagger_ui_html(
                openapi_url=f"{root}{openapi_url}",
                title=app.title + " - Swagger UI",
                oauth2_redirect_url=swagger_ui_oauth2_redirect_url,
                swagger_js_url=f"{root}{static_url}/swagger-ui-bundle.js",
                swagger_css_url=f"{root}{static_url}/swagger-ui.css",
                swagger_favicon_url=favicon,
            )

        @app.get(swagger_ui_oauth2_redirect_url, include_in_schema=False)
        async def swagger_ui_redirect() -> HTMLResponse:
            return get_swagger_ui_oauth2_redirect_html()

    if redoc_url is not None:
        remove_route(redoc_url)

        @app.get(redoc_url, include_in_schema=False)
        async def redoc_html(request: Request) -> HTMLResponse:
            root = request.scope.get("root_path")
            favicon = f"{root}{static_url}/favicon.png"

            return get_redoc_html(
                openapi_url=f"{root}{openapi_url}",
                title=app.title + " - ReDoc",
                redoc_js_url=f"{root}{static_url}/redoc.standalone.js",
                with_google_fonts=False,
                redoc_favicon_url=favicon,
            )

def get_prompt_template(type:str,name:str) -> Optional[str]:
    '''
        从prompt_config中加载模板内容
        type:
        "llm_chat","agent_chat","knowledge_base_chat","search_engine_chat"
        的其中一种，如果有新功能，应该进行加入。
    '''
    from configs import prompt_config
    import importlib#引入 importlib 模块，用于动态导入和操作模块
    importlib.reload(prompt_config)#能强制重新载入文件内容，重新执行模块内的代码。
    return prompt_config.PROMPT_TEMPLATES[type].get(name)




def run_in_thread_pool(
        func: Callable,
        params: List[Dict] = [],
) -> Generator:
    '''
    在线程池中批量运行任务，并将运行结果以生成器的形式返回。
    请确保任务中的所有操作是线程安全的，任务函数请全部使用关键字参数。
    '''
    tasks = []
    with ThreadPoolExecutor() as pool:
        for kwargs in params:
            thread = pool.submit(func, **kwargs)
            tasks.append(thread)

        for obj in as_completed(tasks):  # TODO: Ctrl+c无法停止
            yield obj.result()



