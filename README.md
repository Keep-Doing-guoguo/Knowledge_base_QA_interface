# 基于 LangChain 的私有化大模型问答系统开发实践【附完整项目结构说明】

针对不同群体的学习价值

学生党

	•	熟悉 LangChain 实战结构
	•	理解私有化部署流程
	•	掌握知识库问答基本流程：embedding、RAG、检索、召回、记忆

上班族开发者

	•	可将本项目作为企业内部 AI 助手基础框架
	•	快速扩展 PDF 工具助手、FAQ 系统
	•	对接公司现有系统，适配业务场景

企业/公司

	•	落地智能客服、文档问答
	•	模块解耦，方便二次开发和模型替换
	•	可对接已有账号系统，实现权限控制
	•	可部署在内网，实现零外部依赖的 AI 服务



## 一、项目背景

在大模型飞速发展的浪潮下，越来越多的企业和组织希望将其能力融入到自己的业务场景中，例如客户支持、内部文档问答、智能助手等。但传统大模型如 ChatGPT 虽然强大，却存在诸多现实痛点：

	•	隐私安全：企业数据不希望发送至第三方服务器，尤其是敏感文档、用户数据等。
	•	联网依赖：依赖外部 API，受限于网络质量、请求频率、费用高昂。
	•	缺乏定制能力：通用大模型无法很好地理解特定业务术语或产品文档。

因此，企业/个人逐步倾向于本地部署大模型，并结合自有知识库构建智能问答系统。本项目正是在这一背景下诞生，具备以下特点：

	•	 基于 LangChain 架构，结构清晰、扩展方便
	•	 支持 Milvus 等主流向量数据库，易于构建大规模文档检索能力
	•	 实现了知识库管理 + 文档入库 + 向量化 + RAG 检索 + 上下文记忆 等一整套问答流程
	•	 所有模块解耦，支持替换 LLM / embedding 模型 / Reranker / 切分策略
	•	 采用 FastAPI 提供统一的接口服务，易于与企业现有系统对接


## 二、项目根目录
```
├── configs/                  # 配置文件模块（模型、服务、提示词等）
│   ├── basic_config.py       # 基础配置（路径、端口、日志级别等）
│   ├── kb_config.py          # 知识库配置（如向量库、embedding 模型）
│   ├── model_config.py       # 模型相关配置（LLM、参数等）
│   ├── prompt_config.py      # Prompt 模板配置
│   └── server_config.py      # 服务器运行配置（FastAPI、CORS等）
├── document_loaders/
│   ├── __init__.py
│   ├── constrast_deault_csv.py    # CSV 文件对比工具（可能用于增量更新）
│   ├── FilteredCSVloader.py       # 带过滤逻辑的 CSV 加载器（按列筛选、去重等）
│   ├── myimgloader.py             # 自定义图片识别文档加载器（结合OCR使用）
│   ├── mypdfloader.py             # 自定义 PDF 加载器（改造原LangChain PDF加载逻辑）
│   ├── ocr.py                     # 图像OCR识别，提取图片中的文字（结合图文文档使用）
│   ├── test.csv                   # 示例数据文件，供测试导入使用
├── server/
│   ├── callback_handler/                          # 回调处理器模块
│   │   ├── conversation_callback_handler.py       # 多轮对话的中间状态处理与回调
│   ├── chat/                                      # 对话主逻辑模块
│   │   ├── chat.py                                # 通用聊天接口（LLMChain）
│   │   ├── file_chat.py                           # 针对文件内容的对话接口
│   │   ├── knowledge_base_chat.py                 # 针对知识库的对话接口
│   │   └── utils.py                               # 辅助函数（格式化输出、响应结构等）
│   ├── db/                                        # 数据模型与数据库接口
│   │   ├── models/                                # ORM 数据模型定义（SQLAlchemy）
│   │   │   ├── base.py
│   │   │   ├── conversation_model.py              # 对话记录模型
│   │   │   ├── knowledge_base_model.py            # 知识库主表模型
│   │   │   ├── knowledge_file_model.py            # 文档表（来源文件等）
│   │   │   ├── knowledge_metadata_model.py        # 文档元信息模型
│   │   │   └── message_model.py                   # 用户消息记录模型
│   │
│   │   │── repository/                            # 数据访问层（Repository模式）
│   │   │   ├── base.py
│   │   │   ├── conversation_repository.py
│   │   │   ├── knowledge_base_repository.py
│   │   │   ├── knowledge_file_repository.py
│   │   │   ├── knowledge_metadata_repository.py
│   │   │   └── message_repository.py
│   ├── base.py                                # DB连接配置与统一封装
│   └── session.py                             # Session管理
│   ├── knowledge_base/
│   │   ├── kb_service/                                # 知识库核心服务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── base.py                                # 基础服务定义
│   │   │   ├── milvus_kb_service.py                   # Milvus 向量库对接逻辑
│   │   model/                                     # API模型层（独立定义结构体）
│   │   │   │kb_document_model.py                   # 存储文档结构定义
│   │   ├── kb_api.py                              # 通用知识库结构体
│   │   ├── kb_doc_api.py                          # 文档上传/提取结构体
│   │   ├── learn_make_text_splitter.py            # 文本切分调试逻辑（开发测试用）
│   │   ├── migrate.py                             # 数据迁移、初始化脚本
│   │   ├── utils.py
│   │   └── utils.md
│   ├── memoey/
│   │   ├── conversation_db_buffer_memory.py
│   ├── reranker/
│   │   ├── reranker.py
│   ├── static/
│   api.py
│   embeddings_api.py
│   utils.py
│api.py
│init_database_v1.py
```


