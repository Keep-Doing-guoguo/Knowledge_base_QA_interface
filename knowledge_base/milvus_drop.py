from pymilvus import connections, Collection

# 1️⃣ 连接 Milvus
connections.connect("default", host="10.40.100.16", port="9997")

# 2️⃣ 加载集合
collection_name = "samples"
col = Collection(collection_name)

# 3️⃣ 删除所有记录
# ✅ 这里根据主键 pk 字段条件删除全部
delete_result = col.delete(expr='pk != ""')

# 4️⃣ flush 确认提交删除
col.flush()

print(f"✅ 已清空集合 '{collection_name}' 中的所有数据。")
print(f"删除详情: {delete_result}")