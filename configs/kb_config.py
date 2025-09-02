#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/5/12 22:17
@source from: 
"""
import os
# 缓存向量库数量（针对FAISS）
CACHED_VS_NUM = 1

# 缓存临时向量库数量（针对FAISS），用于文件对话
CACHED_MEMO_VS_NUM = 10

KB_ROOT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base")
if not os.path.exists(KB_ROOT_PATH):
    os.mkdir(KB_ROOT_PATH)#
DB_ROOT_PATH = os.path.join(KB_ROOT_PATH,"info.db")
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_ROOT_PATH}"

print(os.path.dirname(__file__))#这个会输出当前文件的目录所在位置；
print(os.path.dirname(os.path.dirname(__file__)))#输出当前文件的所在目录。
print(SQLALCHEMY_DATABASE_URI)

# 是否开启中文标题加强，以及标题增强的相关配置
# 通过增加标题判断，判断哪些文本为标题，并在metadata中进行标记；
# 然后将文本与往上一级的标题进行拼合，实现文本信息的增强。
ZH_TITLE_ENHANCE = False
# TextSplitter配置项，如果你不明白其中的含义，就不要修改。

# 知识库中单段文本长度(不适用MarkdownHeaderTextSplitter)
CHUNK_SIZE = 250
DEFAULT_VS_TYPE = "milvus"
# 知识库中相邻文本重合长度(不适用MarkdownHeaderTextSplitter)
OVERLAP_SIZE = 50
# 可选向量库类型及对应配置
kbs_config = {

    "milvus": {
        "host": "10.40.100.16",
        "port": "9997",
        "user": "neo4j",
        "password": "neo4j",
        "secure": False,
    },
    "milvus_kwargs": {
        "index_params": {"index_type": "IVF_FLAT", "metric_type": "L2", "params": {"nlist": 128}},
        "search_params": {"metric_type": "L2", "params": {"nprobe": 10}}
    }
}
KB_INFO = {
    "知识库名称": "知识库介绍",
    "samples": "关于本项目issue的解答",
}
path = '/Volumes/'
VECTOR_SEARCH_TOP_K = 3
SCORE_THRESHOLD = 0.6

# TextSplitter配置项，如果你不明白其中的含义，就不要修改。
text_splitter_dict = {
    "ChineseRecursiveTextSplitter": {
        "source": "huggingface",   # 选择tiktoken则使用openai的方法
        "tokenizer_name_or_path": "",
    },
    "SpacyTextSplitter": {
        "source": "huggingface",
        "tokenizer_name_or_path": "gpt2",
    },
    "RecursiveCharacterTextSplitter": {
        "source": "tiktoken",
        "tokenizer_name_or_path": "cl100k_base",
    },
    "MarkdownHeaderTextSplitter": {
        "headers_to_split_on":
            [
                ("#", "head1"),
                ("##", "head2"),
                ("###", "head3"),
                ("####", "head4"),
            ]
    },
}

# TEXT_SPLITTER 名称
TEXT_SPLITTER_NAME = "RecursiveCharacterTextSplitter"