---

## 三、 项目目录结构概览


### 3.1、configs/ 配置模块

统一管理各个子系统和功能的参数与路径。

* `basic_config.py`：项目基本路径、端口、日志等级等
* `kb_config.py`：知识库配置，如 Milvus、embedding 模型路径
* `model_config.py`：语言模型相关配置
* `prompt_config.py`：LLM prompt 模板配置
* `server_config.py`：FastAPI 接口、CORS 设置

---

### 3.2、document\_loaders/ 文档加载器模块

支持不同格式文档加载、清洗、切分，为知识库入库做准备。

* `FilteredCSVloader.py`：带过滤逻辑的 CSV 加载器
* `mypdfloader.py`：自定义 PDF 加载器
* `ocr.py` + `myimgloader.py`：支持 OCR 图文识别
* `contrast_default_csv.py`：对比两版 CSV 差异
* `test.csv`：测试用示例文档

---

###  3.3、server/knowledge\_base/ 知识库模块

整个知识库功能的核心，包括向量入库、文档切分、文档结构定义。

###  3.4、kb\_service/

* `milvus_kb_service.py`：Milvus 入库、查询逻辑
* `base.py`：抽象服务基类

###  3.5、 model/

* `kb_document_model.py`：文档结构体定义

### 其他

* `kb_api.py` / `kb_doc_api.py`：用于接口请求体定义（Pydantic）
* `learn_make_text_splitter.py`：切分调试脚本
* `migrate.py`：数据库初始化 & 数据迁移脚本

---

### 3.6、server/chat/ 对话服务模块

整合 LangChain 或 API 实现不同对话能力。

* `chat.py`：通用问答（无知识库）
* `file_chat.py`：上传文件的对话逻辑
* `knowledge_base_chat.py`：结合 RAG 的智能问答
* `utils.py`：格式化响应、构造输出

---

###  3.7、 server/db/ 数据库与持久化模块

采用 SQLAlchemy 定义表结构，并使用 Repository 模式封装操作。

###  3.8、 models/

* `conversation_model.py`：多轮对话记录
* `knowledge_file_model.py`：文档上传记录
* `message_model.py`：用户发送消息日志

### 3.8、 repository/

* `knowledge_base_repository.py`：知识库主表操作
* `message_repository.py`：聊天记录读写

---

### 3.8、 server/memoey/ 多轮记忆模块

* `conversation_db_buffer_memory.py`：将历史对话缓存在数据库中，实现上下文记忆。

---

### 3.8、 server/reranker/ Rerank 模块

* `reranker.py`：重排序模块，比如使用 BGE-Reranker 对初步检索结果进行排序优化。

---

### 3.8、 FastAPI 启动与接口文件

