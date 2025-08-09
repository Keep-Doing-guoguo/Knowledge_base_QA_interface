#!/usr/bin/env python
# coding=utf-8

"""
@author: zgw
@date: 2025/5/13 10:22
@source from: 
"""
from functools import wraps
from contextlib import contextmanager
from server.db.base import SessionLocal
from sqlalchemy.orm import Session

@contextmanager
def session_scope() -> Session:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def with_session(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        print(f'函数{func.__name__}被调用')
        print(f"位置参数：{args}")
        print(f"关键字参数：{kwargs}")

        with session_scope() as session:
            try:
                result = func(session,*args,**kwargs)
                session.commit()
                print(f"函数{func.__name__} 返回值：{result}")
                return result

            except Exception as e:
                session.rollback()
                print(f"函数{func.__name__} 出现异常:{e}")
                raise
    return wrapper

#权限校验：
def require_admin(func):
    @wraps(func)
    def wrapper(user_role, *args, **kwargs):
        print(f'函数{func.__name__}被调用')
        print(f"位置参数：{args}")
        print(f"关键字参数：{kwargs}")
        if user_role != "admin":
            print("无权限访问")
            return
        return func(*args, **kwargs)
    return wrapper
#
# @require_admin
# def delete_user(user_id):
#     print(f"用户 {user_id} 已被删除")
#
# # 测试
# delete_user("user")      # 无权限访问
# delete_user("admin", 101) # 用户 101 已被删除




