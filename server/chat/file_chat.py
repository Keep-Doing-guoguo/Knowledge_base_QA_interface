from fastapi import Body, File, Form, UploadFile
from sse_starlette.sse import EventSourceResponse
from configs import (LLM_MODELS, VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD, TEMPERATURE,
                     CHUNK_SIZE, OVERLAP_SIZE, ZH_TITLE_ENHANCE)
from server.utils import (wrap_done, get_ChatOpenAI,
                        BaseResponse, get_prompt_template, get_temp_dir, run_in_thread_pool)
from langchain.chains import LLMChain
from langchain.callbacks import AsyncIteratorCallbackHandler
from typing import AsyncIterable, List, Optional
import asyncio
from langchain.prompts.chat import ChatPromptTemplate
from server.chat.utils import History
from server.knowledge_base.kb_service.base import EmbeddingsFunAdapter
from server.knowledge_base.utils import KnowledgeFile
import json
import os
from pathlib import Path


def _parse_files_in_thread(
    files: List[UploadFile],
    dir: str,
    zh_title_enhance: bool,
    chunk_size: int,
    chunk_overlap: int,
):
    """
    通过多线程将上传的文件保存到对应目录内。
    生成器返回保存结果：[success or error, filename, msg, docs]
    """
    def parse_file(file: UploadFile) -> dict:
        '''
        保存单个文件。
        '''
        try:
            filename = file.filename
            file_path = os.path.join(dir, filename)
            file_content = file.file.read()  # 读取上传文件的内容

            if not os.path.isdir(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            with open(file_path, "wb") as f:
                f.write(file_content)
            kb_file = KnowledgeFile(filename=filename, knowledge_base_name="temp")
            kb_file.filepath = file_path
            docs = kb_file.file2text(zh_title_enhance=zh_title_enhance,
                                     chunk_size=chunk_size,
                                     chunk_overlap=chunk_overlap)
            return True, filename, f"成功上传文件 {filename}", docs
        except Exception as e:
            msg = f"{filename} 文件上传失败，报错信息为: {e}"
            return False, filename, msg, []

    params = [{"file": file} for file in files]
    for result in run_in_thread_pool(parse_file, params=params):#代码通过 run_in_thread_pool 函数将 parse_file 函数分配到多个线程中执行。run_in_thread_pool 函数接受要处理的函数和对应的参数列表。
        yield result


def upload_temp_docs(
    files: List[UploadFile] = File(..., description="上传文件，支持多文件"),
    prev_id: str = Form(None, description="前知识库ID"),
    chunk_size: int = Form(CHUNK_SIZE, description="知识库中单段文本最大长度"),
    chunk_overlap: int = Form(OVERLAP_SIZE, description="知识库中相邻文本重合长度"),
    zh_title_enhance: bool = Form(ZH_TITLE_ENHANCE, description="是否开启中文标题加强"),
) -> BaseResponse:
    '''
    将文件保存到临时目录，并进行向量化。
    返回临时目录名称作为ID，同时也是临时向量库的ID。
    '''
    if prev_id is not None:#如果提供了 prev_id，则从 memo_faiss_pool 缓存池中删除对应的旧知识库。这是为了防止新上传的文件与旧的知识库内容混淆。
        memo_faiss_pool.pop(prev_id)

    failed_files = []# 用于记录处理失败的文件信息。
    documents = []#用于存储成功解析出的文档片段，这些片段将被添加到向量数据库中。
    path, id = get_temp_dir(prev_id)#调用 get_temp_dir 函数获取一个临时目录路径 path，并生成或重用一个唯一的知识库 id。
    for success, file, msg, docs in _parse_files_in_thread(files=files,
                                                        dir=path,
                                                        zh_title_enhance=zh_title_enhance,
                                                        chunk_size=chunk_size,
                                                        chunk_overlap=chunk_overlap):#生成器函数来逐个处理上传的文件。
        if success:
            documents += docs
        else:
            failed_files.append({file: msg})#每个文件处理成功与否会返回一个 success 标志，如果成功则将解析出的文档片段 docs 添加到 documents 列表中，否则将失败信息 msg 和对应文件名记录到 failed_files 列表中。

    with memo_faiss_pool.load_vector_store(id).acquire() as vs:
        vs.add_documents(documents)#使用 memo_faiss_pool 加载或创建一个新的 FAISS 向量数据库，并将所有成功解析出的文档片段添加到数据库中。
    return BaseResponse(data={"id": id, "failed_files": failed_files})


async def file_chat(query: str = Body(..., description="用户输入", examples=["你好"]),
                    knowledge_id: str = Body(..., description="临时知识库ID"),
                    top_k: int = Body(VECTOR_SEARCH_TOP_K, description="匹配向量数"),
                    score_threshold: float = Body(SCORE_THRESHOLD, description="知识库匹配相关度阈值，取值范围在0-1之间，SCORE越小，相关度越高，取到1相当于不筛选，建议设置在0.5左右", ge=0, le=2),
                    history: List[History] = Body([],
                                                description="历史对话",
                                                examples=[[
                                                    {"role": "user",
                                                    "content": "我们来玩成语接龙，我先来，生龙活虎"},
                                                    {"role": "assistant",
                                                    "content": "虎头虎脑"}]]
                                                ),
                    stream: bool = Body(False, description="流式输出"),
                    model_name: str = Body(LLM_MODELS[0], description="LLM 模型名称。"),
                    temperature: float = Body(TEMPERATURE, description="LLM 采样温度", ge=0.0, le=1.0),
                    max_tokens: Optional[int] = Body(None, description="限制LLM生成Token数量，默认None代表模型最大值"),
                    prompt_name: str = Body("default", description="使用的prompt模板名称(在configs/prompt_config.py中配置)"),
                ):
    if knowledge_id not in memo_faiss_pool.keys():
        return BaseResponse(code=404, msg=f"未找到临时知识库 {knowledge_id}，请先上传文件")#部分代码首先检查传入的 knowledge_id 是否存在于 memo_faiss_pool 缓存中。如果找不到对应的知识库ID，函数会立即返回一个 404 错误，提示用户先上传文件以创建知识库。

    history = [History.from_data(h) for h in history]#这段代码将用户传入的历史对话数据转换为 History 对象列表，以便后续处理。History.from_data() 是一个工厂方法，用于将字典格式的数据转换为 History 类实例。

    async def knowledge_base_chat_iterator() -> AsyncIterable[str]:#是一个异步生成器，用于逐步生成和返回与用户查询相关的内容。这种生成器在处理流式输出时非常有用。
        nonlocal max_tokens
        callback = AsyncIteratorCallbackHandler()#创建一个 AsyncIteratorCallbackHandler 实例，用于处理生成器的回调事件。这个就是用来做流式输出的。
        if isinstance(max_tokens, int) and max_tokens <= 0:
            max_tokens = None

        model = get_ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            callbacks=[callback],
        )
        embed_func = EmbeddingsFunAdapter()#使用适配器模式创建一个嵌入函数，以将用户查询转换为向量表示。
        embeddings = await embed_func.aembed_query(query)#在临时知识库中，根据查询向量进行相似度搜索，返回与查询内容最相关的文档。
        with memo_faiss_pool.acquire(knowledge_id) as vs:
            docs = vs.similarity_search_with_score_by_vector(embeddings, k=top_k, score_threshold=score_threshold)
            docs = [x[0] for x in docs]#筛选出与查询最相关的文档，并按相似度排序。返回的文档将用于生成回答。


        context = "\n".join([doc.page_content for doc in docs])#将所有相关文档的内容拼接成一个上下文字符串，作为生成回答的基础。
        if len(docs) == 0: ## 如果没有找到相关文档，使用Empty模板
            prompt_template = get_prompt_template("knowledge_base_chat", "empty")#根据是否找到相关文档，选择适当的提示模板。如果没有找到相关文档，则使用 empty 模板。
        else:
            prompt_template = get_prompt_template("knowledge_base_chat", prompt_name)
        input_msg = History(role="user", content=prompt_template).to_msg_template(False)
        chat_prompt = ChatPromptTemplate.from_messages(
            [i.to_msg_template() for i in history] + [input_msg])

        chain = LLMChain(prompt=chat_prompt, llm=model)

        # Begin a task that runs in the background.
        task = asyncio.create_task(wrap_done(
            chain.acall({"context": context, "question": query}),
            callback.done),
        )#启动一个异步任务，使用 wrap_done 包装后的任务会在完成时通知回调处理器。

        source_documents = []
        for inum, doc in enumerate(docs):
            filename = doc.metadata.get("source")
            text = f"""出处 [{inum + 1}] [{filename}] \n\n{doc.page_content}\n\n"""
            source_documents.append(text)#将相关文档的内容和来源信息整理成一个列表，便于后续输出。

        if len(source_documents) == 0: # 没有找到相关文档
            source_documents.append(f"""<span style='color:red'>未找到相关文档,该回答为大模型自身能力解答！</span>""")

        if stream:#如果 stream 参数为 True，系统会逐步生成和发送回答内容。生成的每一部分内容都会通过 SSE（Server-Sent Events）推送给客户端。
            async for token in callback.aiter():
                # Use server-sent-events to stream the response
                yield json.dumps({"answer": token}, ensure_ascii=False)
            yield json.dumps({"docs": source_documents}, ensure_ascii=False)
        else:#如果 stream 为 False，系统会先生成完整的回答，然后一次性返回给客户端。
            answer = ""
            async for token in callback.aiter():
                answer += token
            yield json.dumps({"answer": answer,
                              "docs": source_documents},
                             ensure_ascii=False)
        await task#等待异步任务完成，确保所有处理步骤都已执行完毕。

    return EventSourceResponse(knowledge_base_chat_iterator())#，file_chat 函数返回一个 EventSourceResponse，用于处理流式数据传输。如果使用流式输出，生成器会逐步推送内容；否则，返回完整的 JSON 响应。
