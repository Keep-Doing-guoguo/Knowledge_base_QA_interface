#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/5/13 14:00
@source from: 
"""
from server.db.session import with_session
from typing import Dict,List
import uuid
from server.db.models.message_model import MessageModel

@with_session
def add_message_to_db(session,conversation_id:str,chat_type,query,response="",message_id=None,
                      metadata:Dict={}):
    '''
    新增聊天记录
    1.	你调用 add_message_to_db(...)，无需传 session。
	2.	@with_session 会自动创建 session，传给函数。
	3.	函数内部调用 session.add(...)，操作数据库。
	4.	函数返回后，装饰器会自动 commit() 或 rollback()。
    :param session:
    :param conversation_id:
    :param chat_type:
    :param query:
    :param response:
    :param message_id:
    :param metadata:
    :return:
    '''
    if not message_id:
        message_id = uuid.uuid4().hex#生成一个 唯一的消息 ID，以 32 个十六进制字符组成的字符串形式。加上hex表示去掉中间的-
    m = MessageModel(id=message_id,chat_type=chat_type,query=query,response=response,
                     conversation_id=conversation_id,
                     meta_data=metadata)
    session.add(m)
    session.commit()
    return m.id
    pass

@with_session
def updata_message(session,message_id,response:str=None,metadata:Dict=None):
    '''
    更新已有的聊天记录
    :param session:
    :param message_id:
    :param response:
    :param metadata:
    :return:
    '''
    m = get_message_by_id(message_id)
    if m is not None:
        if response is not None:
            m.response = response
        if isinstance(metadata,dict):
            m.meta_data = metadata

        session.add(m)
        session.commit()
        return m.id


@with_session
def get_message_by_id(session,message_id) -> MessageModel:
    '''

    查找聊天记录
    :param session:
    :param message_id:
    :return:
    '''
    m = session.query(MessageModel).filter_by(id=message_id).first()
    return m



@with_session
def feedback_message_to_db():
    """
        反馈聊天记录
    """
    pass

@with_session
def filter_message(session,conversation_id:str,limit:int = 10):
    '''
    查询10条小心，根据时间排序。并且规定格式。
    :param session:
    :param conversation_id:
    :param limit:
    :return:
    '''
    messages = (session.query(MessageModel).filter_by(conversation_id=conversation_id)
                .filter(MessageModel.response!='')
                .order_by(MessageModel.create_time.desc()).limit(limit).all())

    data = []
    for m in messages:
        data.append({"query":m.query,"response":m.response})

    return data



# def add_message_to_db(conversation_id, chat_type, query, response, meta_data=None,
#                       feedback_score=-1, feedback_reason=''):
#     """
#     添加消息记录到数据库
#     """
#     if meta_data is None:
#         meta_data = {}
#
#     message = MessageModel(
#         id=uuid.uuid4().hex,
#         conversation_id=conversation_id,
#         chat_type=chat_type,
#         query=query,
#         response=response,
#         meta_data=meta_data,
#         feedback_score=feedback_score,
#         feedback_reason=feedback_reason
#     )
#
#     session = SessionLocal()
#     try:
#         session.add(message)
#         session.commit()
#         return message
#     except Exception as e:
#         session.rollback()
#         raise e
#     finally:
#         session.close()

#测试使用
# msg = add_message_to_db(
#     conversation_id="abc123",
#     chat_type="chat",
#     query="你好",
#     response="你好，请问有什么可以帮忙的？",
#     meta_data={"model": "gpt-4"},
#     feedback_score=5,
#     feedback_reason="回答准确"
# )
#
# print("保存成功，message_id:", msg.id)