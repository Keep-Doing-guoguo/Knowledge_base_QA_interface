#!/usr/bin/env python
# coding=utf-8


"""
@author: zgw
@date: 2025/6/7
@desc: 初始化知识库数据库表结构（共4张表）
"""

import os
import json
import sys
import argparse
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, JSON, func, create_engine
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import sessionmaker

# ======== 数据库路径配置 ========
#          /Volumes/PSSD/未命名文件夹/donwload/创建知识库数据库/knowledge_base/info.db
DB_PATH = "/Volumes/PSSD/未命名文件夹/donwload/创建知识库数据库/knowledge_base/info.db"
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"

# ======== SQLAlchemy 初始化 ========
engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base: DeclarativeMeta = declarative_base()

# ======== ORM 模型定义 ========

class KnowledgeBaseModel(Base):
    __tablename__ = 'knowledge_base'
    id = Column(Integer, primary_key=True, autoincrement=True, comment='知识库ID')
    kb_name = Column(String(50), comment='知识库名称')
    kb_info = Column(String(200), comment='知识库简介(用于Agent)')
    vs_type = Column(String(50), comment='向量库类型')
    embed_model = Column(String(50), comment='嵌入模型名称')
    file_count = Column(Integer, default=0, comment='文件数量')
    create_time = Column(DateTime, default=func.now(), comment='创建时间')


class KnowledgeFileModel(Base):
    __tablename__ = 'knowledge_file'
    id = Column(Integer, primary_key=True, autoincrement=True, comment='知识文件ID')
    file_name = Column(String(255), comment='文件名')
    file_ext = Column(String(10), comment='文件扩展名')
    kb_name = Column(String(50), comment='所属知识库名称')
    document_loader_name = Column(String(50), comment='文档加载器名称')
    text_splitter_name = Column(String(50), comment='文本分割器名称')
    file_version = Column(Integer, default=1, comment='文件版本')
    file_mtime = Column(Float, default=0.0, comment="文件修改时间")
    file_size = Column(Integer, default=0, comment="文件大小")
    custom_docs = Column(Boolean, default=False, comment="是否自定义docs")
    docs_count = Column(Integer, default=0, comment="切分文档数量")
    create_time = Column(DateTime, default=func.now(), comment='创建时间')


class FileDocModel(Base):
    __tablename__ = 'file_doc'
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    kb_name = Column(String(50), comment='知识库名称')
    file_name = Column(String(255), comment='文件名称')
    doc_id = Column(String(50), comment="向量库文档ID")
    meta_data = Column(JSON, default={})


class SummaryChunkModel(Base):
    __tablename__ = 'summary_chunk'
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    kb_name = Column(String(50), comment='知识库名称')
    summary_context = Column(String(255), comment='总结文本')
    summary_id = Column(String(255), comment='总结矢量id')
    doc_ids = Column(String(1024), comment="向量库id关联列表")
    meta_data = Column(JSON, default={})


# ======== 表操作函数 ========
def create_tables():
    print("📌 正在创建所有表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 表创建完毕")

def reset_tables():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("⚠️ 数据库表已清空并重新创建")

# ======== 命令行入口 ========
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="初始化知识库数据库")

    parser.add_argument(
        "--create-tables",
        action="store_true",
        help="创建数据库表"
    )

    parser.add_argument(
        "--clear-tables",
        action="store_true",
        help="清空并重建数据库表"
    )

    args = parser.parse_args()
    start_time = datetime.now()

    print("📦 执行参数:")
    for arg, value in vars(args).items():
        print(f"  {arg}: {value}")

    if args.create_tables:
        create_tables()

    if args.clear_tables:
        reset_tables()

    print(f"✅ 执行完毕，耗时: {datetime.now() - start_time}")
#python 创建表.py --create-tables
#python 创建表.py --clear-tables