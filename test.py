#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/8/28 11:05
@source from: 
"""
from pymilvus import connections
connections.connect("default", host="", port="9997")
print('debug')