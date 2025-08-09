from typing import List
from langchain.document_loaders.unstructured import UnstructuredFileLoader
from document_loaders.ocr import get_ocr


class RapidOCRLoader(UnstructuredFileLoader):
    def _get_elements(self) -> List:
        def img2text(filepath):
            resp = ""
            ocr = get_ocr()
            result, _ = ocr(filepath)
            if result:
                ocr_result = [line[1] for line in result]
                resp += "\n".join(ocr_result)
            return resp

        text = img2text(self.file_path)
        from unstructured.partition.text import partition_text
        return partition_text(text=text, **self.unstructured_kwargs)


if __name__ == "__main__":
    loader = RapidOCRLoader(file_path="/Volumes/PSSD/未命名文件夹/donwload/创建知识库数据库/knowledge_base/samples/content/llm/img/大模型技术栈-算法与原理-幕布图片-81470-404273.jpg")
    docs = loader.load()
    print(docs)
