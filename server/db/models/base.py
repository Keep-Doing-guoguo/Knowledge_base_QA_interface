#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/5/12 22:02
@source from: 
"""
from datetime import datetime
from sqlalchemy import Column,DateTime,String,Integer


class BaseModel:
    '''

    基础模型，其实用处并不是很大。
    '''
    id = Column(Integer,primary_key=True,index=True,comment='主键ID')
    create_time = Column(DateTime,default=datetime.utcnow,comment='创建时间')#GANS
    update_time = Column(DateTime,default=None,onupdate=datetime.utcnow(),comment='更新时间')
    create_by = Column(String,default=None,comment='创建者')
    update_by = Column(String,default=None,comment='更新者')