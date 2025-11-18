#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/6/7 16:07
@source from: 
"""
from server.db.models.knowledge_base_model import KnowledgeBaseModel
from server.db.models.knowledge_file_model import KnowledgeFileModel, FileDocModel
from server.db.session import with_session
from server.knowledge_base.utils import KnowledgeFile
from typing import List, Dict


@with_session
def list_docs_form_db(session,kb_name:str,file_name:str,meta_data:Dict={}) -> List[Dict]:
    '''
    docs表的字段为：id、kbname、filename、docid、metadata
    :param session:
    :param kb_name:
    :param file_name:
    :param meta_data:
    :return:
    '''
    docs = session.query(FileDocModel).filter(FileDocModel.kb_name.ilike(kb_name))
    if file_name:#如果这文件存在拿到这个文件所有的metadata
        docs = docs.filter(FileDocModel.file_name.ilike(file_name))
    for k,v in meta_data.items():
        docs = docs.filter(FileDocModel.metadata[k].as_string() == str(v))
    return [{"id": x.doc_id, "metadata": x.metadata} for x in docs.all()]
@with_session
def delete_docs_from_db(session,kb_name:str,file_name:str=None)->List[Dict]:##这里是删除某一个知识库里面的某一个文件。
    docs = list_docs_form_db(kb_name=kb_name,file_name=file_name)
    query = session.query(FileDocModel).filter(FileDocModel.kb_name.ilike(kb_name))
    if file_name:
        query = query.filter(FileDocModel.file_name.ilike(file_name))
    query.delete(synchronize_session=False)
    session.commit()
    return docs

@with_session
def add_docs_to_db(session,
                   kb_name: str,
                   file_name: str,
                   doc_infos: List[Dict]):
    '''
    将某知识库某文件对应的所有Document信息添加到数据库。
    doc_infos形式：[{"id": str, "metadata": dict}, ...]
    '''
    #! 这里会出现doc_infos为None的情况，需要进一步排查
    if doc_infos is None:
        print("输入的server.db.repository.knowledge_file_repository.add_docs_to_db的doc_infos参数为None")
        return False
    for d in doc_infos:
        obj = FileDocModel(
            kb_name=kb_name,
            file_name=file_name,
            doc_id=d["id"],
            meta_data=d["metadata"],
        )
        session.add(obj)
    return True


@with_session
def add_file_to_db(session,
                kb_file: KnowledgeFile,
                docs_count: int = 0,
                custom_docs: bool = False,
                doc_infos: List[str] = [], # 形式：[{"id": str, "metadata": dict}, ...]
                ):
    '''
    查询知识库是否存在，查询知识库文件是否存在。如果存在的话进行更新。如果不存在的话进行添加。添加到数据库中，然后再进行添加到Doc
    :param session:
    :param kb_file:
    :param docs_count:
    :param custom_docs:
    :param doc_infos:
    :return:
    '''
    kb = session.query(KnowledgeBaseModel).filter_by(kb_name=kb_file.kb_name).first()
    if kb:
        # 如果已经存在该文件，则更新文件信息与版本号
        existing_file: KnowledgeFileModel = (session.query(KnowledgeFileModel)
                                             .filter(KnowledgeFileModel.kb_name.ilike(kb_file.kb_name),
                                                     KnowledgeFileModel.file_name.ilike(kb_file.filename))
                                            .first())
        mtime = kb_file.get_mtime()
        size = kb_file.get_size()

        if existing_file:
            existing_file.file_mtime = mtime
            existing_file.file_size = size
            existing_file.docs_count = docs_count
            existing_file.custom_docs = custom_docs
            existing_file.file_version += 1
        # 否则，添加新文件
        else:
            new_file = KnowledgeFileModel(
                file_name=kb_file.filename,
                file_ext=kb_file.ext,
                kb_name=kb_file.kb_name,
                document_loader_name=kb_file.document_loader_name,
                text_splitter_name=kb_file.text_splitter_name or "SpacyTextSplitter",
                file_mtime=mtime,
                file_size=size,
                docs_count = docs_count,
                custom_docs=custom_docs,
            )
            kb.file_count += 1
            session.add(new_file)
        add_docs_to_db(kb_name=kb_file.kb_name, file_name=kb_file.filename, doc_infos=doc_infos)
    return True

@with_session
def delete_file_from_db(session,kb_file:KnowledgeFile):
    #1.先看看在特定的知识库中有没有这个文件.2.然后有的话就进行删除
    existing_file = (session.query(KnowledgeFileModel)
                     .filter(KnowledgeFileModel.file_name.ilike(kb_file.filename),
                             KnowledgeFileModel.kb_name.ilike(kb_file.kb_name))
                     .first())
    if existing_file:
        session.delete(existing_file)
        delete_docs_from_db(kb_name=kb_file.kb_name, file_name=kb_file.filename)
        session.commit()

        kb = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_file.kb_name)).first()
        if kb:
            kb.file_count -= 1
            session.commit()
    return True
@with_session
def file_exists_in_db(session, kb_file: KnowledgeFile):
    existing_file = (session.query(KnowledgeFileModel)
                     .filter(KnowledgeFileModel.file_name.ilike(kb_file.filename),
                            KnowledgeFileModel.kb_name.ilike(kb_file.kb_name))
                    .first())#同一个知识库下的某一个文件才可以删除
    return True if existing_file else False
@with_session
def delete_files_from_db(session, knowledge_base_name: str):
    '''
    先把filemodel里面的文件删除；然后再删除docmodel里面的内容；然后再删除这个知识库（只是将文件归置为0）。
    :param session:
    :param knowledge_base_name:
    :return:
    '''
    print(f"knowledge_base_name----{knowledge_base_name}")
    session.query(KnowledgeFileModel).filter(KnowledgeFileModel.kb_name.ilike(knowledge_base_name)).delete(synchronize_session=False)
    session.query(FileDocModel).filter(FileDocModel.kb_name.ilike(knowledge_base_name)).delete(synchronize_session=False)
    kb = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(knowledge_base_name)).first()
    if kb:
        kb.file_count = 0
    session.commit()
    return True

@with_session
def list_files_from_db(session, kb_name):
    '''
    从knowledgefile中先query，然后过滤kb_name符合的，把这些全部都取出来。然后再拿到file_name。
    :param session:
    :param kb_name:
    :return:
    '''
    files = session.query(KnowledgeFileModel).filter(KnowledgeFileModel.kb_name.ilike(kb_name)).all()
    docs = [f.file_name for f in files]
    return docs

if __name__ == "__main__":

    #添加文件先到数据库，然后再到知识库中。


    #1.查询docs表中的某一个文件。
    print(list_docs_form_db(kb_name='samples',file_name="test.txt",meta_data={}))

    #2.添加文件到docs表,该函数只会被add_file进行调用
    #print(add_docs_to_db(kb_name="samples",file_name="",doc_infos={}))

    #3.删除某一个知识库里面的某一个文件
    #print(delete_docs_from_db(kb_name='samples',file_name='test.txt'))

    #4.添加文件到知识库中.先把文件数据添加到数据库中。
    #添加文件需要去多个方法的建立，首先需要一个KnowledegFile的构建，这个可以去使用kb_doc_api里面进行测试。

    #


