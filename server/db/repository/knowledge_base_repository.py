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
    kb = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)).first()#在知识库中查询，过滤知识库中的名字然后匹配，拿到第一个。
    if not kb:
        kb = KnowledgeBaseModel(kb_name=kb_name, kb_info=kb_info, vs_type=vs_type, embed_model=embed_model)
        session.add(kb)
    else:  # update kb with new vs_type and embed_model
        kb.kb_info = kb_info
        kb.vs_type = vs_type
        kb.embed_model = embed_model
    return True

@with_session
def load_kb_from_db(session, kb_name):
    kb = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)).first()
    if kb:
        kb_name, vs_type, embed_model = kb.kb_name, kb.vs_type, kb.embed_model
    else:
        kb_name, vs_type, embed_model = None, None, None
    return kb_name, vs_type, embed_model

@with_session
def delete_kb_from_db(session,kb_name):
    kb = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)).first()
    if kb:
        session.delete(kb)
    return True


@with_session
def list_kbs_from_db(session, min_file_count: int = -1):#list_files_from_db
    kbs = session.query(KnowledgeBaseModel.kb_name).filter(KnowledgeBaseModel.file_count > min_file_count).all()
    kbs = [kb[0] for kb in kbs]
    return kbs

@with_session
def kb_exists(session,kb_name):
    kb = session.query(KnowledgeBaseModel.kb_name).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)).first()
    status = True if kb else False
    return status

@with_session
def list_kb_from_db(session):
    all_kb = session.query(KnowledgeBaseModel)
    all_kb_name = [kb.kb_name for kb in all_kb]
    return all_kb_name

@with_session
def get_kb_detail(session,kb_name):
    kb = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)).first()
    if kb:
        return {
            "kb_name":kb.kb_name,
            "kb_info":kb.kb_info,
            "vs_type":kb.vs_type,
            "embed_model":kb.embed_model,
            "file_count":kb.file_count,
            "create_time":kb.create_time
        }
    return {}

if __name__ == "__main__":
    #1.添加知识库
    print(add_kb_to_db(kb_name="samples", kb_info="测试知识库", vs_type="milvus", embed_model="bge-large-zh"))

    #2.删除指定的知识库
    #print(delete_kb_from_db(kb_name="examples"))



    #3.查询有那些知识库。
    print(list_kb_from_db())

    #4.确定某知识库是否存在
    print(kb_exists(kb_name='samples'))

    #5.查询知识库名称的，就是查询有那些知识库。.
    print(list_kbs_from_db())


    #6.加载知识库这个类
    print(load_kb_from_db('samples'))

    #7.查询知识库的具体信息：
    print(get_kb_detail('samples'))



