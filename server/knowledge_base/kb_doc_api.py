import os
import urllib
from fastapi import File, Form, Body, Query, UploadFile
from configs import (VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD,
                     CHUNK_SIZE, OVERLAP_SIZE,
                     logger, log_verbose, )
from server.utils import BaseResponse, ListResponse, run_in_thread_pool
from server.knowledge_base.utils import (validate_kb_name, get_file_path,
                                         KnowledgeFile,files2docs_in_thread_)
from fastapi.responses import FileResponse
from server.knowledge_base.kb_service.base import KBServiceFactory

from langchain.docstore.document import Document
from server.knowledge_base.model.kb_document_model import DocumentWithVSId
from typing import List, Dict


def search_docs(query:str = Body("",examples=[],description="用户输入问题"),
                knowledge_base_name :str = Body(...,examples=[]),
                top_k:int = Body(VECTOR_SEARCH_TOP_K,description="匹配向量数"),
                score_threshold:float = Body(SCORE_THRESHOLD,description=""),
                file_name:str = Body("",description='文件名称'),
                metadata:dict=Body({},description="")) -> List[DocumentWithVSId]:

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    data = []
    if kb is not None:
        if query:
            docs = kb.search_docs(query,top_k,score_threshold)
            for doc,score in docs:
                doc_data = doc.dict()
                doc_data.pop("id",None)
                data.append(DocumentWithVSId(**doc_data,score=score, id=doc.metadata.get("pk")))
        elif file_name or metadata:
            data = kb.list_docs(file_name=file_name,metadata=metadata)
    return data
'''
返回的结果为：

[
  {
    "page_content": "监督电话：（0373）6330018\n\n邮 箱：xgrsc@xxgc.edu.cn\n\n学校官网：http://www.xxgc.edu.cn\n\n到校路线：学校位于新乡市新飞大道南段777号，距新乡市高铁站14公里左右，北临新乡市汽车客运南站，西临107国道，东临京港澳高速。市内可乘坐11路公交车到新乡工程学院下车。自驾者在手机地图搜索“新乡工程学院（南校区）”可直接到达。",
    "metadata": {
      "source": "test.txt",
      "pk": "5d940d90-4484-4534-9086-7cf1b5cee5b9"
    },
    "type": "Document",
    "id": "5d940d90-4484-4534-9086-7cf1b5cee5b9",
    "score": 0.5273342132568359
  },
  {
    "page_content": "新乡工程学院（原河南科技学院新科学院）是经教育部批准设立的全日制普通本科高等学校。学校地处中原名城新乡市，现有南、北和大学科技园三个校区，规划占地面积2200亩，总建筑面积110万平方米。学校设有教学学院12个，涵盖经济学、管理学、法学、文学、理学、工学、农学、艺术学、教育学等九大学科门类。其中，新一轮河南省重点学科3个，河南省“综合改革试点专业”2个，“河南省一流本科专业建设点”2个，建设产教融合类专业建设点3个，“河南省民办普通高等学校专业建设资助项目”5个，获批省级工程（技术）研究中心和市",
    "metadata": {
      "source": "test.txt",
      "pk": "0769ccd7-b1ac-4d57-b8e2-263f3d8cc8c6"
    },
    "type": "Document",
    "id": "0769ccd7-b1ac-4d57-b8e2-263f3d8cc8c6",
    "score": 0.5310670733451843
  }
]
'''

def list_files(
        knowledge_base_name: str
) -> ListResponse:
    if not validate_kb_name(knowledge_base_name):
        return ListResponse(code=403, msg="Don't attack me", data=[])
    knowledge_base_name = urllib.parse.unquote(knowledge_base_name)

    #判断是否有这个知识库
    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        return ListResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}", data=[])
    else:
        all_doc_names = kb.list_files()#这里返回的是一个list，list里面放的是filename
        return ListResponse(data=all_doc_names)
