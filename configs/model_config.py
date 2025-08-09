#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/5/13 14:37
@source from: 
"""
LLM_MODELS = ["qwen-api", "zhipu-api", "openai-api"]  # "Qwen-1_8B-Chat",
# LLM通用对话参数
TEMPERATURE = 0.7

EMBEDDING_MODEL = "qwen-api"

# 选用的reranker模型
RERANKER_MODEL = ""
# 是否启用reranker模型
USE_RERANKER = False
RERANKER_MAX_LENGTH = 1024
MODEL_PATH = None