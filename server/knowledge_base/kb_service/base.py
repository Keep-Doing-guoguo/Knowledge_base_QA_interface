import operator
from abc import ABC, abstractmethod

import os
import requests
from pathlib import Path
import numpy as np
from langchain.embeddings.base import Embeddings
from langchain.docstore.document import Document
from server.db.repository.knowledge_base_repository import load_kb_from_db,add_kb_to_db,delete_kb_from_db
from server.db.repository.knowledge_file_repository import delete_files_from_db,list_files_from_db,delete_file_from_db,add_file_to_db
from server.db.repository.knowledge_file_repository import file_exists_in_db

from configs import (kbs_config, VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD, KB_INFO,EMBEDDING_MODEL)
from server.knowledge_base.utils import (
    get_kb_path, get_doc_path, KnowledgeFile,
    list_kbs_from_folder, list_files_from_folder,
)

from typing import List, Union, Dict, Optional


from server.knowledge_base.model.kb_document_model import DocumentWithVSId


def normalize(embeddings: List[List[float]]) -> np.ndarray:
    '''
    sklearn.preprocessing.normalize 的替代（使用 L2），避免安装 scipy, scikit-learn
    '''
    norm = np.linalg.norm(embeddings, axis=1)
    norm = np.reshape(norm, (norm.shape[0], 1))
    norm = np.tile(norm, (1, len(embeddings[0])))
    return np.divide(embeddings, norm)


def score_threshold_process(score_threshold, k, docs):
    if score_threshold is not None:
        cmp = (
            operator.le
        )
        docs = [
            (doc, similarity)
            for doc, similarity in docs
            if cmp(similarity, score_threshold)
        ]
        '''
        确实用的 L2 距离，所以分数 0.86 表示比较接近，1.45 表示不太接近。在 Milvus 里如果使用 L2（欧式距离），距离越小 → 向量越接近（更相似）。

        '''
    return docs[:k]

