#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2024/12/25 14:29
@source from: 
"""
import sys
from server.knowledge_base.migrate import (create_tables, reset_tables, import_from_db,
                                           folder2db)

import nltk
from datetime import datetime

# 设置 NLTK 数据路径


# 定义主逻辑函数
def init_database(
        recreate_vs=True,
        create_tables_flag=False,
        clear_tables_flag=False,
        import_db_path=None,
        update_in_db_flag=False,
        increament_flag=False,
        prune_db_flag=False,
        prune_folder_flag=False,
        kb_name=[],
        embed_model=None
):
    """
    主逻辑函数，用于初始化数据库或向量库。

    参数:
    - recreate_vs: 是否重新创建向量库
    - create_tables_flag: 是否创建空表
    - clear_tables_flag: 是否重置数据库表
    - import_db_path: 导入数据库路径
    - update_in_db_flag: 是否更新数据库中的向量
    - increament_flag: 是否增量更新向量库
    - prune_db_flag: 是否清理数据库中文档
    - prune_folder_flag: 是否清理文件夹中未使用的文件
    - kb_name: 知识库名称列表
    - embed_model: 嵌入模型名称
    """
    kb_name = kb_name or []
    start_time = datetime.now()

    if create_tables_flag:
        create_tables()  # 确保表存在

    if clear_tables_flag:
        reset_tables()
        print("Database tables have been reset.")
        print("Database tables have been reset.")

    if recreate_vs:
        create_tables()
        print("Recreating all vector stores...")
        folder2db(kb_names=kb_name, mode="recreate_vs", embed_model=embed_model)
    elif import_db_path:
        import_from_db(import_db_path)

    end_time = datetime.now()
    print(f"Total time taken: {end_time - start_time}")


# 示例调用
if __name__ == "__main__":
    # 示例调用，可以在此处调整参数直接运行
    init_database(
        recreate_vs=True,
        kb_name=[],
        embed_model="qwen-api"
    )