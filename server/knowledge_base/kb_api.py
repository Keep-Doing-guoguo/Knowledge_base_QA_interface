import urllib
from server.utils import BaseResponse, ListResponse
from server.knowledge_base.utils import validate_kb_name
from server.knowledge_base.kb_service.base import KBServiceFactory
from configs import EMBEDDING_MODEL, logger, log_verbose
from fastapi import Body
from server.db.repository.knowledge_base_repository import list_kbs_from_db
def list_kbs():
    # Get List of Knowledge Base
    return ListResponse(data=list_kbs_from_db())
def create_kb(knowledge_base_name:str = Body(...,examples=['examples']),
              vector_store_type:str = Body(...,examples=['milvus']),
              embed_model:str = Body(EMBEDDING_MODEL)) -> BaseResponse:
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")
    if knowledge_base_name is None or knowledge_base_name.strip() == "":
        return BaseResponse(code=404, msg="知识库名称不能为空，请重新填写知识库名称")

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)##方法检查指定名称的知识库是否已存在。如果存在，则返回 404 错误代码和一个消息，说明已有同名的知识库。
    if kb is not None:
        return BaseResponse(code=404, msg=f"已存在同名知识库 {knowledge_base_name}")
    kb = KBServiceFactory.get_service(knowledge_base_name, vector_store_type, embed_model)##如果知识库不存在，使用 KBServiceFactory.get_service 创建一个新的知识库服务实例。
    try:
        kb.create_kb()
    except Exception as e:
        msg = f"创建知识库出错：{e}"
        logger.error(f'{e.__class__.__name__}: {msg}')
        return BaseResponse(code=500,msg=msg)

    return BaseResponse(code=200, msg=f"已新增知识库 {knowledge_base_name}")

def delete_kb(knowledge_base_name:str=Body(...,examples=["samples"])):
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")
    knowledge_base_name = urllib.parse.unquote(knowledge_base_name)#解析链接里面的内容

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)#获取到MilvusKBService类
    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")
    try:
        status = kb.clear_vs()#清空向量库
        status = kb.drop_kb()#清空数据库,删除知识库就要删除向量库里面的内容和数据库里面的知识库信息。
        if status:
            return BaseResponse(code=200, msg=f"成功删除知识库 {knowledge_base_name}")
    except Exception as e:
        msg = f"删除知识库时出现意外： {e}"
        logger.error(f'{e.__class__.__name__}: {msg}',)
