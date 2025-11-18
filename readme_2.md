项目使用：

1.使用init_database来创建数据库文件。

2.使用server下的embeddings_api来测试模型服务是否可用。使用utils文件来测试大模型是否可用。需要在base文件中配置embedding的api地址和key，在utils文件中配置大模型的api地址和key。

3.执行api文件，来启动服务。

4.提问问题：新乡工程学院：
回答：
data: {"answer": "新乡工程学院（原河南科技学院新科学院）是经教育部批准设立的全日制普通本科高等学校，位于河南省新乡市。学校现有南、北和大学科技园三个校区，规划占地面积2200亩，总建筑面积110万平方米。学校设有12个教学学院，涵盖经济学、管理学、法学、文学、理学、工学、农学、艺术学、教育学等九大学科门类。拥有新一轮河南省重点学科3个，河南省“综合改革试点专业”2个，“河南省一流本科专业建设点”2个，产教融合类专业建设点3个，以及5个“河南省民办普通高等学校专业建设资助项目”。学校还获批省级工程（技术）研究中心和市级科研平台。  \n\n地址：新乡市新飞大道南段777号  \n监督电话：（0373）6330018  \n邮箱：xgrsc@xxgc.edu.cn  \n官网：http://www.xxgc.edu.cn  \n\n交通：距新乡高铁站约14公里，北临新乡汽车客运南站，西临107国道，东临京港澳高速。市内可乘11路公交车至“新乡工程学院”站下车；自驾可导航“新乡工程学院（南校区）”前往。", "docs": ["出处 [1] [test.txt](http://127.0.0.1:7861/knowledge_base/download_doc?knowledge_base_name=samples&file_name=test.txt) \n\n监督电话：（0373）6330018\n\n邮 箱：xgrsc@xxgc.edu.cn\n\n学校官网：http://www.xxgc.edu.cn\n\n到校路线：学校位于新乡市新飞大道南段777号，距新乡市高铁站14公里左右，北临新乡市汽车客运南站，西临107国道，东临京港澳高速。市内可乘坐11路公交车到新乡工程学院下车。自驾者在手机地图搜索“新乡工程学院（南校区）”可直接到达。\n\n", "出处 [2] [test.txt](http://127.0.0.1:7861/knowledge_base/download_doc?knowledge_base_name=samples&file_name=test.txt) \n\n新乡工程学院（原河南科技学院新科学院）是经教育部批准设立的全日制普通本科高等学校。学校地处中原名城新乡市，现有南、北和大学科技园三个校区，规划占地面积2200亩，总建筑面积110万平方米。学校设有教学学院12个，涵盖经济学、管理学、法学、文学、理学、工学、农学、艺术学、教育学等九大学科门类。其中，新一轮河南省重点学科3个，河南省“综合改革试点专业”2个，“河南省一流本科专业建设点”2个，建设产教融合类专业建设点3个，“河南省民办普通高等学校专业建设资助项目”5个，获批省级工程（技术）研究中心和市\n\n"]}


5.执行sql中的脚本，可以查看数据库中的表结构和数据。

需要背的内容：
1.数据库的创建和使用
message-create-time query response
conversation：id
knowledge ：名称、embeddding名称、milvus的选择、创建时间，文件count。
knowledge file：文件名称、文件所在位置、文件load工具、文件splitter、文件source。
filedoc：text、对应的milvusid。

sqlalchemy:需要engine、sessionlocal、需要basedeclaretive。
repository的创建
message：需要updata_message、add_message、get_message_id。
session.query(message).filter(message.id).first()
new_mssage = message():创建这个类。
session.add(new_message)
conversation：add_conversation_id
knowledge_base:add_knowledge_base,get_knowledge_base_name,updata_knowledge_base,load_kb_from_db,get_kb_detial.这些都是数据库层面的内容。
knowledge_file:add_knowledge_file,（需要将文件对应的添加到doc_file表）

fastapi部分和chat部分的是一样的。chat部分和knowledge部分内容。这里是mount_app的方法。然后这块使用create_app。unicorn.run的方法来启动web程序。里面的方法是create_task来实施。
分别创建接口为chat和knowledge_base_chat这个是大致一样的接口内容。

然后是关于知识库上传的部分内容：

上传知识库文件。
通过表单上（表单分为File，Form等）传到服务器，然后保存到本地，保存成功后，然后再进行embedding操作。这里是需要再knowledgefile、filedoc俩个表里面都有相应的操作的。

api 转发到 kb_api和kb_doc_api。kb_api主要包含的是知识库的一些方法，另一个主要是知识库文件的方法。然后再跳转到base和milvuse_service_base里面实现数据和milvus的操作。再追踪到reposity里面。knowledgefile用来解析文件，文件解析后都变成了document，然后将会存放到数据库中和向量库中。
milvusservice中继承base类，base里面主要实现的数据库操作，milvus实现的是向量库的操作。继承langchain的milvus。milvus.col_drop即可。

milvus。query（“expr = f'pk in 「ids」''”，）
appfastapi部分
然后unicrin.run(app)既可以运行起来这个web服务。
ascyio.run(main())这个是本地程序的运行。
ascyio主要是异步io操作。是一个非阻塞的任务。

loader部分有unsfileloader，rapidocrloader。这些都是继承unsfileloader来实现的。
spliiter只使用了charactertextsplitter。主要是按照字符来进行分割的。separator主要是按照换行来进行切分。

异步请求可以使用httpx.AsyncClient()来实现异步请求。

线程池可以使用threadpool来实现，最后使用gather来实现异步io操作。
fastapi的依赖注入，将模块拆分化，简化程序，复用代码。
然后是魔法函数的使用。__init__()初始化，__str__()字符串表示，__add__()算术运算等。
__repr__()：返回对象的正式字符串表示，通常用于调试。
pool.submit()来实现多线程的操作。
as_completed()来实现多线程的异步操作。
splitter有那些呢？

charactertextsplitter：按字符分割
markdowntextsplitter：按markdown语法分割
pythontextsplitter：按python语法分割
recursivecharactertextsplitter：递归按字符分割

loader有哪些呢？
textloader：加载文本文件
pdfloader：加载PDF文件
unsfileloader：加载各种文件


chain有那些呢》比如retriqa、llmchain。conversationchain

agent。zerotypechain。conversaionlagent


项目详细介绍是：

主要实现技术为fastapi、langchain、sqlalchmy、milvus、httpx等技术。

从上到下的进行介绍：
接口部分：

创建知识库
（前端传入字段，知识库名称，先校验是否存在这个知识库，如果存在的话，就直接进行更新这个数据库名称。本知识库的milvus，知识库创建时间。sqlite部分将数据信息写入数据库。）
删除知识库
（前端传入字段，知识库名称，先进行校验这个知识库是否存在。如果已经删除，则返回结果为True。）
上传知识库文件
（前端传入字段，包括文件、知识库名称、文件的chunk_size、文件的overlap、文件是否向量化、文件是否覆盖）
删除知识库文件
（前端传入知识库名称，文件名称、文件内容）
获取知识库文件列表
（前端传入知识库名称、）
查询知识库内容
（前端输入知识库名称、输入query、输入top_k、输入分数阈值、）

总结口主要是由api实现

整体架构是：controller、service、repository、sqlalchmy组成。

关于知识库接口：创建知识库、删除知识库、主要由代码kb_api实现

关于知识库文件接口：上传知识库文件（upload、updata实现）、删除知识库文件、获取知识库文件列表、查询知识库内容。主要由代码kb_doc_api实现。

接口往下分发：
base：主管数据库操作；milvusservice：主管向量库操作；
repository：主管数据库的增删改查操作；