def _save_files_in_thread(files: List[UploadFile],
                          knowledge_base_name: str,
                          override: bool):
    """
    通过多线程将上传的文件保存到对应知识库目录内。
    生成器返回保存结果：{"code":200, "msg": "xxx", "data": {"knowledge_base_name":"xxx", "file_name": "xxx"}}
    """

    def save_file(file: UploadFile, knowledge_base_name: str, override: bool) -> dict:
        '''
        保存单个文件。
        '''
        try:
            filename = file.filename
            file_path = get_file_path(knowledge_base_name=knowledge_base_name, doc_name=filename)
            data = {"knowledge_base_name": knowledge_base_name, "file_name": filename}

            file_content = file.file.read()  # 读取上传文件的内容
            if (os.path.isfile(file_path)
                    and not override
                    and os.path.getsize(file_path) == len(file_content)
            ):
                # TODO: filesize 不同后的处理
                file_status = f"文件 {filename} 已存在。"
                logger.warn(file_status)
                return dict(code=404, msg=file_status, data=data)

            if not os.path.isdir(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            with open(file_path, "wb") as f:
                f.write(file_content)
            return dict(code=200, msg=f"成功上传文件 {filename}", data=data)
        except Exception as e:
            msg = f"{filename} 文件上传失败，报错信息为: {e}"
            logger.error(f'{e.__class__.__name__}: {msg}',
                         exc_info=e if log_verbose else None)
            return dict(code=500, msg=msg, data=data)

    params = [{"file": file, "knowledge_base_name": knowledge_base_name, "override": override} for file in files]
    for result in run_in_thread_pool(save_file, params=params):
        yield result

def upload_docs(
        files: List[UploadFile] = File(..., description="上传文件，支持多文件"),
        knowledge_base_name: str = Form("samples", description="知识库名称", examples=["samples"]),
        override: bool = Form(False, description="覆盖已有文件"),
        to_vector_store: bool = Form(True, description="上传文件后是否进行向量化"),
        chunk_size: int = Form(CHUNK_SIZE, description="知识库中单段文本最大长度"),
        chunk_overlap: int = Form(OVERLAP_SIZE, description="知识库中相邻文本重合长度"),

) -> BaseResponse:
    """
    API接口：上传文件，并/或向量化
    """
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")

    failed_files = {}

    file_names = []
    # 先将上传的文件保存到磁盘，这里的实现是多线程保存文件的。
    for result in _save_files_in_thread(files, knowledge_base_name=knowledge_base_name, override=override):
        filename = result["data"]["file_name"]
        if result["code"] != 200:
            failed_files[filename] = result["msg"]

        file_names.append(filename)

    # 对保存的文件进行向量化
    if to_vector_store:
        result = update_docs(
            knowledge_base_name=knowledge_base_name,
            file_names=file_names,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        failed_files.update(result.data["failed_files"])


    return BaseResponse(code=200, msg="文件上传与向量化完成", data={"failed_files": failed_files})




def update_docs(
        knowledge_base_name: str = Body(..., description="知识库名称", examples=["samples"]),
        file_names: List[str] = Body(..., description="文件名称，支持多文件", examples=[["file_name1", "text.txt"]]),
        chunk_size: int = Body(CHUNK_SIZE, description="知识库中单段文本最大长度"),
        chunk_overlap: int = Body(OVERLAP_SIZE, description="知识库中相邻文本重合长度"),

) -> BaseResponse:
    """
    更新知识库文档
    """
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")

    failed_files = {}
    kb_files = []
    # 生成需要加载docs的文件列表
    for file_name in file_names:
        try:
            kb_files.append(KnowledgeFile(filename=file_name, knowledge_base_name=knowledge_base_name))
        except Exception as e:
            msg = f"加载文档 {file_name} 时出错：{e}"
            logger.error(f'{e.__class__.__name__}: {msg}',
                             exc_info=e if log_verbose else None)
            failed_files[file_name] = msg

    for status, result in files2docs_in_thread_(kb_files,
                                               chunk_size=chunk_size,
                                               chunk_overlap=chunk_overlap,):#这里是单线程处理文件的，一个一个的进行返回的。
        if status:
            kb_name, file_name, new_docs = result
            kb_file = KnowledgeFile(filename=file_name, knowledge_base_name=knowledge_base_name)
            kb_file.splited_docs = new_docs
            kb.update_doc(kb_file)
        else:
            kb_name, file_name, error = result
            failed_files[file_name] = error


    return BaseResponse(code=200, msg=f"更新文档完成", data={"failed_files": failed_files})

def delete_docs(knowledge_base_name:str=Body(...,examples=['samples']),
                file_names:List[str]=Body(...,examples=[['test.txt']]),
                delete_content:bool=Body(False)):#是否删除知识库源文件。
    '''
    需要确定是那个知识库，那个文件。确定知识库是否存在，确定文件
    :return:
    '''
    if not validate_kb_name(knowledge_base_name):
        #验证服务器路径是否存在该知识库。
        return BaseResponse(code=403, msg="Don't attack me")

    #确定存在这个知识库。
    knowledge_base_name = urllib.parse.unquote(knowledge_base_name)
    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")

    failed_files = {}
    for file_name in file_names:
        if not kb.exist_doc(file_name):
            failed_files[file_name] = f"未找到文件 {file_name}"
        try:
            kb_file = KnowledgeFile(filename=file_name,
                                    knowledge_base_name=knowledge_base_name)
            kb.delete_doc(kb_file, delete_content, not_refresh_vs_cache=True)#在知识库中删除文件，对应三个库，KbnowledgeBaseModel（这里面某一个知识库的filecount需要减一）、KbnowledgeFileModel（这里需要删除一个文件）、FileDocModel（这里需要删除多个id和文件）
        except Exception as e:
            msg = f"{file_name} 文件删除失败，错误信息：{e}"
            logger.error(f'{e.__class__.__name__}: {msg}')
            failed_files[file_name] = msg
    return BaseResponse(code=200, msg=f"文件删除完成", data={"failed_files": failed_files})

def download_doc(
    knowledge_base_name: str = Query(..., description="知识库名称", examples=["samples"]),
    file_name: str = Query(..., description="文件名称", examples=["test.txt"]),
preview: bool = Query(False, description="是：浏览器内预览；否：下载"),
):#下载知识库文件
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")
    if preview:
        content_disposition_type = "inline"
    else:
        content_disposition_type = None
    try:
        kb_file = KnowledgeFile(filename=file_name,
                                knowledge_base_name=knowledge_base_name)
        if os.path.exists(kb_file.filepath):
            return FileResponse(
                path=kb_file.filepath,
                filename=kb_file.filename,
                media_type="multipart/form-data",
                content_disposition_type=content_disposition_type,
            )
    except Exception as e:
        msg = f"{kb_file.filename} 读取文件失败，错误信息是：{e}"
        logger.error(f'{e.__class__.__name__}: {msg}',)
        return BaseResponse(code=500, msg=msg)

    return BaseResponse(code=500, msg=f"{kb_file.filename} 读取文件失败")
def updata_info(
        knowledge_base_name:str=Body(...,description="知识库名称", examples=["samples"]),
        kb_info: str = Body(..., description="知识库介绍", examples=["这是一个知识库"]),
):#更新的是知识库信息
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")
    kb.update_info(kb_info)

    return BaseResponse(code=200, msg=f"知识库介绍修改完成", data={"kb_info": kb_info})
'''
docs:为list，list里面是tuple。
一个为Document，另一个为float。
'''
# ====== 自测主程序 ======

def main():
    # 1.测试上传文件到知识库中。
    #resp = update_docs(knowledge_base_name="samples",file_names=["test.txt"],chunk_size=300, chunk_overlap=50, )
    # 打印结果
    #print(resp)
    # 2.查看上传到知识库的文档，需要根据知识库名称和文件名称来进行匹配。
    resp1 = list_files('samples')
    print(resp1)
    # 3.查询相关信息的文档
    resp2 = search_docs('新乡工程学院',knowledge_base_name='samples',top_k=6,score_threshold=0.6,file_name="test.txt")
    print(resp2)


if __name__ == "__main__":
    main()