#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/5/12 22:10
@source from: 
"""
from sqlalchemy import Column,Integer,String,DateTime,JSON,func

from server.db.base import Base

class MessageModel(Base):
    '''
    聊天记录模型

    '''
    __tablename__ = 'message'
    id = Column(String(32),primary_key=True,comment='')
    conversation_id = Column(String(32),default=None,index=True,comment='')

    chat_type  = Column(String(50),comment='')
    query = Column(String(4096),comment='')
    response = Column(String(4096),comment='')

    meta_data = Column(JSON,default={})

    feedback_score = Column(Integer,default=-1,comment='')
    feedback_reason = Column(String(255),default='',comment='')
    create_time = Column(DateTime,default=func.now,comment='')


    def __repr__(self):
        return f"<message(id='{self.id}')"

