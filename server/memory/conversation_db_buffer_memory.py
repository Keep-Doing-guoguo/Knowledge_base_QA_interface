#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/5/13 16:03
@source from: 
"""
from typing import Any, List, Dict

from langchain.memory.chat_memory import BaseChatMemory
from langchain.schema import get_buffer_string, BaseMessage, HumanMessage, AIMessage
from langchain.schema.language_model import BaseLanguageModel
from server.db.repository.message_repository import filter_message

class ConversationBufferDBMemory(BaseChatMemory):
    conversation_id :str
    human_prefix:str = 'Human'
    ai_prefix:str = 'Assistant'
    llm:BaseLanguageModel
    memory_key :str = 'history'
    max_token_limit:int =2000
    message_limit :int = 10

    @property
    def buffer(self)->List[BaseMessage]:
        messages = filter_message(conversatinon_id = self.conversation_id,limit=self.message_limit)

        messages = list(reversed(messages))

        chat_messages:List[BaseMessage] = []

        for message in messages:
            chat_messages.append(HumanMessage(content=message['query']))
            chat_messages.append(AIMessage(content=message['response']))

        if not chat_messages:
            return []

        #提炼chat message，如果它超过最大的token限制。
        curr_buffer_length = self.llm.get_num_tokens(get_buffer_string(chat_messages))

        if curr_buffer_length > self.max_token_limit:
            pruned_memory = []
            while curr_buffer_length > self.max_token_limit and chat_messages:
                pruned_memory.append(chat_messages.pop(0))#始终将第一条消息pop出去。
                curr_buffer_length = self.llm.get_num_tokens(get_buffer_string(chat_messages))


        return chat_messages


    @property
    def memory_variables(self) -> list[str]:

        return [self.memory_key]

    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
        buffer:Any = self.buffer

        if self.return_messages:
            final_buffer:Any = buffer
        else:
            final_buffer = get_buffer_string(
                buffer,
                human_prefix=self.human_prefix,
                ai_prefix=self.ai_prefix
            )
        return {self.memory_key:final_buffer}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Nothing should be saved or changed"""
        pass

    def clear(self) -> None:
        """Nothing to clear, got a memory like a vault."""
        pass

