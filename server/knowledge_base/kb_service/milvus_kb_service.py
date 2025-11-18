import os.path
from typing import List, Dict, Optional
import uuid
from langchain.schema import Document
from langchain.vectorstores.milvus import Milvus
from pathlib import Path

from configs import kbs_config

from server.knowledge_base.kb_service.base import KBService, EmbeddingsFunAdapter, \
    score_threshold_process
from server.knowledge_base.utils import KnowledgeFile


class MilvusKBService(KBService):
    milvus: Milvus

    @staticmethod
    def get_collection(milvus_name):
        from pymilvus import Collection
        return Collection(milvus_name)

    # def save_vector_store(self):
    #     if self.milvus.col:
    #         self.milvus.col.flush()

    def get_doc_by_ids(self, ids: List[str]) -> List[Document]:
        result = []
        if self.milvus.col:
            data_list = self.milvus.col.query(expr=f'pk in {ids}', output_fields=["*"])
            for data in data_list:
                text = data.pop("text")
                result.append(Document(page_content=text, metadata=data))
        return result

    def del_doc_by_ids(self, ids: List[str]) -> bool:
        self.milvus.col.delete(expr=f'pk in {ids}')

    @staticmethod
    def search(milvus_name, content, limit=3):
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10},
        }
        c = MilvusKBService.get_collection(milvus_name)
        return c.search(content, "embeddings", search_params, limit=limit, output_fields=["content"])


    def vs_type(self) -> str:
        return 'milvus_l'

    def _load_milvus(self):
        self.milvus = Milvus(embedding_function=EmbeddingsFunAdapter(self.embed_model),
                             collection_name=self.kb_name, 
                             connection_args=kbs_config.get("milvus"),
                             index_params=kbs_config.get("milvus_kwargs")["index_params"],
                             search_params=kbs_config.get("milvus_kwargs")["search_params"]
                             )

    def do_init(self):

        self._load_milvus()



    def do_search(self, query: str, top_k: int, score_threshold: float=0.6):
        self._load_milvus()
        embed_func = EmbeddingsFunAdapter(self.embed_model)
        embeddings = embed_func.embed_query(query)
        docs = self.milvus.similarity_search_with_score_by_vector(embeddings, top_k)#去milvus中进行检索。

        # [
        #     (Document(page_content="中国移动成立于2000年...", metadata={"source": "report_2024.pdf"}), 0.89),
        #     (Document(page_content="5G 是第五代移动通信技术...", metadata={"source": "whitepaper.txt"}), 0.87),
        #     ...
        # ]
        a = score_threshold_process(score_threshold, top_k, docs)
        return score_threshold_process(score_threshold, top_k, docs)

    def do_add_doc(self, docs: List[Document], **kwargs) -> List[Dict]:
        # TODO: workaround for bug #10492 in langchain
        for doc in docs:
            for k, v in doc.metadata.items():
                doc.metadata[k] = str(v)
            for field in self.milvus.fields:
                doc.metadata.setdefault(field, "")
            doc.metadata.pop(self.milvus._text_field, None)#将字段里面的内容pop出来。
            doc.metadata.pop(self.milvus._vector_field, None)#起一个验证的作用。根据 key 删除并返回对应的值。
            # 如果 collection 需要手动 id，就生成 uuid
        ids = kwargs.get("ids")
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in docs]
        for i, doc in enumerate(docs):
            doc.metadata["pk"] = ids[i]
        ids = self.milvus.add_documents(docs,ids=ids)
        doc_infos = [{"id": id, "metadata": doc.metadata} for id, doc in zip(ids, docs)]
        return doc_infos

    def do_delete_doc(self, kb_file: KnowledgeFile, **kwargs):
        if self.milvus.col:
            filepath = kb_file.filepath.replace('\\', '\\\\')
            base_dir = os.path.dirname(filepath)
            filepath = Path(kb_file.filepath).relative_to(base_dir).as_posix()

            delete_list = [item.get("pk") for item in
                           self.milvus.col.query(expr=f'source == "{filepath}"', output_fields=["pk"])]#查找所有 source 等于 filepath 的记录。
            print()
            '''
            self.milvus.col：输出的是schema信息：
            <Collection>:
            -------------
            <name>: samples
            <description>: 
            <schema>: {'auto_id': False, 'description': '', 'fields': [
                {'name': 'source', 'description': '', 'type': <DataType.VARCHAR: 21>, 'params': {'max_length': 65535}},
                {'name': 'text', 'description': '', 'type': <DataType.VARCHAR: 21>, 'params': {'max_length': 65535}},
                {'name': 'pk', 'description': '', 'type': <DataType.VARCHAR: 21>, 'params': {'max_length': 65535}, 'is_primary': True, 'auto_id': False},
                {'name': 'vector', 'description': '', 'type': <DataType.FLOAT_VECTOR: 101>, 'params': {'dim': 1024}}
            ], 'enable_dynamic_field': False}
            查询返回的结果为：
            [
                {"pk": "c9d96ddf-3f91-435f-9b19-b005c6c1d7d2"},
                {"pk": "b5ac4744-71ff-4540-8dc1-23beaacf1fe4"},
            ]
            '''
            self.milvus.col.delete(expr=f'pk in {delete_list}')

    def do_clear_vs(self):
        if self.milvus.col:
            self.do_drop_kb()
            self.do_init()

    def do_drop_kb(self):
        if self.milvus.col:
            self.milvus.col.release()
            self.milvus.col.drop()

    def do_create_kb(self):
        pass


if __name__ == '__main__':
    pass
    # 测试建表使用
    from server.db.base import Base, engine

    #milvusService = MilvusKBService("samples",'BAAI/bge-large-zh-v1.5')#初始化类方法。
    #milvusService.add_doc(KnowledgeFile("/Volumes/PSSD/未命名文件夹/donwload/创建知识库数据库/server/knowledge_base/kb_service/目录结构.md", "samples"))
    knowledge_base_name = 'samples'
    top_k = 3
    score_threshold = 0.6
    query = '介绍新乡工程学院'
    mil = MilvusKBService('samples','BAAI/bge-large-zh-v1.5')
    docs_ = mil.search_docs(query=query,  top_k=top_k,
                        score_threshold=score_threshold)
    print(docs_)
    print('debug')
    #print(milvusService.get_doc_by_ids(["444022434274215486"]))
    # milvusService.delete_doc(KnowledgeFile("README.md", "test"))
    # milvusService.do_drop_kb()
    # print(milvusService.search_docs("如何启动api服务"))