* `api.py`：主服务启动入口，定义 FastAPI 路由
* `embeddings_api.py`：可对外暴露的 embedding 接口（支持向量生成）
* `init_database_v1.py`：数据库初始化脚本



## 四、实现的具体接口功能-核心功能概述


### 4.1、基础管理

	1.	/knowledge_base/list_knowledge_bases
	•	功能：返回系统中已存在的所有知识库名称及基础信息。
	•	用途：用于前端展示可选知识库列表，或后续调用其它接口时选择目标库。
	2.	/knowledge_base/create_knowledge_base
	•	功能：新建一个知识库，指定名称、描述等元信息。
	•	用途：初始化知识库，为上传文档、向量化和问答交互做准备。
	3.	/knowledge_base/delete_knowledge_base
	•	功能：根据名称或ID删除指定的知识库及其全部文档内容和向量数据。
	•	用途：清理不再使用的知识库。



### 4.2、文档管理

	4.	/knowledge_base/list_files
	•	功能：获取指定知识库中的所有文档文件清单及其元信息。
	•	用途：用于前端展示当前库中的内容，并支持下载或删除。
	5.	/knowledge_base/upload_docs
	•	功能：上传新的文件到指定知识库，并可选执行文本抽取与向量化。
	•	用途：实现从文档到知识的自动注入，支持 PDF、CSV、TXT 等多种类型。
	6.	/knowledge_base/delete_docs
	•	功能：删除某个知识库中的一个或多个指定文档。
	•	用途：移除错误或过期的数据文件。
	7.	/knowledge_base/update_docs
	•	功能：对已有文件内容进行增量更新（如重抽取、替换内容等）。
	•	用途：内容修改后重新生成 embedding，保持库内一致性。
	8.	/knowledge_base/update_docs_by_id
	•	功能：根据文件 ID 精确指定并更新单个文档内容及向量信息。
	•	用途：对上传后的文件执行更细粒度的维护操作。
	9.	/knowledge_base/download_doc
	•	功能：下载原始上传的文档文件。
	•	用途：便于用户查看或再次处理原始资料。



### 4.3、内容维护与搜索
	10.	/knowledge_base/update_info
	•	功能：修改知识库的元信息，如描述、标签、创建者等。
	•	用途：用于信息展示、美化、管理标识。
	11.	/knowledge_base/search_docs
	•	功能：对知识库执行向量化搜索，返回最相关的文档片段集合。
	•	用途：实现 RAG 场景下的检索增强问答（Retrieval-Augmented Generation）。
	12.	/knowledge_base/recreate_vector_store
	•	功能：根据当前知识库文档内容，重新构建向量索引（支持流式响应）。
	•	用途：当更换了 embedding 模型、切分粒度、清洗规则后用于重建索引。

## 五、项目总结

本项目是一个完整的大模型问答系统示例，适合用于企业内部部署、课程教学演示、开发者二次定制。以下是项目的核心价值点总结：

### 5.1、 技术架构完善

	•	LangChain 支撑全流程：涵盖 Prompt 模板构建、RAG 检索、链式调用等核心能力
	•	FastAPI + SQLAlchemy：提供高效后端服务与数据持久化能力
	•	支持多种文档格式：包括 PDF、CSV、图片 OCR 等，覆盖企业常用文档类型
	•	支持多模态扩展：可扩展为图文混合输入的问答系统

### 5.2、  模块化设计

	•	文档加载器（loaders）/ 向量服务（kb_service）/ LLM 调用（chat）/ reranker 排序 等模块完全解耦
	•	易于接入自定义模型，如通义千问、Qwen、ChatGLM、Mistral 等

### 5.3、  实战落地能力强

	•	已实现对话上下文记忆（conversation buffer）与多轮问答能力
	•	提供完整 API 接口文档，配合前端可快速开发业务工具
	•	可作为企业内部 AI 助手框架，快速搭建 FAQ、内部文档搜索、客服自动应答等系统

### 5.4、  可迁移性强

	•	可运行在本地或内网，无需外部依赖
	•	所有模块均可替换，支持私有模型、向量库、reranker
	•	跨平台支持良好，Mac / Linux / Windows 环境均可快速部署