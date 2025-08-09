#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/5/13 16:42
@source from: 
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult
from server.db.repository import updata_message



class ConversationCallbackHandler(BaseCallbackHandler):
    raise_error :bool = True
    def __init__(self,conversation_id:str,message_id:str,chat_type:str,query:str):
        self.conversation_id = conversation_id
        self.message_id = message_id
        self.chat_type = chat_type
        self.query = query
        self.start_at = None

    @property
    def always_verbose(self) -> bool:
        return True

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        **kwargs: Any,
    ) -> None:
        pass

    def on_chain_end(
        self,
        response:LLMResult,
        **kwargs: Any,
    ) -> None:
        anwser = response.generations[0][0].text

        updata_message(self.message_id,anwser)


