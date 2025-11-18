#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/5/13 11:20
@source from: 
"""
import sys
from datetime import datetime
sys.path.append(".")
from server.knowledge_base.migrate import create_tables,reset_tables

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "-r",
        "--recreate-vs",
        action='store_true',
        help=("""
            recreate vector store.
            use this option if you have copied document files to the content folder, but vector store has not been populated or DEFAUL_VS_TYPE/EMBEDDING_MODEL changed.
        """
              )
    )
    parser.add_argument(
        "--create-tables",
        action="store_true",#当参数出现时，将值设为 True，如果不出现，值为 False。

        help=(
            """help"""
        )
    )

    parser.add_argument(
        "--clear-tables",
        action="store_true",
        help="Clear and reset all database tables."
    )

    args = parser.parse_args()
    start_time = datetime.now()

    print("Parsed arguments:")
    for arg,value in vars(args).items():
        print(f"{arg}:{value}")

    if args.create_tables:
        create_tables()

    if args.clear_tables:
        reset_tables()
        print('database tables reseted!')

#python 数据库相关操作.py --create-tables

#该文件执行上述命令即可创建数据库文件；数据库表结构信息；