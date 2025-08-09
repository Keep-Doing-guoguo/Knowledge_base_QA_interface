
#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/5/13 15:43
@source from: 
"""
#=======

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
from langchain.prompts import PromptTemplate
from server.utils import get_prompt_template


#=======

from pydantic import BaseModel,Field

from langchain.prompts.chat import ChatMessagePromptTemplate
from typing import List,Tuple,Dict,Union
#表示值可以是 str 类型或 None，相当于 Union[str, None]
#表示值可以是 str 或 int 类型，支持多个类型的联合

class History(BaseModel):
    role:str = Field(...)
    content:str = Field(...)

    def to_msg_tuple(self):
        return 'ai' if self.role=='assistant' else 'human',self.content

    def to_msg_template(self,is_raw=True) -> ChatMessagePromptTemplate:

        role_maps = {
            'ai':'assistant',
            'human':'user',
        }

        role = role_maps.get(self.role,self.role)#如果 self.role 存在于 role_maps，就返回映射后的值；否则返回原值。

        if is_raw:
            content = "{% raw %}" + self.content + "{% endraw %}"
        else:
            content = self.content

        return ChatMessagePromptTemplate.from_template(
            content,
            template_format="jinja2",
            role=role
        )
    @classmethod
    def from_data(cls,h:Union[List,Tuple, Dict]) -> "History":#这是一个类方法（@classmethod），所以 cls 代表类本身，而不是实例。支持输入三种数据结构：list、tuple、dict。
        if isinstance(h, (list,tuple)) and len(h) >= 2:
            h = cls(role=h[0], content=h[1])#如果传入的是列表或元组（长度 ≥ 2），将第一个元素当作角色 role，第二个元素当作内容 content。
        elif isinstance(h, dict):
            h = cls(**h)#如果是字典，直接使用关键字参数初始化，例如 {"role": "user", "content": "hi"}。

        return h#	•	最后返回构建好的 History 实例。

b = History.from_data(["user", "你好"])       # OK ✅。变成了History类
b1 = History.from_data(("ai", "你好呀"))      # OK ✅
b2 = History.from_data({"role": "user", "content": "hi"})  # OK ✅
history_test = [b,b1,b2]
print(History)


##############history##############
history = [History(role='user', content='我们来玩成语接龙，我先来，生龙活虎'), History(role='assistant', content='虎头虎脑')]
history = [History.from_data(h) for h in history]
prompt_template = get_prompt_template('llm_chat','default')#default：{{ input }}
input_msg = History(role='user',content=prompt_template).to_msg_template(False)
#a = input_msg.to_msg_template(False)
chat_prompt = ChatPromptTemplate.from_messages(
                [i.to_msg_template() for i in history] + [input_msg]
            )
'''
情况一：使用 is_raw=False ✅（正确）
=======
msg = History(role='user', content='{{ input }}').to_msg_template(False)
ChatPromptTemplate.from_messages([... , msg]).format_messages(input='你好')
渲染后大模型看到的是：
Human: 你好

情况二：使用 is_raw=True ❌（错误）
msg = History(role='user', content='{{ input }}').to_msg_template(True)
实际内容变成：
Human: {% raw %}{{ input }}{% endraw %}
LangChain 会把它当作纯文本，最终大模型接收到：
Human: {{ input }}
❗ 这时候 {{ input }} 不会被替换，模型看到的是变量名原样，效果就不对了。

=======
最终的chat_prompt：

ChatPromptTemplate.from_messages([
    ChatMessagePromptTemplate(role="user", content="{% raw %}我们来玩成语接龙，我先来，生龙活虎{% endraw %}"),
    ChatMessagePromptTemplate(role="assistant", content="{% raw %}虎头虎脑{% endraw %}"),
    ChatMessagePromptTemplate(role="user", content="（你当前的 prompt_template 内容）")
])


[
  {"role": "user", "content": "我们来玩成语接龙，我先来，生龙活虎"},
  {"role": "assistant", "content": "虎头虎脑"},
  {"role": "user", "content": "（你的prompt模板，比如 '请接上一个成语'）"}
]
'''
#print(history)#with_history

##############conversation_id and history_len > 0##############
# prompt = get_prompt_template('llm_chat','with_history')
# chat_prompt = PromptTemplate.from_template(prompt)
# # memory = ConversationBufferDBMemory(conversation_id=conversation_id,llm=model,message_limit = history_len)#
#
# ##############else##############
# prompt_template = get_prompt_template('llm_chat','prompt_name')
# input_msg = History(role='user',content=prompt_template).to_msg_template(False)#因为这里直接嗲用的提示词。提示词里面已经使用了{{input}}
# chat_prompt = ChatPromptTemplate.from_messages([input_msg])#只是ChatPromptTemplate的方法调用。