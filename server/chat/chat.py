#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/5/13 14:36
@source from: 
"""
from fastapi import Body
from sse_starlette.sse import EventSourceResponse
from configs import LLM_MODELS,TEMPERATURE
from langchain.chains import LLMChain
from langchain.callbacks import AsyncIteratorCallbackHandler
from typing import AsyncIterator
import asyncio
import json
from langchain.prompts.chat import ChatPromptTemplate
from typing import List,Optional,Union
from server.chat.utils import History
from langchain.prompts import PromptTemplate
from server.utils import get_prompt_template, get_ChatOpenAI,wrap_done
from server.memory.conversation_db_buffer_memory import ConversationBufferDBMemory
from server.db.repository import add_message_to_db
from server.callback_handler.conversation_callback_handler import ConversationCallbackHandler



async def chat(query:str = Body(...,description='',examples=['你好']),
               conversation_id:str = Body(...,description=''),
               history_len:int = Body(),
               history:Union[int,List[History]] = Body(),
               stream:bool = Body(),
               model_name:str = Body(),
               temperature:float = Body(),
               max_tokens :Optional[int] = Body(),
               prompt_name:str = Body()
               ):


    async def chat_iterator() -> AsyncIterator[str]:
        nonlocal history,max_tokens
        callback = AsyncIteratorCallbackHandler()
        callbacks = [callback]
        memory = None

        message_id = add_message_to_db(chat_type='llm_chat',conversation_id=conversation_id)

        conversation_callback = ConversationCallbackHandler(conversation_id=conversation_id, message_id=message_id,
                                                            chat_type="llm_chat",
                                                            query=query)  # 这里是当聊天结束后将回调函数，然后保存历史聊天记录。
        callbacks.append(conversation_callback)
        if isinstance(max_tokens, int) and max_tokens <= 0:
            max_tokens = None
        print('debug3')
        model = get_ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            callbacks=callbacks,
        )

        if history:#表示从前端拿出来的聊天记录
            history = [History.from_data(h) for h in history]#先拿到数据进行转变
            prompt_template = get_prompt_template('llm_chat',prompt_name)
            input_msg = History(role='user',content=prompt_template).to_msg_template(False)
            chat_prompt = ChatPromptTemplate.from_messages(
                [i.to_msg_template() for i in history] + [input_msg]
            )
        elif conversation_id and history_len > 0:#表示从数据库中拿的聊天记录

            prompt = get_prompt_template('llm_chat','with_history')
            chat_prompt = PromptTemplate.from_template(prompt)
            memory = ConversationBufferDBMemory(conversation_id=conversation_id,llm=model,message_limit = history_len)

        else:#表示没有聊天记录
            prompt_template = get_prompt_template('llm_chat',prompt_name)
            input_msg = History(role='user',content=prompt_template).to_msg_template(False)
            chat_prompt = ChatPromptTemplate.from_messages([input_msg])

        chain = LLMChain(prompt=chat_prompt,llm=model,memory=memory)#LLMChain 内部会自动调用 .format() 或 .format_messages()！
        chain = asyncio.create_task(
            wrap_done(
                chain.acall({"input":query}),
                callback.done,)
        )#这里是创建俩个任务。

        if stream:
            async for token in callback.aiter():
                yield json.dumps({"text":token,"message_id":message_id},ensure_ascii=False)

        else:

            answer = ""
            async for token in callback.aiter():
                answer+=token
            yield json.dumps({"text":token,"message_id":message_id},ensure_ascii=False)
        await chain


    return EventSourceResponse(chat_iterator())
'''
🏁 asyncio.run()
相当于“开赛” → 启动整个异步比赛（事件循环）
🏃 asyncio.create_task()
相当于“让某个选手开始跑” → 在比赛过程中并发多个选手



import asyncio

async def main():
    print("Hello asyncio.run")

asyncio.run(main())
！
import asyncio

async def main():
    print("Hello run_until_complete")

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(main())
loop.close()



'''