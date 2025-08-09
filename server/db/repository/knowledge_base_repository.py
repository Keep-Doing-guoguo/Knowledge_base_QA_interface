#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/6/7 16:07
@source from: 
"""
from server.db.models.knowledge_base_model import KnowledgeBaseModel
from server.db.session import with_session


@with_session
def add_kb_to_db(session, kb_name, kb_info, vs_type, embed_model):
    # 创建知识库实例
    kb = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)).first()
    if not kb:
        kb = KnowledgeBaseModel(kb_name=kb_name, kb_info=kb_info, vs_type=vs_type, embed_model=embed_model)
        session.add(kb)
    else:  # update kb with new vs_type and embed_model
        kb.kb_info = kb_info
        kb.vs_type = vs_type
        kb.embed_model = embed_model
    return True


@with_session
def list_kbs_from_db(session, min_file_count: int = -1):
    kbs = session.query(KnowledgeBaseModel.kb_name).filter(KnowledgeBaseModel.file_count > min_file_count).all()
    kbs = [kb[0] for kb in kbs]
    return kbs


@with_session
def kb_exists(session, kb_name):
    kb = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)).first()
    status = True if kb else False
    return status


@with_session
def load_kb_from_db(session, kb_name):
    kb = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)).first()
    if kb:
        kb_name, vs_type, embed_model = kb.kb_name, kb.vs_type, kb.embed_model
    else:
        kb_name, vs_type, embed_model = None, None, None
    return kb_name, vs_type, embed_model


@with_session
def delete_kb_from_db(session, kb_name):
    kb = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)).first()
    if kb:
        session.delete(kb)
    return True


@with_session
def get_kb_detail(session, kb_name: str) -> dict:
    kb: KnowledgeBaseModel = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)).first()
    if kb:
        return {
            "kb_name": kb.kb_name,
            "kb_info": kb.kb_info,
            "vs_type": kb.vs_type,
            "embed_model": kb.embed_model,
            "file_count": kb.file_count,
            "create_time": kb.create_time,
        }
    else:
        return {}


# ========================
# 测试入口
# ========================

if __name__ == "__main__":
    test_kb_name = "test_kb"
    test_kb_info = "这是一个用于测试的知识库"
    test_vs_type = "FAISS"
    test_embed_model = "text-embedding-ada-002"

    print("🧪 开始测试知识库数据库操作函数...")

    # 1. 添加知识库
    print(f"📌 正在添加知识库：{test_kb_name}")
    add_kb_to_db(
        kb_name=test_kb_name,
        kb_info=test_kb_info,
        vs_type=test_vs_type,
        embed_model=test_embed_model
    )
    print("✅ 添加完成")

    # 2. 检查是否存在
    exists = kb_exists(kb_name=test_kb_name)
    print(f"🔍 知识库 {test_kb_name} 是否存在？{'是' if exists else '否'}")
    assert exists is True, "❌ 添加知识库失败"

    # 3. 获取详细信息
    print(f"📝 获取知识库 {test_kb_name} 的详细信息")
    detail = get_kb_detail(test_kb_name)
    print("Detail:", detail)

    # 4. 加载基本信息
    kb_name, vs_type, embed_model = load_kb_from_db(test_kb_name)
    print(f"🧠 加载知识库信息：{kb_name}, {vs_type}, {embed_model}")
    assert kb_name == test_kb_name, "❌ 加载知识库名称错误"
    assert vs_type == test_vs_type, "❌ 向量库类型不一致"
    assert embed_model == test_embed_model, "❌ 嵌入模型不一致"

    # 5. 列出所有知识库
    print("📋 当前数据库中的知识库列表：")
    all_kbs = list_kbs_from_db(min_file_count=-1)
    print(all_kbs)
    assert test_kb_name in all_kbs, "❌ 列表中未找到刚添加的知识库"

    # 6. 删除知识库
    print(f"🗑️ 正在删除知识库：{test_kb_name}")
    delete_kb_from_db(test_kb_name)
    print("✅ 删除完成")

    # 7. 再次检查是否存在
    exists_after_delete = kb_exists(kb_name=test_kb_name)
    print(f"🔍 删除后，知识库 {test_kb_name} 是否还存在？{'是' if exists_after_delete else '否'}")
    assert exists_after_delete is False, "❌ 删除失败"

    print("🎉 所有测试通过！")















