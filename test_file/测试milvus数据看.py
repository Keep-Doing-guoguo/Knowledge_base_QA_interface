#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/8/28 11:05
@source from: 
"""
from pymilvus import connections
connections.connect("default", host="10.40.100.16", port="9997")
print('debug')