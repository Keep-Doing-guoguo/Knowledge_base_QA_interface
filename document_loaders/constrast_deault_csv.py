#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/6/27 10:50
@source from: 
"""
from langchain.document_loaders import CSVLoader


path = '/Volumes/PSSD/未命名文件夹/donwload/创建知识库数据库/document_loaders/test.csv'
loader = CSVLoader(file_path=path)
docs = loader.load()
print(docs[0].page_content)


#FilteredCSVLoader

from document_loaders import FilteredCSVloader
loader = FilteredCSVloader(
    file_path="test.csv",
    columns_to_read=["question"],
    metadata_columns=["category"],
    autodetect_encoding=True
)
docs = loader.load()
print(docs[0].page_content)  # -> What is LangChain?
print(docs[0].metadata)      # -> {'source': 'test.csv', 'row': 0, 'category': 'AI'}

'''

特性
FilteredCSVLoader
CSVLoader (默认)
是否选择列
✅ 是，只读取 columns_to_read
❌ 否，默认全部读取
是否支持元数据指定
✅ 是，支持 metadata_columns
❌ 否，默认无
是否易于嵌入检索任务
✅ 更清晰简洁
❌ 需额外处理字段分割
输出内容是否干净
✅ page_content 很纯粹
❌ 含多个字段拼接

'''