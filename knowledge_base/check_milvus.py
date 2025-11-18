#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/7/21 11:20
@source from: 
"""
from pymilvus import connections, utility, Collection

# 连接 Milvus 服务
connections.connect("default", host="10.40.100.16", port="9997")

# 查看所有集合
collections = utility.list_collections()
print("📦 所有集合:", collections)

# 查看某个集合的 schema
collection = Collection(name=collections[2])  # 替换成你关心的集合名
print("📄 Schema:", collection.schema)

# 查看字段名称
print("🧬 字段名:", [f.name for f in collection.schema.fields])

# 查看前 5 条数据
# collection.load()
# results = collection.query(expr="", output_fields=["*"], limit=5)
# for row in results:
#     print(row)

####
from pymilvus import connections, Collection

# 连接 Milvus
connections.connect("default", host="10.40.100.16", port="9997")

# 连接集合
collection = Collection("samples")

# 打印 schema
print("集合 Schema:", collection.schema)

# 打印字段名
print("字段名:", [f.name for f in collection.schema.fields])
print("总行数:", collection.num_entities)

# 查询所有字段
results = collection.query(
    expr="",
    output_fields=["pk", "source", "text"],  # 想看哪些字段写哪些
    limit=50  # 返回 5 条
)
for r in results:
    print(r)

import numpy as np

# 假设你有一个 1024 维的向量
# dummy_vector = np.random.rand(1024).tolist()
#
# search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
#
# results = collection.search(
#     data=[dummy_vector],
#     anns_field="vector",   # 向量字段名
#     param=search_params,
#     limit=3,
#     output_fields=["pk", "text"]
# )
#
# for r in results[0]:
#     print("score:", r.score, "text:", r.entity.get("text"))


'''

1. source
	•	类型: VARCHAR
	•	含义: 文件来源（通常是文件路径或者文件名）
	•	用途: 方便追踪这段文本来自哪个文档，比如 README.md 或者某个 PDF。

⸻

2. text
	•	类型: VARCHAR
	•	含义: 文本内容（被切分后的 chunk / 段落）
	•	用途: 知识库里真正的自然语言内容，后续可以返回给用户做参考答案。

⸻

3. pk
	•	类型: VARCHAR（主键 Primary Key）
	•	含义: 唯一标识符（每条数据的 ID）
	•	用途: 在数据库里标识这一条记录，比如 uuid 或者自定义的 ID。
👉 因为 auto_id=False，所以你在插入的时候必须自己提供这个 pk，否则会报错（就是你之前遇到的 “A list of valid ids are required when auto_id is False”）。

⸻

4. vector
	•	类型: FLOAT_VECTOR (dim=1024)
	•	含义: 文本对应的 向量表示（embedding）
	•	用途: 用于相似度搜索（比如用户提问时，把问题转成 embedding，然后跟 vector 字段做余弦相似度/内积/L2 距离匹配）。


'''