class KBService(ABC):#继承自 ABC（Abstract Base Class），表示这是一个抽象基类，不能直接实例化，必须由子类实现其抽象方法。

    def __init__(self,
                 knowledge_base_name: str,
                 embed_model: str = EMBEDDING_MODEL,
                 ):
        self.kb_name = knowledge_base_name
        self.kb_info = KB_INFO.get(knowledge_base_name, f"关于{knowledge_base_name}的知识库")
        self.embed_model = embed_model
        self.kb_path = get_kb_path(self.kb_name)#'/Users/zhangguowen/Downloads/donwload/Langchain-Chatchat-0.2.9/knowledge_base/test'
        self.doc_path = get_doc_path(self.kb_name)#'/Users/zhangguowen/Downloads/donwload/Langchain-Chatchat-0.2.9/knowledge_base/test/content'
        self.do_init()

    def __repr__(self) -> str:
        return f"{self.kb_name} @ {self.embed_model}"

    def create_kb(self):
        '''
        创建知识库，属于数据库的内容。
        :return:
        '''
        if not os.path.exists(self.doc_path):
            os.makedirs(self.doc_path)  # 创建所需的目录。
        self.do_create_kb()
        status = add_kb_to_db(self.kb_name,self.kb_info,self.vs_type(), self.embed_model)
        return status

    def clear_vs(self):
        '''
        删除向量库中的所有内容。
        :return:
        '''
        self.do_clear_vs()#清空向量库里面关于这个知识库的内容，milvusservice里面已经实现了。
        status = delete_files_from_db(self.kb_name)#
        return status

    def list_files(self):
        return list_files_from_db(self.kb_name)#list_kbs_from_db

    @abstractmethod
    def do_create_kb(self):
        '''

        :return:
        '''
        pass
    def list_docs(self,file_name:str=None,metadata:Dict={}) -> List[DocumentWithVSId]:
        '''
        列出来文档，应该从file里面查询。
        :param file_name:
        :param metadata:
        :return:
        '''
        files = list_files_from_db(self.kb_name)

        pass
    def _docs_to_embeddings(self, docs: List[Document]) -> Dict:
        '''
        将 List[Document] 转化为 VectorStore.add_embeddings 可以接受的参数
        '''
        return embed_documents(docs=docs, embed_model=self.embed_model, to_query=False)

    def add_doc(self, kb_file: KnowledgeFile, docs: List[Document] = [], **kwargs):
        """
        向知识库添加文件
        如果指定了docs，则不再将文本向量化，并将数据库对应条目标为custom_docs=True
        """
        if docs:
            custom_docs = True
            for doc in docs:
                doc.metadata.setdefault("source", kb_file.filename)
        else:
            docs = kb_file.file2text()
            custom_docs = False

        if docs:
            # 将 metadata["source"] 改为相对路径
            for doc in docs:
                try:
                    source = doc.metadata.get("source", "")
                    if os.path.isabs(source):
                        rel_path = Path(source).relative_to(self.doc_path)
                        doc.metadata["source"] = str(rel_path.as_posix().strip("/"))
                except Exception as e:
                    print(f"cannot convert absolute path ({source}) to relative path. error is : {e}")
            self.delete_doc(kb_file)#	5.	删除旧的文档
            doc_infos = self.do_add_doc(docs, **kwargs)#	6.	添加新文档到向量库
            status = add_file_to_db(kb_file,
                                    custom_docs=custom_docs,
                                    docs_count=len(docs),
                                    doc_infos=doc_infos)#	7.	更新数据库
        else:
            status = False
        return status
    def delete_doc(self,kb_file:KnowledgeFile,delete_content:bool=False,**kwargs):
        #1.删除milvus中的doc数据内容
        self.do_delete_doc(kb_file,**kwargs)#是milvus中的方法。
        status = delete_file_from_db(kb_file)
        if delete_content and os.path.exists(kb_file.filepath):
            os.remove(kb_file.filepath)
        return status
    def exist_doc(self, file_name: str):
        return file_exists_in_db(KnowledgeFile(knowledge_base_name=self.kb_name,
                                               filename=file_name))
    def updata_inf(self,kb_info:str):
        self.kb_info = kb_info
        status = add_kb_to_db(self.kb_name, self.kb_info, self.vs_type(), self.embed_model)
        return status
    def update_doc(self, kb_file: KnowledgeFile, docs: List[Document] = [], **kwargs):
        """
        使用content中的文件更新向量库
        如果指定了docs，则使用自定义docs，并将数据库对应条目标为custom_docs=True
        """
        if os.path.exists(kb_file.filepath):
            self.delete_doc(kb_file, **kwargs)
            return self.add_doc(kb_file, docs=docs, **kwargs)

    @abstractmethod
    def do_clear_vs(self):
        """
        从知识库删除全部向量子类实自己逻辑
        """
        pass
    def drop_kb(self):
        """
        删除知识库
        """
        self.do_drop_kb()
        status = delete_kb_from_db(self.kb_name)
        return status
    def search_docs(self,
                    query:str,
                    top_k:int = VECTOR_SEARCH_TOP_K,
                    score_threshold:float = SCORE_THRESHOLD) -> List[Document]:
        docs = self.do_search(query,top_k,score_threshold)
        return docs

class KBServiceFactory:
#该类的职责是通过静态方法创建不同类型的 KBService（知识库服务）实例。
    @staticmethod
    def get_service_by_name(kb_name: str) -> KBService:
        _, vector_store_type, embed_model = load_kb_from_db(kb_name)#从数据库中加载知识库
        if _ is None:  # kb not in db, just return None
            return None
        from server.knowledge_base.kb_service.milvus_kb_service import MilvusKBService
        return MilvusKBService(kb_name,embed_model=embed_model)
    @staticmethod
    def get_service(kb_name: str, vector_store_type, embed_model) -> KBService:
        from server.knowledge_base.kb_service.milvus_kb_service import MilvusKBService

        return MilvusKBService(kb_name, embed_model=embed_model)


class EmbeddingsFunAdapter(Embeddings):
    def __init__(self, api_key: str, model: str = "BAAI/bge-large-zh-v1.5"):
        self.api_key = "sk-ruourlqqajhathtbsgmywvanbywoikkwkyhczzqemhkrxcuu"
        self.model = model
        self.url = "https://api.siliconflow.cn/v1/embeddings"

    def _call_api(self, texts: List[str]) -> List[List[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "input": texts if len(texts) > 1 else texts[0],
            "encoding_format": "float"
        }
        response = requests.post(self.url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()["data"]
        embeddings = [item["embedding"] for item in data]
        return normalize(embeddings).tolist()

    async def _call_api_async(self, texts: List[str]) -> List[List[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "input": texts if len(texts) > 1 else texts[0],
            "encoding_format": "float"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()["data"]
            embeddings = [item["embedding"] for item in data]
            return normalize(embeddings).tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._call_api(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._call_api([text])[0]

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        return await self._call_api_async(texts)

    async def aembed_query(self, text: str) -> List[float]:
        return (await self._call_api_async([text]))[0]



